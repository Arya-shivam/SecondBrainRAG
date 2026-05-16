"""
retriever.py — Hybrid Search over the OpenSearch 'second_brain' index.

Performs two independent searches then fuses the results using
Reciprocal Rank Fusion (RRF) to produce a single ranked list.

Search strategies:
  1. BM25  — Classic full-text keyword matching (great for exact terms,
             proper nouns, technical jargon like 'LoRA' or 'asyncpg').
  2. kNN   — k-Nearest Neighbors on the embedding vector. Finds chunks
             that are semantically similar even if they share no keywords.

Why Hybrid?
  BM25 alone misses synonyms and related concepts.
  Vector alone misses exact terms and can hallucinate relevance.
  Together they cover each other's weaknesses.
"""
from dataclasses import dataclass
from typing import Optional

from src.db.opensearch import get_opensearch_client
from src.rag.embedder import embed_text
from langfuse.decorators import observe


@dataclass
class RetrievedChunk:
    document_id: str
    chunk_index: int
    text: str
    title: str
    creators: list[str]
    source_type: str
    score: float


@observe()
async def retrieve(
    query: str,
    top_k: int = 5,
    source_type: Optional[str] = None,
) -> list[RetrievedChunk]:
    """
    Run hybrid search and return top-K ranked chunks.

    Args:
        query:       The user's natural language question.
        top_k:       Number of results to return.
        source_type: Optional filter e.g. 'youtube' or 'article'.
    """
    # Step 1: Embed the query for vector search
    query_vector = await embed_text(query)

    client = get_opensearch_client()

    # --- BM25 Search ---
    bm25_body = {
        "size": top_k * 2,  # fetch more, RRF will re-rank
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text^2", "title"],  # weight text higher
            }
        },
        "_source": True,
    }

    # --- kNN (Vector) Search ---
    knn_body = {
        "size": top_k * 2,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": top_k * 2,
                }
            }
        },
        "_source": True,
    }

    # Optional source_type filter (added to both queries)
    if source_type:
        filter_clause = {"term": {"source_type": source_type}}
        bm25_body["query"] = {
            "bool": {
                "must": bm25_body["query"],
                "filter": filter_clause,
            }
        }
        knn_body["query"] = {
            "bool": {
                "must": knn_body["query"],
                "filter": filter_clause,
            }
        }

    bm25_resp = client.search(index="second_brain", body=bm25_body)
    knn_resp = client.search(index="second_brain", body=knn_body)

    # --- Reciprocal Rank Fusion (RRF) ---
    # Score = sum of 1/(k + rank) for each list the doc appears in.
    # k=60 is the standard constant that dampens outlier ranks.
    RRF_K = 60
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, hit in enumerate(bm25_resp["hits"]["hits"]):
        doc_id = hit["_id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (RRF_K + rank + 1)
        docs[doc_id] = hit["_source"]

    for rank, hit in enumerate(knn_resp["hits"]["hits"]):
        doc_id = hit["_id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (RRF_K + rank + 1)
        docs[doc_id] = hit["_source"]

    # Sort by RRF score descending, take top_k
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for doc_id, score in ranked:
        src = docs[doc_id]
        results.append(RetrievedChunk(
            document_id=src.get("document_id", ""),
            chunk_index=src.get("chunk_index", 0),
            text=src.get("text", ""),
            title=src.get("title", ""),
            creators=src.get("creators", []),
            source_type=src.get("source_type", ""),
            score=score,
        ))

    return results
