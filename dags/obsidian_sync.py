from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import re
from pathlib import Path
import logging

# We need to import the functions from src. However, Airflow runs in its own container.
# We have mounted /src into /opt/airflow/dags/src, so we can import it.
# Wait, docker-compose.yaml mounts ./dags:/opt/airflow/dags, so src is not there.
# Let's add src to Python path or we need to mount it.
import sys
# Assuming we mount ./src to /opt/airflow/src in docker-compose, we can append it:
sys.path.append("/opt/airflow/src")

# We will handle the import inside the task to avoid DAG parsing errors if src is missing
def sync_obsidian_vault():
    try:
        from src.rag.chunker import chunk_markdown
        from src.rag.embedder import embed_text
        from src.db.opensearch import index_chunk, get_opensearch_client
    except ImportError as e:
        logging.error(f"Failed to import RAG modules. Is /opt/airflow/src mounted? Error: {e}")
        return

    import asyncio
    vault_path = Path("/opt/airflow/data/obsidian")
    if not vault_path.exists():
        logging.warning(f"Vault path does not exist: {vault_path}")
        return

    client = get_opensearch_client()
    indexed_count = 0

    for filepath in vault_path.rglob("*.md"):
        try:
            content = filepath.read_text(encoding="utf-8")
            
            # Check if ingested is false
            if "ingested: false" not in content:
                continue
                
            logging.info(f"Found un-indexed file: {filepath.name}")
            
            # Extract title
            title = filepath.stem
            for line in content.split('\\n'):
                if line.startswith("title:"):
                    title = line.replace("title:", "").strip().strip('"')
                    break
                    
            chunks = chunk_markdown(content)
            logging.info(f"Split {filepath.name} into {len(chunks)} chunks.")
            
            for i, chunk in enumerate(chunks):
                vector = asyncio.run(embed_text(chunk))
                if not vector:
                    continue
                    
                metadata = {
                    "source": filepath.name,
                    "title": title,
                    "chunk_index": i,
                    "filepath": str(filepath.resolve())
                }
                index_chunk(client, document_id=filepath.name, chunk_index=i, text=chunk, title=title, creators=[], source_type="markdown", published_date=None, embedding=vector)
            
            # Mark as ingested: true
            new_content = content.replace("ingested: false", "ingested: true")
            filepath.write_text(new_content, encoding="utf-8")
            logging.info(f"Successfully synced and marked {filepath.name} as ingested.")
            indexed_count += 1
            
        except Exception as e:
            logging.error(f"Error syncing {filepath}: {e}")

    logging.info(f"Sync complete. Indexed {indexed_count} new files.")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'obsidian_vault_sync',
    default_args=default_args,
    description='Syncs unindexed Markdown files from the Obsidian Vault to OpenSearch',
    schedule_interval=timedelta(hours=1), # Run every 1 hour
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['second_brain'],
) as dag:

    sync_task = PythonOperator(
        task_id='sync_obsidian_vault_task',
        python_callable=sync_obsidian_vault,
    )
