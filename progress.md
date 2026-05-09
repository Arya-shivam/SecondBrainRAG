# Project Progress & Next Steps

## Completed So Far

### Infrastructure & Core Services
- [x] Docker Compose environment successfully set up and running locally.
- [x] Services healthy: Postgres, OpenSearch, Airflow, Langfuse, and FastAPI app.
- [x] Dependencies cleanly managed via `uv`.

### Storage Layer (Second Brain Schema)
- [x] **Database Initialization:** `scripts/init-postgres.sql` sets up the `documents`, `creators`, `document_creators`, and `chunks` tables.
- [x] **PostgreSQL Connection:** Created `src/db/postgres.py` using `asyncpg` for fast asynchronous DB operations.
- [x] **OpenSearch Connection:** Created `src/db/opensearch.py` with the `second_brain` index mapping (BM25 + 768d `knn_vector`).
- [x] **Verification:** Verified end-to-end insertion of mock documents and embeddings via `seed_mock_data.py`.

### Ingestion Pipeline
- [x] **YouTube Transcript Fetcher:** Created `yt_fetcher.py` using `youtube-transcript-api` and `yt-dlp` to download and parse transcripts into Obsidian Markdown format.
- [x] **Universal Data Ingestion:** Created `universal_ingest.py` using `pymupdf` (PDFs), `trafilatura` (Web Articles), and `python-docx` (Word Docs). Automatically parses files or URLs.

### Zero-Friction Capture Tools
- [x] **API Exposure:** Added `/api/ingest` to the FastAPI backend to receive data from external tools.
- [x] **Chrome Extension:** Built a "one-click" browser extension with local network observability (desktop notifications) to instantly save web articles and YouTube videos to the ingestion pipeline.

### Product Definition
- [x] Established project architecture (Airflow -> VectorDB -> LlamaIndex -> FastAPI).
- [x] Defined the Bot Identity: **Dhi**, representing the living intelligence and deep equivalent of Grok trained on your consumed content.

## Next Steps

### Telegram Bot (Dhi)
- [ ] Create the `telegram_bot.py` script so you can send links and thoughts to your bot from your phone.

### Retrieval & Generation (Phase 3)
- [x] Implement the RAG retrieval pipeline (Hybrid search: BM25 + vectors in OpenSearch with RRF).
- [x] Create the LLM generator using OpenRouter (`meta-llama/llama-3.1-8b-instruct:free` for now) and strict grounding prompts.
- [x] Create the `/ask` endpoint to orchestrate retrieval and generation.
- [ ] Establish the two-way sync where Airflow picks up the `ingested: false` notes, chunks them, and adds them to OpenSearch.
