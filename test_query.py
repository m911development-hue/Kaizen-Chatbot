import asyncio
from backend.app.services.rag_service import rag_service

async def main():
    rag_service.initialize()
    query = "Who presented Kaizen No. 01 and what is the theme of this Kaizen?"
    print(f"Query: {query}\n")
    
    docs = await rag_service.retrieve(query)
    print("--- RETRIEVED DOCUMENTS ---")
    for i, doc in enumerate(docs, 1):
        print(f"Doc {i} - Page {doc.metadata.get('page')}:")
        print(doc.page_content)
        print("-" * 50)
        
    res = await rag_service.generate_response(query)
    print("\n--- AI RESPONSE ---")
    print(res["response"])

if __name__ == "__main__":
    asyncio.run(main())
