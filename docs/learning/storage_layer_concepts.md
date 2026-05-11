# Storage Layer Concepts: Building the Second Brain

This document explains the core concepts and file structures we introduced while building the persistence (storage) layer for your Second Brain. The goal of this layer is to hold both the raw text chunks and their mathematical representations (embeddings) so that our RAG (Retrieval-Augmented Generation) pipeline can query them later.

## 1. Dual-Database Architecture
A robust RAG system typically separates relational metadata from vector search capabilities to get the best of both worlds. We use:

*   **PostgreSQL**: Handles relational metadata (e.g., matching a document to its author, storing URLs, publication dates). It provides ACID guarantees ensuring our data is reliably written.
*   **OpenSearch**: A specialized search engine that handles **Hybrid Search**. It stores the exact same text chunks alongside a 768-dimensional `knn_vector` (the embedding). OpenSearch allows us to run BM25 (keyword matching) and k-Nearest Neighbors (semantic meaning) in a single query.

## 2. File Explanations

### `scripts/init-postgres.sql`
**What it does:** This is the initialization script for PostgreSQL. When the Postgres Docker container starts with an empty data volume, it runs this script automatically.
**Key Concepts:**
- `documents`: The parent table holding high-level information about an article or video.
- `creators`: A normalized table for authors/channels. Normalization prevents data duplication.
- `document_creators`: A junction (many-to-many) table. One document can have multiple authors, and one author can write multiple documents.
- `chunks`: Stores the granular pieces of text broken down from the main document.

### `src/db/postgres.py`
**What it does:** Contains the asynchronous Python functions to interact with PostgreSQL.
**Key Concepts:**
- `asyncpg`: We use `asyncpg` instead of traditional `psycopg2` because FastAPI is asynchronous. This prevents database queries from blocking the main event loop, allowing your API to handle multiple ingestion requests simultaneously.
- `ON CONFLICT DO UPDATE`: This is an "Upsert" (Update or Insert) operation. If you try to ingest the same URL twice, the database gracefully updates the existing record instead of throwing a duplicate key error.

### `src/db/opensearch.py`
**What it does:** Establishes the connection to OpenSearch and defines the index schema.
**Key Concepts:**
- **Index Mapping**: Similar to a SQL schema, but for search engines.
- `knn_vector` type: We define a field of 768 dimensions (the standard output size of models like `nomic-embed-text`).
- `hnsw` algorithm: Hierarchical Navigable Small World. This is the underlying algorithm OpenSearch uses to quickly find nearest neighbors in high-dimensional space without comparing against every single document (which would be extremely slow).
- `analyzer: "english"`: This tells OpenSearch to apply English stemming and stop-word removal (e.g., treating "running" and "run" as the same word) for better keyword searches.

### `scripts/seed_mock_data.py`
**What it does:** A test script to verify that our Python code successfully communicates with both databases inside the Docker network.
**Key Concepts:**
- **End-to-End Verification**: By inserting fake data into both systems, we guarantee that the tables exist, the OpenSearch index is properly formatted, and the network ports are correctly mapped between containers.
- **Relational Integrity**: Notice how the script inserts the OpenSearch ID (`os_id`) into the Postgres `chunks` table. This creates a bridge between the two databases, so if we find a chunk in OpenSearch, we can perfectly trace it back to its exact Postgres record.
