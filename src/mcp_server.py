"""
mcp_server.py — Second Brain MCP Server

Exposes your personal knowledge base as MCP tools that any compatible
LLM client can call (Claude Desktop, Claude CLI, Codex, Cursor, etc.)

Transport modes:
  - stdio  (default): for terminal agents — `uv run python -m src.mcp_server`
  - http   (--http):  for Claude.ai web  — `uv run python -m src.mcp_server --http`

Tools exposed:
  • search_memory(query, top_k?)  — Hybrid vector+BM25 search across your vault
  • save_note(title, content, folder?) — Create a new Markdown note in your vault
  • list_sources()                — List all indexed document titles
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# ── App setup ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="second-brain",
    instructions=(
        "This MCP server gives you access to the user's personal Second Brain knowledge base. "
        "Use `search_memory` whenever the user asks something that might be in their notes or research. "
        "Use `save_note` to persist new information they want to remember. "
        "Always cite the source titles returned by search_memory."
    ),
)


# ── Tool: search_memory ───────────────────────────────────────────────────────
@mcp.tool()
async def search_memory(query: str, top_k: int = 5) -> str:
    """
    Semantically search the user's Second Brain knowledge base.

    Args:
        query: Natural language question or keywords to search for.
        top_k: Number of results to return (default: 5, max: 20).

    Returns:
        Formatted string of the most relevant knowledge chunks with source titles.
    """
    from src.rag.retriever import retrieve

    top_k = min(top_k, 20)
    chunks = await retrieve(query, top_k=top_k)

    if not chunks:
        return "No relevant information found in the Second Brain for this query."

    lines = [f"Found {len(chunks)} relevant chunks from your Second Brain:\n"]
    for i, chunk in enumerate(chunks, 1):
        creators = ", ".join(chunk.creators) if chunk.creators else "Unknown"
        lines.append(
            f"[{i}] **{chunk.title}** ({chunk.source_type})\n"
            f"    Author: {creators} | Score: {chunk.score:.4f}\n"
            f"    {chunk.text[:500]}{'...' if len(chunk.text) > 500 else ''}\n"
        )

    return "\n".join(lines)


# ── Tool: save_note ───────────────────────────────────────────────────────────
@mcp.tool()
async def save_note(title: str, content: str, folder: str = "notes") -> str:
    """
    Save a new Markdown note to the user's Obsidian vault and index it in OpenSearch.

    Args:
        title:   Title for the note.
        content: The main body content of the note (Markdown supported).
        folder:  Subfolder inside the vault (default: 'notes'). 
                 Use descriptive names like 'work', 'research', 'ideas'.

    Returns:
        Confirmation message with the path where the note was saved.
    """
    from src.ingest.universal_ingest import _write_vault

    date = datetime.now().strftime("%Y-%m-%d")
    filepath = _write_vault(
        folder=folder,
        title=title,
        text=content,
        date=date,
        tags=["mcp-saved"],
        meta={},
    )

    return f"✓ Note saved to: {filepath}\nIt has been indexed and is now searchable in your Second Brain."


# ── Tool: list_sources ────────────────────────────────────────────────────────
@mcp.tool()
async def list_sources(limit: int = 50) -> str:
    """
    List all documents indexed in the Second Brain.

    Args:
        limit: Maximum number of documents to return (default: 50).

    Returns:
        A list of all indexed document titles and their types.
    """
    from src.db.opensearch import get_opensearch_client

    client = get_opensearch_client()

    body = {
        "size": 0,
        "aggs": {
            "unique_docs": {
                "terms": {
                    "field": "document_id",
                    "size": limit,
                }
            }
        },
    }

    resp = client.search(index="second_brain", body=body)
    buckets = resp.get("aggregations", {}).get("unique_docs", {}).get("buckets", [])

    if not buckets:
        return "No documents are indexed in the Second Brain yet."

    lines = [f"📚 {len(buckets)} documents indexed in your Second Brain:\n"]
    for i, bucket in enumerate(buckets, 1):
        doc_id = bucket["key"]
        chunk_count = bucket["doc_count"]
        lines.append(f"  {i}. {doc_id}  ({chunk_count} chunks)")

    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Second Brain MCP Server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP/SSE server (for Claude.ai web). Default: stdio for CLI agents.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP mode (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for HTTP mode (default: 8001)",
    )
    args = parser.parse_args()

    if args.http:
        print(f"🧠 Second Brain MCP Server running on http://{args.host}:{args.port}/sse", file=sys.stderr)
        print("   Connect Claude.ai → Settings → Integrations → Add MCP Server", file=sys.stderr)
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        # stdio mode — Claude CLI, Codex, Cursor all use this
        mcp.run(transport="stdio")
