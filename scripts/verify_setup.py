import httpx
import asyncio

async def verify():
    print("Checking infrastructure...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/health")
            if resp.status_code == 200:
                data = resp.json()
                print("✅ FastAPI is up")
                if data["services"]["opensearch"] == "ok":
                    print("✅ OpenSearch is reachable")
                else:
                    print(f"❌ OpenSearch issue: {data['services']['opensearch']}")
            else:
                print("❌ FastAPI returned non-200 status")
    except Exception as e:
        print(f"❌ Failed to reach FastAPI: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
