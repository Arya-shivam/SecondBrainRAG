# arXiv Research Paper Curator — Product Requirements Document

**Version:** 1.0  
**Status:** In Progress  
**Author:** Personal Project  
**Last Updated:** May 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Goals & Success Metrics](#goals--success-metrics)
4. [System Architecture](#system-architecture)
5. [Phase 1 — Foundation & Infrastructure](#phase-1--foundation--infrastructure)
6. [Phase 2 — Ingestion Pipeline](#phase-2--ingestion-pipeline)
7. [Phase 3 — Retrieval & Generation](#phase-3--retrieval--generation)
8. [Phase 4 — Interface & Observability](#phase-4--interface--observability)
9. [Phase 5 — Brain Map (v2)](#phase-5--brain-map-v2)
10. [Infrastructure Decisions & Tradeoffs](#infrastructure-decisions--tradeoffs)
11. [Data Models](#data-models)
12. [API Specification](#api-specification)
13. [Non-Functional Requirements](#non-functional-requirements)
14. [Out of Scope](#out-of-scope)

---

## Overview

A personal RAG (Retrieval-Augmented Generation) system that ingests, indexes, and lets you query academic papers from arXiv. Ask questions in natural language, get answers grounded in real papers with source citations.

Version 2 adds an **Obsidian-style interactive graph** — a visual brain map of papers linked by citations, topic similarity, and your own annotations.

**Primary user:** Yourself.  
**Scale:** Personal use, ~1000–10,000 papers, single machine deployment.

---

## Bot Identity (Dhi)

**Dhi — Your Personal Deep Intelligence**

**Meaning:**
Dhi (धी) is an ancient Sanskrit word from the Vedas that represents higher intellect, visionary wisdom, and the power of insightful thought. It is the illuminating faculty of the mind that cuts through confusion, connects ideas, and reveals truth. In the famous Gayatri Mantra, Dhi is the very quality we pray to awaken.

Just like a deep equivalent of Grok, Dhi is built to consume everything you feed it — your notes, thoughts, readings, and experiences — and transform them into clear, sharp, and profound understanding.

It is not just memory.
It is living intelligence.

---

## Problem Statement

Academic papers are hard to use in practice:

- You save hundreds of PDFs you never read again
- Search is keyword-only — you can't ask "what approaches exist for reducing hallucinations in LLMs?"
- No memory across papers — you can't see how ideas connect across 50 papers at once
- Reading a paper cold gives no context of what it builds on or what built on it

This system solves all four problems.

---

## Goals & Success Metrics

### Core goals

| Goal | Metric | Target |
|------|--------|--------|
| Answer quality | RAGAS faithfulness score | > 0.8 |
| Retrieval accuracy | nDCG@10 | > 0.75 |
| Response latency | p95 end-to-end | < 5 seconds |
| Ingestion reliability | Daily sync success rate | > 99% |
| Source accuracy | Answers cite correct papers | > 90% |

### Personal success criteria (qualitative)

- You stop opening individual PDFs and just ask the system instead
- You find connections between papers you didn't know existed
- The graph view surfaces "neighbourhoods" of related work clearly

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                          │
│  arXiv API → Airflow DAG → PDF Parsing → Chunking          │
│              (daily sync)   (GROBID/Docling) (semantic)    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    STORAGE LAYER                            │
│  PostgreSQL (metadata, authors, citations, graph edges)     │
│  OpenSearch  (chunks + embeddings, BM25 + vector index)    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 RETRIEVAL PIPELINE                          │
│  LlamaIndex → Hybrid Search → Reranking → Context Builder  │
│               (BM25 + vectors)  (Cohere/local)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 GENERATION LAYER                            │
│  Ollama (Llama 3.2 local) → Prompt Template → Answer       │
│  FastAPI /ask endpoint (async)                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 INTERFACE LAYER                             │
│  Gradio (Q&A UI) + D3.js Graph (v2 brain map)              │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│               OBSERVABILITY LAYER                           │
│  Langfuse (traces, prompt versions, user feedback)         │
│  RAGAS (retrieval + answer quality metrics)                │
└─────────────────────────────────────────────────────────────┘
```

### Tech stack summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Orchestration | Apache Airflow 2.8 | Retry logic, backfill, DAG visibility |
| Metadata store | PostgreSQL 16 | ACID, relational joins, JSONB |
| Vector + text search | OpenSearch 2.11 | Native BM25 + kNN in one query |
| Embeddings | `nomic-embed-text` via Ollama | Local, free, good quality |
| LLM inference | Ollama + Llama 3.2 8B | Private, zero cost per query |
| Retrieval framework | LlamaIndex | Purpose-built for RAG pipelines |
| API | FastAPI (async) | Performance, pydantic validation |
| UI | Gradio | Fast to build, good enough for personal use |
| Graph UI (v2) | D3.js force-directed | Obsidian-style, fully custom |
| Observability | Langfuse | Prompt versioning, traces, RAGAS |
| PDF parsing | GROBID + Docling (fallback) | Structured extraction, citation parsing |
| Package manager | uv | Faster than pip, lockfile support |
| Linting | ruff | Fast, opinionated |

---

## Phase 1 — Foundation & Infrastructure

**Timeline:** Week 1  
**Goal:** All services running locally, talking to each other. No ML yet.

### Deliverables

- [ ] `docker-compose.yml` with all 6 services
- [ ] FastAPI app boots, `/health` returns status of each service
- [ ] `.env` config wired through pydantic-settings
- [ ] PostgreSQL schema created (papers, authors, chunks tables)
- [ ] OpenSearch index created with correct mappings
- [ ] Mock seed script — 5 fake papers inserted and retrievable
- [ ] pre-commit + ruff configured
- [ ] `README.md` with local setup instructions

### Services in Docker Compose

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 5432 | Metadata store |
| OpenSearch 2.11 | 9200 | Search + vector index |
| Ollama | 11434 | LLM + embedding inference |
| Airflow | 8080 | Pipeline orchestration |
| Langfuse | 3000 | Observability |
| FastAPI app | 8000 | Main API |

### Project structure

```
arxiv-curator/
├── docker-compose.yml
├── .env
├── .env.example
├── .pre-commit-config.yaml
├── pyproject.toml
├── Dockerfile
├── src/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── health.py
│   │   └── ask.py
│   ├── models/
│   │   └── paper.py
│   └── db/
│       ├── postgres.py
│       └── opensearch.py
├── dags/
│   └── arxiv_sync.py
└── scripts/
    ├── seed_mock_data.py
    └── verify_setup.py
```

### Definition of done

All 6 containers show `healthy` in `docker compose ps`. Hitting `GET /health` returns `200 OK` with status of every downstream service. Mock seed script inserts and retrieves 5 papers without errors.

---

## Phase 2 — Ingestion Pipeline

**Timeline:** Weeks 2–3  
**Goal:** Real papers flowing from arXiv into Postgres + OpenSearch daily.

### Deliverables

- [ ] Airflow DAG — daily sync from arXiv API
- [ ] Metadata fetch (title, abstract, authors, categories, date, DOI)
- [ ] PDF download with rate limiting and retry
- [ ] GROBID PDF parser for structured text + citation extraction
- [ ] Docling fallback OCR for scans / failed GROBID parses
- [ ] Chunking strategy implemented (semantic + max-token size)
- [ ] Embedding generation via `nomic-embed-text`
- [ ] Chunks + embeddings written to OpenSearch
- [ ] Citation links written to `paper_citations` table in Postgres
- [ ] Backfill script for historical papers (e.g. last 90 days)
- [ ] Dead-letter queue for failed ingestions
- [ ] Ingestion metrics tracked in Langfuse

### Airflow DAG flow

```
fetch_new_arxiv_ids
        │
        ▼
download_pdfs (parallel, 4 workers, rate-limited)
        │
        ├──── parse_pdf_grobid
        │              │ (on failure)
        │              └── parse_pdf_docling_fallback
        │
        ▼
chunk_and_embed
        │
        ├──── write_to_postgres (metadata + citations)
        └──── write_to_opensearch (chunks + embeddings)
```

### Chunking strategy

| Strategy | When used | Chunk size |
|----------|-----------|------------|
| Semantic (sentence boundary) | Body text | ~300 tokens |
| Fixed-size with overlap | Fallback | 512 tokens, 50 overlap |
| Section-aware | Papers with GROBID sections | Per section |

### Paper categories to track (configurable)

Default: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `stat.ML`

---

## Phase 3 — Retrieval & Generation

**Timeline:** Weeks 4–5  
**Goal:** Ask a question, get a grounded answer with sources.

### Deliverables

- [ ] LlamaIndex hybrid retrieval (BM25 + vector, fused with RRF)
- [ ] Reranking step (local cross-encoder or Cohere rerank API)
- [ ] Context builder — top-K chunks assembled with source metadata
- [ ] Prompt template with grounding instructions
- [ ] Ollama Llama 3.2 answer generation
- [ ] `POST /ask` endpoint returning answer + sources + latency
- [ ] Langfuse trace per request (query → chunks → prompt → answer)
- [ ] RAGAS evaluation suite on 20 test questions

### Retrieval pipeline detail

```
User query
    │
    ├── BM25 search (keyword match — good for terms like "LoRA", "RLHF")
    └── Vector search (semantic similarity via embeddings)
            │
            ▼
    Reciprocal Rank Fusion (merge BM25 + vector results)
            │
            ▼
    Reranker (cross-encoder scores top-20, returns top-5)
            │
            ▼
    Context builder (assemble chunks + paper titles + authors)
            │
            ▼
    LLM (answer grounded in context, cite paper IDs inline)
```

### Prompt template structure

```
You are a research assistant. Answer the question using ONLY
the provided context. Cite papers by their ID in [brackets].
If the context doesn't contain the answer, say so.

Context:
{top_k_chunks_with_metadata}

Question: {user_question}

Answer:
```

### API contract — `/ask`

```
POST /ask
{
  "question": "What methods reduce hallucination in LLMs?",
  "top_k": 5,
  "filters": {
    "after_date": "2024-01-01",
    "categories": ["cs.AI", "cs.CL"]
  }
}

→ 200 OK
{
  "answer": "Several approaches have been proposed...",
  "sources": [
    {
      "paper_id": "2401.12345",
      "title": "...",
      "authors": ["..."],
      "chunk_text": "...",
      "score": 0.91
    }
  ],
  "latency_ms": 1840,
  "trace_id": "langfuse-trace-xyz"
}
```

---

## Phase 4 — Interface & Observability

**Timeline:** Week 6  
**Goal:** Usable UI, measurable quality, prompt iteration loop.

### Deliverables

- [ ] Gradio UI — question input, answer display, source cards with abstract preview
- [ ] Langfuse dashboard — latency, RAGAS scores, prompt versions
- [ ] Thumbs up/down feedback captured per answer
- [ ] Prompt versioning — A/B test two prompt templates
- [ ] RAGAS metrics automated: faithfulness, answer relevance, context precision
- [ ] nDCG@10 retrieval metric computed weekly on eval set

### Gradio UI layout

```
┌──────────────────────────────────────────┐
│  arXiv Curator                           │
├──────────────────────────────────────────┤
│  Ask a question about your papers...     │
│  [text input                          ]  │
│  [Search]  Filters: date range, category │
├──────────────────────────────────────────┤
│  Answer                                  │
│  ─────────────────────────────────────   │
│  Several papers address this. [2401.xxx] │
│  proposes...                             │
├──────────────────────────────────────────┤
│  Sources                                 │
│  ┌──────────────────────────────────┐    │
│  │ 2401.xxx · Attention Is All You  │    │
│  │ Need · Vaswani et al. 2017       │    │
│  │ "...relevant chunk text here..." │    │
│  │ Score: 0.91   [👍] [👎] [Open]   │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

### Observability metrics to track

| Metric | Tool | Frequency |
|--------|------|-----------|
| Request latency p50/p95 | Langfuse | Per request |
| RAGAS faithfulness | RAGAS | Weekly batch |
| RAGAS answer relevance | RAGAS | Weekly batch |
| nDCG@10 retrieval | Custom script | Weekly |
| User thumbs up rate | Langfuse | Ongoing |
| Prompt version comparison | Langfuse | Per experiment |

---

## Phase 5 — Brain Map (v2)

**Timeline:** Future (after Phase 4 is stable)  
**Goal:** Obsidian-style interactive graph of your paper collection.

### Concept

Every paper is a node. Edges are drawn from:
- **Citations** — paper A references paper B (extracted by GROBID)
- **Semantic similarity** — embedding cosine similarity > 0.85 between papers
- **Manual tags** — you group papers into clusters yourself

The graph is force-directed (D3.js), zoomable, and clickable. Clicking a node shows the paper card. Clicking an edge shows why two papers are connected.

### Data to store from day 1 (plant the seed in Phase 1)

These tables should be created in Phase 1 even though they won't be used until v2:

```sql
-- Citation graph edges
CREATE TABLE paper_citations (
    source_paper_id VARCHAR(20) REFERENCES papers(arxiv_id),
    cited_paper_id  VARCHAR(20),
    confidence      FLOAT DEFAULT 1.0,
    extracted_by    VARCHAR(20) DEFAULT 'grobid',
    PRIMARY KEY (source_paper_id, cited_paper_id)
);

-- Semantic similarity edges (computed offline)
CREATE TABLE paper_similarity (
    paper_a_id  VARCHAR(20) REFERENCES papers(arxiv_id),
    paper_b_id  VARCHAR(20) REFERENCES papers(arxiv_id),
    score       FLOAT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (paper_a_id, paper_b_id)
);

-- User clusters / annotations
CREATE TABLE paper_clusters (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100),
    color      VARCHAR(7),  -- hex color for graph node
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_cluster_members (
    paper_id    VARCHAR(20) REFERENCES papers(arxiv_id),
    cluster_id  INTEGER REFERENCES paper_clusters(id),
    PRIMARY KEY (paper_id, cluster_id)
);
```

### v2 Deliverables

- [ ] `GET /graph` endpoint returning nodes + edges as JSON
- [ ] D3.js force-directed graph frontend
- [ ] Node color = category / cluster
- [ ] Edge weight = citation count or similarity score
- [ ] Click node → paper card with abstract + ask button
- [ ] Zoom, pan, filter by date/category
- [ ] "Neighbourhood" view — show all papers within 2 hops of selected

---

## Infrastructure Decisions & Tradeoffs

### PostgreSQL vs MongoDB

**Chose Postgres.** This project has relational data — papers have authors, authors have papers, papers cite papers. Aggregation pipelines in Mongo can handle it, but Postgres gives ACID transactions (important when ingesting paper + chunks + citations atomically), better tooling support across Airflow/LlamaIndex/Langfuse, and JSONB for flexible metadata alongside proper foreign keys. Mongo wins at massive scale with truly dynamic schemas — not this project.

### OpenSearch vs alternatives

| Option | BM25 | Vectors | Cost | Verdict |
|--------|------|---------|------|---------|
| OpenSearch | Native | Native kNN | Free, self-hosted | ✅ Chosen |
| Pinecone | No | Yes | Paid managed | ❌ No BM25 |
| Weaviate | Plugin | Native | Self-hosted | Fine, more complex |
| pgvector | No | Yes | Free | ❌ BM25 weak |
| Elasticsearch | Native | Native | License cost | Close second |

Hybrid search (BM25 + vectors in one query) is critical for academic text — exact term matching for paper IDs, author names, and technical terms (LoRA, RLHF, etc.) that vectors handle poorly.

### Ollama (local) vs OpenAI API

| Factor | Ollama | OpenAI |
|--------|--------|--------|
| Cost | $0/query | ~$0.002/query |
| Privacy | Papers stay local | Data sent to OpenAI |
| Quality | Llama 3.2 8B — good | GPT-4o — better |
| Latency | Depends on GPU/CPU | Fast, consistent |
| Offline | Yes | No |

**Chose Ollama.** Personal project, privacy matters, cost at 1000+ queries/day adds up. The architecture supports swapping in OpenAI with one config change if needed.

### Airflow vs cron job

Cron jobs fail silently. Airflow gives retries, backfill (catch up missed days), task-level failure handling, rate limiting between tasks, and a UI to debug failures. For a pipeline that downloads hundreds of PDFs with rate limits and two fallback parsers, cron is not enough.

### LlamaIndex vs LangChain

LlamaIndex is purpose-built for indexing and retrieval. Cleaner abstractions for chunking strategies, index management, and query engines. LangChain is broader but more boilerplate for pure RAG. LlamaIndex is the right tool here.

---

## Data Models

### PostgreSQL schema

```sql
CREATE TABLE papers (
    arxiv_id        VARCHAR(20) PRIMARY KEY,
    title           TEXT NOT NULL,
    abstract        TEXT,
    published_date  DATE,
    updated_date    DATE,
    categories      TEXT[],
    pdf_url         TEXT,
    doi             TEXT,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

CREATE TABLE authors (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    UNIQUE(name)
);

CREATE TABLE paper_authors (
    paper_id    VARCHAR(20) REFERENCES papers(arxiv_id),
    author_id   INTEGER REFERENCES authors(id),
    position    INTEGER,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE chunks (
    id              SERIAL PRIMARY KEY,
    paper_id        VARCHAR(20) REFERENCES papers(arxiv_id),
    chunk_index     INTEGER,
    text            TEXT NOT NULL,
    token_count     INTEGER,
    section         VARCHAR(100),
    opensearch_id   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### OpenSearch index mapping

```json
{
  "mappings": {
    "properties": {
      "chunk_id":     { "type": "integer" },
      "paper_id":     { "type": "keyword" },
      "title":        { "type": "text", "analyzer": "english" },
      "authors":      { "type": "text" },
      "text":         { "type": "text", "analyzer": "english" },
      "section":      { "type": "keyword" },
      "published":    { "type": "date" },
      "categories":   { "type": "keyword" },
      "embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw",
          "engine": "nmslib",
          "parameters": { "ef_construction": 128, "m": 16 }
        }
      }
    }
  },
  "settings": {
    "index": { "knn": true },
    "number_of_shards": 1,
    "number_of_replicas": 0
  }
}
```

---

## API Specification

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health — Postgres, OpenSearch, Ollama |
| `POST` | `/ask` | Ask a question, returns answer + sources |
| `GET` | `/papers` | List ingested papers with filters |
| `GET` | `/papers/{arxiv_id}` | Get single paper + chunks |
| `GET` | `/stats` | Ingestion stats — paper count, chunk count, last sync |
| `GET` | `/graph` | Graph data (nodes + edges) for v2 brain map |
| `POST` | `/feedback` | Submit thumbs up/down on an answer |

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| `/ask` p95 latency | < 5 seconds |
| `/ask` p50 latency | < 2 seconds |
| Ingestion pipeline success rate | > 99% |
| System uptime | Best effort (personal use) |
| Max papers at launch | 10,000 |
| Max concurrent users | 1 (personal) |
| Data retention | Indefinite |
| Security | Local only, no auth needed for v1 |

---

## Out of Scope

- Multi-user support
- Authentication / API keys for v1
- Mobile app
- Real-time paper alerts / push notifications
- Integration with reference managers (Zotero, Mendeley) — future consideration
- Fine-tuning / training pipeline (SageMaker) — noted in diagram as future enhancement
- Cloud deployment — local Docker only for v1

---

*Built with: Airflow · PostgreSQL · OpenSearch · Ollama · LlamaIndex · FastAPI · Gradio · Langfuse*