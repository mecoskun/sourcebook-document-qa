import asyncio

from app.mcp_client import MCPBridge


async def test_tool_arguments_can_include_name():
    bridge = MCPBridge()
    task = asyncio.create_task(bridge.call("index_document", name="handbook.txt"))
    tool, arguments, future = await bridge.queue.get()
    assert tool == "index_document"
    assert arguments == {"name": "handbook.txt"}
    future.set_result({"id": "document"})
    assert await task == {"id": "document"}
