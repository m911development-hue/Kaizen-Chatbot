"""
Quick test: Check RAG health and force rebuild if needed.
Run: .venv/Scripts/python.exe test_rag.py --rebuild
"""
import asyncio
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.rag_service import rag_service
from backend.app.config import settings

def main():
    print("=" * 60)
    print("KAIZEN AI -- RAG Health Check and Rebuild")
    print("=" * 60)
    
    from pathlib import Path
    pdf_path = Path(settings.COMPANY_PDF_PATH)
    print(f"\n[1] PDF Path: {pdf_path}")
    print(f"    Exists: {pdf_path.exists()}")
    if pdf_path.exists():
        print(f"    Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    print(f"\n[2] Initializing RAG service...")
    try:
        rag_service.initialize()
        print("    OK - RAG service initialized successfully")
    except Exception as e:
        print(f"    FAIL - Init failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    stats = rag_service.get_stats()
    print(f"\n[3] Knowledge Base Stats:")
    print(f"    Total documents: {stats['total_documents']}")
    print(f"    Total chunks: {stats['total_chunks']}")
    print(f"    Has documents: {stats['has_documents']}")
    
    if stats['total_chunks'] == 0 or '--rebuild' in sys.argv:
        print(f"\n[4] Force rebuilding index...")
        import hashlib
        pdf_bytes = pdf_path.read_bytes()
        current_hash = hashlib.sha256(pdf_bytes).hexdigest()
        try:
            rag_service.rebuild_company_index(pdf_path, current_hash)
            print("    OK - Rebuild complete!")
            stats = rag_service.get_stats()
            print(f"    New chunk count: {stats['total_chunks']}")
        except Exception as e:
            print(f"    FAIL - Rebuild failed: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print(f"\n[5] Testing query: 'Who presented Kaizen No. 01?'")
    try:
        docs = asyncio.run(rag_service.retrieve("Who presented Kaizen No. 01 and what is the theme?", k=8))
        print(f"    Retrieved {len(docs)} chunks:")
        for i, doc in enumerate(docs, 1):
            page = doc.metadata.get('page', '?')
            preview = doc.page_content[:150].replace('\n', ' ')
            print(f"    [{i}] Page {page}: {preview}...")
    except Exception as e:
        print(f"    FAIL - Query failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n[6] Testing full response generation...")
    try:
        result = asyncio.run(rag_service.generate_response("Who presented Kaizen No. 01 and what is the theme?"))
        print(f"    Response: {result['response'][:500]}")
        print(f"    Sources: {result['sources']}")
    except Exception as e:
        print(f"    FAIL - Response generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Done!")

if __name__ == "__main__":
    main()
