"""
Setup script to initialize Pinecone vector database with FAQ data.
Run this script once to populate the vector database with fintech FAQ data.
"""

import asyncio
import os
from dotenv import load_dotenv
from rag_service import RAGService

async def main():
    """Initialize vector database with FAQ data."""
    print("🚀 Starting Pinecone Vector Database Setup")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check environment variables
    pinecone_key = os.getenv("PINECONE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    print(f"📋 Environment Check:")
    print(f"   Pinecone API Key: {'✅ Set' if pinecone_key else '❌ Missing'}")
    print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print()

    if not pinecone_key:
        print("⚠️  Warning: PINECONE_API_KEY not found.")
        print("   Set it in your .env file: PINECONE_API_KEY=your_key_here")
        print("   Get your key from: https://app.pinecone.io/")
        print()

    if not openai_key:
        print("⚠️  Warning: OPENAI_API_KEY not found.")
        print("   Set it in your .env file: OPENAI_API_KEY=your_key_here")
        print("   Get your key from: https://platform.openai.com/api-keys")
        print()

    # Initialize RAG service
    print("🔧 Initializing RAG Service...")
    rag_service = RAGService()

    # Setup index
    print("🗂️  Setting up Pinecone index...")
    index_setup = await rag_service.setup_index()
    if not index_setup:
        print("❌ Failed to setup Pinecone index. Check your API key and network connection.")
        return

    print("✅ Pinecone index setup successful!")

    # Index FAQ data
    faq_file_path = "fintech_faq_data.json"
    if not os.path.exists(faq_file_path):
        print(f"❌ FAQ data file not found: {faq_file_path}")
        return

    print(f"📚 Indexing FAQ data from {faq_file_path}...")
    indexing_success = await rag_service.index_faq_data(faq_file_path)

    if indexing_success:
        print("✅ FAQ data indexed successfully!")

        # Get index statistics
        stats = await rag_service.get_index_stats()
        print(f"📊 Index Statistics:")
        print(f"   Total vectors: {stats.get('total_vectors', 'N/A')}")
        print(f"   Index fullness: {stats.get('index_fullness', 'N/A')}")
        print(f"   Dimension: {stats.get('dimension', 'N/A')}")

        # Test search functionality
        print("\n🔍 Testing search functionality...")
        test_query = "How do I create an account?"
        results = await rag_service.search_similar_faqs(test_query, top_k=2)

        if results:
            print(f"✅ Search test successful! Found {len(results)} results for: '{test_query}'")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['question'][:60]}... (Score: {result['similarity_score']:.3f})")
        else:
            print("❌ Search test failed")

        # Test RAG response generation
        print("\n🤖 Testing RAG response generation...")
        rag_response = await rag_service.generate_rag_response(test_query)

        if rag_response and not rag_response.get('error'):
            print("✅ RAG response generation successful!")
            print(f"   Response length: {len(rag_response['response'])} characters")
            print(f"   Context used: {len(rag_response['context_used'])} FAQs")
            print(f"   Fallback mode: {rag_response.get('fallback', False)}")
        else:
            print("❌ RAG response generation failed")

    else:
        print("❌ Failed to index FAQ data")

    print("\n" + "=" * 50)
    print("🎉 Vector Database Setup Complete!")
    print("\n💡 Next Steps:")
    print("   1. Start your FastAPI server: uvicorn main:app --reload")
    print("   2. Test the chat functionality in your frontend")
    print("   3. Monitor the logs for any issues")

if __name__ == "__main__":
    asyncio.run(main())