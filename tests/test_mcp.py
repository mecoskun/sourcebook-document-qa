import asyncio

from app.mcp_client import MCPBridge


async def test_real_mcp_subprocess_lifecycle_and_empty_workspace():
    bridge = MCPBridge()
    worker = asyncio.create_task(bridge.run())
    await asyncio.wait_for(bridge.ready.wait(), 20)
    try:
        assert bridge.error is None
        assert await bridge.call("list_documents", session_id="empty-test") == []
        assert await bridge.call("search_documents", session_id="empty-test", question="Anything?") == []
        assert await bridge.call("delete_document", session_id="empty-test") == {"deleted": True}
    finally:
        await bridge.queue.put(None)
        await worker
