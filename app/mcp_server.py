"""Internal stdio MCP server. Never expose session identifiers or this server publicly."""
from mcp.server.fastmcp import FastMCP

from app.retrieval import DocumentIndex

mcp = FastMCP("Sourcebook documents")
index = DocumentIndex()


@mcp.tool()
def index_document(session_id: str, name: str, sections: list[dict]) -> dict:
    """Index extracted document passages for one private workspace."""
    return index.add(session_id, name, sections)


@mcp.tool()
def list_documents(session_id: str) -> list[dict]:
    """List source documents belonging to one workspace."""
    return index.list(session_id)


@mcp.tool()
def delete_document(session_id: str, document_id: str | None = None) -> dict:
    """Delete one document, or all documents in this workspace when no ID is provided."""
    index.remove(session_id, document_id)
    return {"deleted": True}


@mcp.tool()
def search_documents(session_id: str, question: str) -> list[dict]:
    """Find relevant passages with source locations from this workspace only."""
    return index.search(session_id, question)


if __name__ == "__main__":
    mcp.run(transport="stdio")
