from opensearchpy import OpenSearch
from src.config import settings

def get_opensearch_client():
    return OpenSearch(
        hosts=[settings.opensearch_url],
        use_ssl=False,
        verify_certs=False,
    )

def init_opensearch(client: OpenSearch):
    index_name = "second_brain"
    
    mapping = {
        "mappings": {
            "properties": {
                "document_id":  { "type": "keyword" },
                "chunk_index":  { "type": "integer" },
                "text":         { "type": "text", "analyzer": "english" },
                "title":        { "type": "text", "analyzer": "english" },
                "creators":     { "type": "text" },
                "source_type":  { "type": "keyword" },
                "published":    { "type": "date" },
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
            "index": { "knn": True },
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
    
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=mapping)
        print(f"Created OpenSearch index '{index_name}'")

def index_chunk(client: OpenSearch, document_id: str, chunk_index: int, text: str, title: str, creators: list[str], source_type: str, published_date, embedding: list[float]):
    doc = {
        "document_id": document_id,
        "chunk_index": chunk_index,
        "text": text,
        "title": title,
        "creators": creators,
        "source_type": source_type,
        "published": published_date.isoformat() if published_date else None,
        "embedding": embedding
    }
    
    response = client.index(
        index="second_brain",
        body=doc,
        refresh=True
    )
    return response["_id"]
