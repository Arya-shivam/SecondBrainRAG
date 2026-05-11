# Second Brain MCP Server — Setup Guide

This server exposes your personal knowledge base as **MCP tools** that any compatible
LLM client can use to search or save your memory.

---

## Tools Available

| Tool | Description |
|------|-------------|
| `search_memory(query, top_k?)` | Semantic + keyword search across your entire vault |
| `save_note(title, content, folder?)` | Create a new note and instantly index it |
| `list_sources(limit?)` | List all indexed documents |

---

## Option A: Claude CLI / Codex CLI / Cursor (stdio)

These terminal agents launch the MCP server as a subprocess automatically.

### Step 1 — Make sure Docker is running (OpenSearch)
```bash
docker compose up -d opensearch
```

### Step 2 — Add to your agent config

**For Claude CLI** (`~/.claude.json` or `claude mcp add`):
```bash
claude mcp add second-brain --command "uv" --args "run python -m src.mcp_server" --cwd "C:\Users\aryas\OneDrive\Desktop\prodRAG"
```

**For Cursor / Windsurf** — add to `.cursor/mcp.json` in your project:
```json
{
  "mcpServers": {
    "second-brain": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_server"],
      "cwd": "C:\\Users\\aryas\\OneDrive\\Desktop\\prodRAG"
    }
  }
}
```

**Manual stdio test:**
```bat
run_mcp.bat
```

---

## Option B: Claude.ai Website (HTTP/SSE)

Claude.ai connects to remote MCP servers over HTTP. Since your server runs locally,
you need to expose port 8001 to the internet (e.g. with ngrok).

### Step 1 — Start the HTTP server
```bat
run_mcp.bat --http
```
This starts the server at `http://localhost:8001/sse`

### Step 2 — Expose it with ngrok (free)
```bash
ngrok http 8001
```
Copy the `https://xxxx.ngrok.io` URL.

### Step 3 — Add to Claude.ai
1. Go to **claude.ai → Settings → Integrations**
2. Click **Add MCP Server**
3. Paste: `https://xxxx.ngrok.io/sse`
4. Done! Claude will now have `search_memory`, `save_note`, and `list_sources` tools.

---

## Environment Variables Required

The server reads from your `.env` file automatically. Make sure these are set:

```env
OPENROUTER_API_KEY=sk-or-...      # For embedding the search query
OPENSEARCH_HOST=localhost          # Default: localhost
OPENSEARCH_PORT=9200               # Default: 9200
```
