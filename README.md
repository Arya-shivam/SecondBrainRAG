# Dhi: A Personal RAG Second Brain

> Inspired by Andrej Karpathy's concept of an "LLM OS" and the idea of a deeply integrated personal knowledge wiki. 

If you are an individual diving deep into AI, constantly consuming research papers, YouTube tech talks, and long-form articles, you know the struggle: hoarding tabs and saving links to the void. **Dhi** is designed to fix that. 

It is a frictionless, localized Second Brain. Instead of manually organizing notes, you just send links and files to Dhi via a Telegram bot or a Chrome extension. Dhi parses the content, embeds the knowledge, and saves it permanently into your local Obsidian vault. From there, you can chat with your entire knowledge base using an advanced Hybrid RAG pipeline.

## 🏗️ Architecture

Dhi runs on a containerized, local-first stack, orchestrated by Docker Compose and `uv`.

1. **Ingestion Layer (Frictionless Capture):**
   - **Interfaces:** A Telegram Bot (for mobile) and a Chrome Extension (for desktop).
   - **Processing:** A FastAPI backend uses `BackgroundTasks` to parse YouTube transcripts (`youtube-transcript-api`), PDFs (`pymupdf`), and web articles (`trafilatura`) without blocking the UI.
   - **Storage:** Parsed text is saved directly to your local file system as Markdown inside an Obsidian vault.
2. **Indexing & Retrieval Layer (Hybrid Search):**
   - **Vector Database:** Local OpenSearch instance.
   - **Embeddings:** Text chunks are embedded via OpenRouter using lightweight models (e.g., `llama-nemotron-embed`).
   - **Hybrid Search:** Combines **BM25** (for exact keyword/jargon matching) and **kNN** (for semantic similarity).
   - **Re-ranking:** Fuses both search scores using Reciprocal Rank Fusion (RRF) to ensure the highest quality context.
3. **Generation & Telemetry Layer:**
   - **LLM:** Context is fed to an LLM via OpenRouter for grounded answers with exact source citations.
   - **Observability:** Fully integrated with a local **Langfuse** container. Every ingestion, retrieval, and generation step is traced to monitor latency, track context quality, and debug prompts visually.

## 🧗‍♂️ Problems Faced & Mitigations

Building a reliable AI-agent backend is rarely straightforward. Here are the major hurdles crossed during development:

### 1. The "Silent Failure" Ingestion Trap
**Problem:** Ingestion tasks (especially large PDFs or hour-long YouTube videos) would occasionally hang or fail silently. Furthermore, Windows console encoding (`cp1252`) crashed the background tasks when attempting to log emojis or complex Unicode characters from scraped text.
**Mitigation:** 
- Decoupled the ingestion pipeline using FastAPI `BackgroundTasks`. 
- Implemented a direct HTTP callback mechanism that pings the user's Telegram chat with a success (or failure) message once the file is safely written to the Obsidian vault.
- Forced `PYTHONUNBUFFERED=1` and reconfigured `sys.stdout` to `utf-8` to guarantee stable, real-time logging.

### 2. Retrieval Blindspots with Pure Vector Search
**Problem:** Semantic search is great for concepts, but terrible at retrieving specific technical jargon (e.g., searching for "LoRA", "asyncpg", or precise API keys).
**Mitigation:** Migrated the entire RAG pipeline from pure vector search to **Hybrid Search** using OpenSearch. By running parallel queries for traditional BM25 keyword matching alongside the kNN vector search, and mathematically fusing them with Reciprocal Rank Fusion (RRF), Dhi now successfully retrieves both conceptual themes and exact technical keywords.

### 3. Observability and SDK Mismatches
**Problem:** Debugging LLM prompts locally without a dashboard is a nightmare. We decided to integrate Langfuse via Docker, but the modern Langfuse Python SDK (v4.x) strictly required newer metadata fields that the older self-hosted Langfuse image (v2.x) didn't provide, causing Pydantic validation crashes.
**Mitigation:** Identified the schema conflict by reviewing stack traces and explicitly downgraded and pinned the `uv` dependency to `langfuse>=2.54.0,<3.0.0`. This instantly restored full tracing capabilities without having to migrate the entire Docker database schema.

## 🚀 Final Product

Dhi is a production-ready, locally hosted API that transforms scattered internet artifacts into a queryable, localized intelligence. 

It is entirely open-source friendly, relying on Postgres, OpenSearch, Langfuse, and standard Markdown. Whether you are building an AI startup, doing academic research, or just trying to organize your digital life, Dhi ensures that nothing you read is ever truly forgotten.
