"""
Utility to view refined data in Vector Database
Shows processed embeddings and metadata
"""

import json
import chromadb
from .config import config

def view_vector_data():
    """View all data in vector database"""
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=config.vector_store_path)
        collection = client.get_collection("regulatory_policies")
        
        # Get all data
        results = collection.get(include=["documents", "metadatas", "embeddings"])
        
        print("=" * 60)
        print("VECTOR DATABASE CONTENTS")
        print("=" * 60)
        print(f"Total Documents: {len(results['documents'])}")
        print()
        
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"DOCUMENT {i+1}:")
            print(f"  Policy ID: {metadata.get('policy_id', 'N/A')}")
            print(f"  Authority: {metadata.get('authority', 'N/A')}")
            print(f"  Version: {metadata.get('version', 'N/A')}")
            print(f"  Section: {metadata.get('section_title', 'N/A')}")
            print(f"  Change Type: {metadata.get('change_type', 'N/A')}")
            print(f"  Processing Date: {metadata.get('processing_date', 'N/A')}")
            print(f"  Content Length: {len(doc)} chars")
            print(f"  Content Preview: {doc[:100]}...")
            print("-" * 40)
        
        # Show statistics
        print("\nSTATISTICS:")
        print(f"  Total embeddings stored: {len(results['embeddings'])}")
        print(f"  Embedding dimension: {len(results['embeddings'][0]) if results['embeddings'] else 'N/A'}")
        
        # Authority breakdown
        authorities = {}
        for metadata in results['metadatas']:
            auth = metadata.get('authority', 'Unknown')
            authorities[auth] = authorities.get(auth, 0) + 1
        
        print("\nAUTHORITY BREAKDOWN:")
        for auth, count in authorities.items():
            print(f"  {auth}: {count} documents")
            
    except Exception as e:
        print(f"Error viewing vector data: {e}")

def search_similar_content(query_text: str, limit: int = 3):
    """Search for similar content in vector database"""
    try:
        from .gemini_utils import get_gemini_api
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=config.vector_store_path)
        collection = client.get_collection("regulatory_policies")
        
        # Generate query embedding
        gemini_api = get_gemini_api()
        query_embedding = gemini_api.generate_embedding(query_text)
        
        if not query_embedding:
            print("Failed to generate query embedding")
            return
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\nSEARCH RESULTS FOR: '{query_text}'")
        print("=" * 50)
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            similarity = 1 - distance  # Convert distance to similarity
            print(f"\nRESULT {i+1} (Similarity: {similarity:.3f}):")
            print(f"  Policy: {metadata.get('policy_id', 'N/A')}")
            print(f"  Section: {metadata.get('section_title', 'N/A')}")
            print(f"  Change Type: {metadata.get('change_type', 'N/A')}")
            print(f"  Content: {doc[:200]}...")
        
    except Exception as e:
        print(f"Error searching: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Search mode
        query = " ".join(sys.argv[1:])
        search_similar_content(query)
    else:
        # View all mode
        view_vector_data()
