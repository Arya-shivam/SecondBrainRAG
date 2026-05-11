import asyncio
import random
from datetime import date

from src.db.postgres import get_db_pool, insert_document, get_or_create_creator, link_document_creator, insert_chunk
from src.db.opensearch import get_opensearch_client, init_opensearch, index_chunk

async def seed():
    print("Connecting to DB...")
    pool = await get_db_pool()
    
    print("Connecting to OpenSearch...")
    os_client = get_opensearch_client()
    init_opensearch(os_client)
    
    print("Seeding mock data...")
    
    doc_id = "test-doc-1"
    title = "Understanding the Second Brain"
    url = "https://example.com/second-brain"
    source_type = "article"
    published = date(2026, 5, 1)
    
    # 1. Insert into Postgres
    await insert_document(
        pool=pool,
        doc_id=doc_id,
        title=title,
        url=url,
        source_type=source_type,
        published_date=published,
        metadata={"tags": ["productivity", "knowledge"]}
    )
    
    creator_id = await get_or_create_creator(pool, "Tiago Forte")
    await link_document_creator(pool, doc_id, creator_id)
    
    # 2. Insert Chunk into OpenSearch and Postgres
    chunk_text = "A second brain is an external, centralized, digital repository for the things you learn."
    embedding = [random.uniform(-1, 1) for _ in range(768)]
    
    os_id = index_chunk(
        client=os_client,
        document_id=doc_id,
        chunk_index=0,
        text=chunk_text,
        title=title,
        creators=["Tiago Forte"],
        source_type=source_type,
        published_date=published,
        embedding=embedding
    )
    
    chunk_db_id = await insert_chunk(
        pool=pool,
        document_id=doc_id,
        chunk_index=0,
        text=chunk_text,
        token_count=16,
        opensearch_id=os_id
    )
    
    print(f"✅ Success! Seeded Document {doc_id}")
    print(f"Chunk DB ID: {chunk_db_id}, OpenSearch ID: {os_id}")
    
    await pool.close()

if __name__ == "__main__":
    asyncio.run(seed())
