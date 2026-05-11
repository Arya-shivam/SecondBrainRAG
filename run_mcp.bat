@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  Second Brain MCP Server — Windows Launcher
REM ─────────────────────────────────────────────────────────────────────────────
REM
REM  USAGE:
REM    run_mcp.bat          → stdio mode  (Claude CLI, Codex, Cursor)
REM    run_mcp.bat --http   → HTTP mode   (Claude.ai website, port 8001)
REM
REM  REQUIREMENTS:
REM    • Docker must be running (OpenSearch container)
REM    • Run from the project root: cd prodRAG && run_mcp.bat
REM ─────────────────────────────────────────────────────────────────────────────

setlocal
set SCRIPT_DIR=%~dp0

REM Load .env if it exists
if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%SCRIPT_DIR%.env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
    )
)

if "%1"=="--http" (
    echo.
    echo  Second Brain MCP Server — HTTP/SSE Mode
    echo  Listening on http://0.0.0.0:8001/sse
    echo  Add this URL to Claude.ai ^> Settings ^> Integrations
    echo.
    uv run python -m src.mcp_server --http
) else (
    uv run python -m src.mcp_server
)
