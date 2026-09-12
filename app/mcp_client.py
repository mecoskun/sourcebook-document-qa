import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import ROOT


class MCPBridge:
    """A single owner task enters/exits MCP contexts; HTTP tasks submit bounded work."""

    def __init__(self):
        self.queue = asyncio.Queue(maxsize=8)
        self.ready = asyncio.Event()
        self.error = None

    async def run(self):
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "app.mcp_server"], cwd=str(ROOT))
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.ready.set()
                    while True:
                        item = await self.queue.get()
                        if item is None:
                            break
                        name, arguments, future = item
                        if future.cancelled():
                            continue
                        try:
                            result = await asyncio.wait_for(session.call_tool(name, arguments), 180)
                            if result.isError:
                                raise RuntimeError("The document tool could not complete the operation.")
                            # Structured MCP results wrap list return values in 'result'.
                            value = result.structuredContent
                            if value is not None:
                                if set(value) == {"result"}:
                                    value = value["result"]
                            else:
                                texts = [block.text for block in result.content if block.type == "text"]
                                if not texts:
                                    raise RuntimeError("The document tool returned no content.")
                                value = json.loads("".join(texts))
                            if not future.done():
                                future.set_result(value)
                        except Exception as exc:
                            if not future.done():
                                future.set_exception(exc)
        except Exception as exc:
            self.error = exc
            self.ready.set()
        finally:
            self.error = self.error or RuntimeError("Document tools have stopped.")
            while not self.queue.empty():
                item = self.queue.get_nowait()
                if item and not item[2].done():
                    item[2].set_exception(self.error)

    async def call(self, tool_name: str, **arguments):
        if self.error:
            raise RuntimeError("Document tools are unavailable.") from self.error
        future = asyncio.get_running_loop().create_future()
        try:
            self.queue.put_nowait((tool_name, arguments, future))
        except asyncio.QueueFull as exc:
            raise RuntimeError("The demo is busy. Please try again shortly.") from exc
        return await asyncio.wait_for(future, 190)
