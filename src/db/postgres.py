import asyncpg
import json
from src.config import settings

async def get_db_pool():
    return await asyncpg.create_pool(settings.postgres_url)

async def insert_document(pool, doc_id: str, title: str, url: str, source_type: str, published_date=None, metadata=None):
    if metadata is None:
        metadata = {}
    
    query = """
    INSERT INTO documents (id, title, url, source_type, published_date, metadata)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (id) DO UPDATE 
    SET title = EXCLUDED.title,
        url = EXCLUDED.url,
        metadata = EXCLUDED.metadata;
    """
    async with pool.acquire() as conn:
        await conn.execute(query, doc_id, title, url, source_type, published_date, json.dumps(metadata))

async def get_or_create_creator(pool, name: str) -> int:
    query_select = "SELECT id FROM creators WHERE name = $1"
    query_insert = "INSERT INTO creators (name) VALUES ($1) RETURNING id"
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query_select, name)
        if row:
            return row['id']
        row = await conn.fetchrow(query_insert, name)
        return row['id']

async def link_document_creator(pool, document_id: str, creator_id: int):
    query = """
    INSERT INTO document_creators (document_id, creator_id)
    VALUES ($1, $2)
    ON CONFLICT DO NOTHING;
    """
    async with pool.acquire() as conn:
        await conn.execute(query, document_id, creator_id)

async def insert_chunk(pool, document_id: str, chunk_index: int, text: str, token_count: int, opensearch_id: str):
    query = """
    INSERT INTO chunks (document_id, chunk_index, text, token_count, opensearch_id)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id;
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, document_id, chunk_index, text, token_count, opensearch_id)
        return row['id']
