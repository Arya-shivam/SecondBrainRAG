import asyncio
from src.rag.generator import generate_answer
from src.rag.retriever import RetrievedChunk
from langfuse import Langfuse
import sys
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Testing Langfuse Integration...", flush=True)
    
    # 1. Check if Langfuse keys are configured
    langfuse = Langfuse()
    if not langfuse.auth_check():
        print("[FAIL] Langfuse keys not found or invalid!")
        sys.exit(1)
        
    print("[SUCCESS] Langfuse keys loaded.")

    # 2. Mock a chunk to test generation
    mock_chunks = [
        RetrievedChunk(
            document_id="doc1",
            chunk_index=0,
            text="Second Brain is a system for organizing your knowledge using Obsidian, FastAPI, and OpenSearch.",
            title="Second Brain Overview",
            creators=["Arya"],
            source_type="article",
            score=1.0
        )
    ]

    print("\nSending question to generator...")
    try:
        # This will trigger the @observe(as_type="generation") decorator
        answer = await generate_answer(
            question="What is Second Brain?",
            chunks=mock_chunks
        )
        print("\n[SUCCESS] Response generated:")
        print(answer)
        
        # Flush Langfuse telemetry so it doesn't wait in the background queue
        langfuse.flush()
        print("\n[SUCCESS] Langfuse telemetry flushed successfully. Check your dashboard at http://localhost:3001!")
        
    except Exception as e:
        print(f"\n[FAIL] Error during generation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
