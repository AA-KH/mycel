import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from groq import AsyncGroq

async def main():
    try:
        client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY_1", ""))
        models = await client.models.list()
        print("Available Models:")
        for m in models.data:
            print(f"- {m.id}")
    except Exception as e:
        print(f"Error fetching models: {e}")

if __name__ == "__main__":
    asyncio.run(main())
