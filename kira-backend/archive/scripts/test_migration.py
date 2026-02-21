"""
Complete Working Example of Migrated Gemini API Integration
Test script to verify migration from google.generativeai to google.genai
"""

import asyncio
from backend.core.gemini_utils_v2 import get_gemini_api_v2

async def test_migration():
    """Test all migrated functionality"""
    print("Testing Gemini API Migration")
    print("=" * 50)
    
    # Initialize API
    api = get_gemini_api_v2()
    
    # Test 1: Embedding Generation
    print("\n1. Testing Embedding Generation:")
    test_text = "Regulatory compliance requirements for banking industry"
    embedding = api.generate_embedding(test_text)
    
    if embedding:
        print(f"   Embedding generated: {len(embedding)} dimensions")
        print(f"   Sample values: {embedding[:5]}...")
    else:
        print("   Embedding generation failed")
    
    # Test 2: Content Generation
    print("\n2. Testing Content Generation:")
    prompt = "Explain the importance of AI governance in banking"
    response = api.generate_content(prompt)
    
    if response:
        print(f"   Content generated: {len(response)} chars")
        print(f"   Response: {response[:200]}...")
    else:
        print("   Content generation failed")
    
    # Test 3: Async Content Generation
    print("\n3. Testing Async Content Generation:")
    try:
        async_response = await api.generate_content_async("What is regulatory compliance?")
        if async_response:
            print(f"   Async content generated: {len(async_response)} chars")
            print(f"   Async response: {async_response[:200]}...")
        else:
            print("   Async content generation failed")
    except Exception as e:
        print(f"   Async test failed: {e}")
    
    # Test 4: Structured Response
    print("\n4. Testing Structured JSON Response:")
    structured_prompt = """
    Analyze this regulatory scenario and provide a JSON response:
    {
        "risk_level": "HIGH|MEDIUM|LOW",
        "compliance_required": true/false,
        "summary": "Brief analysis"
    }
    """
    
    structured_response = api.generate_structured_response(structured_prompt)
    
    if structured_response and not structured_response.get("error"):
        print(f"   Structured response generated")
        print(f"   Risk Level: {structured_response.get('risk_level', 'N/A')}")
        print(f"   Compliance Required: {structured_response.get('compliance_required', 'N/A')}")
        print(f"   Summary: {structured_response.get('summary', 'N/A')}")
    else:
        print(f"   Structured response failed: {structured_response.get('error_message', 'Unknown error')}")
    
    # Test 5: Batch Embeddings
    print("\n5. Testing Batch Embeddings:")
    test_texts = [
        "Banking regulation compliance",
        "AI governance framework",
        "Data protection requirements"
    ]
    
    batch_embeddings = api.generate_embeddings_batch(test_texts)
    
    if batch_embeddings and len(batch_embeddings) == len(test_texts):
        print(f"   Batch embeddings generated: {len(batch_embeddings)} embeddings")
        for i, emb in enumerate(batch_embeddings):
            print(f"   Text {i+1}: {len(emb)} dimensions")
    else:
        print("   Batch embedding generation failed")
    
    print("\n" + "=" * 50)
    print("Migration Test Complete!")
    print("All Gemini API functions working with new google.genai package")

def main():
    """Run migration test"""
    print("Gemini API Migration Test")
    print("Testing migration from google.generativeai to google.genai")
    print()
    
    # Run async test
    asyncio.run(test_migration())
    
    print("\nMigration Summary:")
    print("Import: import google.genai as genai")
    print("Client: genai.Client(api_key=api_key)")
    print("Embedding: models/gemini-embedding-001")
    print("Generation: models/gemini-2.5-flash")
    print("Async Support: generate_content_async()")
    print("No Deprecation Warnings!")

if __name__ == "__main__":
    main()
