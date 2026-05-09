# RAG: Retrieval & Generation Concepts

This document is a deep dive into the core AI concepts powering the "brain" of your Second Brain — specifically, how it **finds** relevant information and **answers** questions using that information.

---

## 1. What is RAG (Retrieval-Augmented Generation)?

A standard LLM (like GPT-4 or Claude) is trained on data up to a certain cutoff date. It knows nothing about your personal notes, YouTube transcripts, or saved articles. More dangerously, when it doesn't know something, it will **hallucinate** — make up a confident-sounding but completely wrong answer.

**RAG solves this by augmenting the LLM's prompt with retrieved facts from your own database at query time.**

```
User Question
     │
     ▼
[Retriever] → searches your Second Brain → returns top-5 relevant chunks
     │
     ▼
[Context Builder] → formats chunks into readable passages
     │
     ▼
[LLM Prompt] → "Answer using ONLY these passages: ..."
     │
     ▼
Grounded Answer (with citations from your actual notes)
```

The LLM is not asked to recall facts from training — it's essentially reading the relevant parts of your Second Brain right before answering.

---

## 2. Embeddings: Turning Text into Numbers

To do **semantic search** (finding conceptually related chunks, not just keyword matches), we need a way to represent text as numbers that a computer can compare.

An **embedding model** (we use `nomic-embed-text`) takes any piece of text and produces a fixed-length list of numbers called a **vector**. For example:

```
"How does attention work in transformers?" → [0.023, -0.441, 0.812, ...]  (768 numbers)
"The attention mechanism allows tokens to..."  → [0.027, -0.445, 0.801, ...]  (768 numbers)
```

These two vectors are **very close together** in 768-dimensional space because the texts are semantically similar, even though they share few keywords.

**Cosine Similarity** is the standard metric used to measure how "close" two vectors are. It measures the angle between them (ignoring magnitude), returning a value from -1 (opposite meaning) to 1 (identical meaning).

**In practice:** At query time, `embedder.py` embeds the user's question, then OpenSearch finds chunks whose embedding vectors are nearest to it — that's the `knn_vector` field in our index.

---

## 3. BM25: The Best Keyword Search Algorithm

**BM25** (Best Match 25) is the industry-standard full-text search algorithm, used by Elasticsearch, OpenSearch, and even Google for initial retrieval. It's an evolution of TF-IDF.

### How it works:
1. **Term Frequency (TF)**: A chunk that contains the query word 5 times is more relevant than one that contains it once. But BM25 applies **saturation** — the 50th occurrence barely helps more than the 5th.
2. **Inverse Document Frequency (IDF)**: Common words like "the" or "is" appear in almost every document, so they carry almost no signal. Rare words like "asyncpg" or "HNSW" are highly discriminative and get a much higher weight.
3. **Document Length Normalization**: A short chunk that mentions a term is probably more relevant than a 10,000-word document that mentions it once.

**Why BM25 beats vector-only search for some queries:**
If you ask *"What does the asyncpg library do?"*, vector search might return chunks about async Python in general (semantically related). BM25 will directly find chunks that contain the exact word "asyncpg" — which is exactly what you want.

---

## 4. Hybrid Search + RRF: The Best of Both Worlds

We run **both** BM25 and kNN simultaneously, getting two separate ranked lists of chunks. Then we need to merge them.

**Reciprocal Rank Fusion (RRF)** is a simple, parameter-free algorithm for combining ranked lists:

```
For each document in any list:
    RRF_score += 1 / (60 + rank)
```

The constant `60` is empirically chosen — it dampens the influence of very high-ranked items to avoid outliers dominating. A document that appears at rank 1 in both BM25 and vector search will have a very high combined score. One that appears at rank 1 in only one list will score lower than if both methods agreed.

**Why 60?** It's the result of years of research by Cormack, Clarke, and Buettcher (2009). It's now universally used in production hybrid search systems including Elasticsearch and Cohere.

---

## 5. OpenRouter: A Unified LLM Gateway

**OpenRouter** is an API gateway that gives you access to dozens of LLMs (GPT-4o, Claude, Llama, Mistral, Gemini) through a single, standardized API endpoint. This is immensely valuable because:

1. **Model Flexibility**: You can switch from Llama-3.1 to GPT-4o by changing a single config line — no code changes.
2. **Cost Optimization**: Start with free models, switch to better ones for hard questions.
3. **OpenAI-Compatible API**: The request/response format is identical to OpenAI's API, so the learning transfers.

### The API Call Structure (from `generator.py`)
```python
response = await client.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question_with_context},
        ],
        "temperature": 0.3,
    }
)
```

- **`model`**: The model identifier on OpenRouter. Models ending in `:free` are free.
- **`messages`**: A list of chat turns. The `system` role sets the persona and rules. The `user` role is the actual question.
- **`temperature`**: Controls randomness. `0.0` = fully deterministic/factual. `1.0` = highly creative/random. We use `0.3` for RAG because we want factual answers, not creative storytelling.

---

## 6. File Reference

| File | Role |
|---|---|
| `src/rag/embedder.py` | Converts query text → 768-dim vector via OpenRouter |
| `src/rag/retriever.py` | Runs BM25 + kNN on OpenSearch, fuses with RRF |
| `src/rag/generator.py` | Builds RAG prompt + calls OpenRouter LLM |
| `src/routers/ask.py` | FastAPI endpoint that orchestrates retrieve → generate |
| `src/config.py` | Central config for `openrouter_api_key`, `openrouter_model`, `embed_model` |

---

## 7. The Full Request Lifecycle

```
POST /ask  {"question": "What did I learn about attention mechanisms?"}
  │
  ├─ embedder.py → embed("What did I learn about attention...") → [0.023, ...]
  │
  ├─ retriever.py
  │     ├─ BM25 search → [chunk_A rank1, chunk_B rank2, chunk_C rank3 ...]
  │     ├─ kNN search  → [chunk_B rank1, chunk_A rank2, chunk_D rank3 ...]
  │     └─ RRF fusion  → [chunk_A score=0.032, chunk_B score=0.031, ...]
  │
  ├─ generator.py
  │     ├─ Format context: "[1] Title: ... Content: ..."
  │     ├─ Build prompt with system rules + context + question
  │     └─ POST to OpenRouter → "Based on [Attention Is All You Need], ..."
  │
  └─ Return: {answer: "...", sources: [...], latency_ms: 1240}
```
