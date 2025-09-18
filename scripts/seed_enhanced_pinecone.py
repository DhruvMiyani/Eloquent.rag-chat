#!/usr/bin/env python3
"""
Enhanced Pinecone seeding script that supports multiple fintech datasets.
This script can seed from the original FAQ data or the enhanced dataset.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time
import argparse

# Add parent directory to path to import from api
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import openai

# Load environment variables
load_dotenv(Path(__file__).parent.parent / "api" / ".env")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-powered-chatbot-challenge")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Initialize clients
openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)

def load_enhanced_faq_data() -> List[Dict[str, Any]]:
    """Load enhanced FAQ data from JSON file."""
    enhanced_file = Path(__file__).parent / "enhanced_fintech_faq_data.json"

    if not enhanced_file.exists():
        print(f"Enhanced dataset not found at {enhanced_file}")
        print("Please run 'python scripts/download_fintech_datasets.py' first")
        return []

    with open(enhanced_file, 'r') as f:
        data = json.load(f)

    # Flatten the structure
    flat_faqs = []
    for category_data in data['faqs']:
        category = category_data['category']
        for qa in category_data['questions']:
            flat_faqs.append({
                'id': qa['id'],
                'category': category,
                'question': qa['question'],
                'answer': qa['answer'],
                'source': qa.get('source', 'enhanced'),
                'text': f"Question: {qa['question']}\\nAnswer: {qa['answer']}"
            })

    return flat_faqs

def load_original_faq_data() -> List[Dict[str, Any]]:
    """Load original FAQ data from JSON file."""
    original_file = Path(__file__).parent / "fintech_faq_data.json"

    if not original_file.exists():
        print(f"Original dataset not found at {original_file}")
        return []

    with open(original_file, 'r') as f:
        data = json.load(f)

    # Flatten the structure
    flat_faqs = []
    for category_data in data['faqs']:
        category = category_data['category']
        for qa in category_data['questions']:
            flat_faqs.append({
                'id': qa['id'],
                'category': category,
                'question': qa['question'],
                'answer': qa['answer'],
                'source': 'original',
                'text': f"Question: {qa['question']}\\nAnswer: {qa['answer']}"
            })

    return flat_faqs

def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def setup_pinecone_index():
    """Setup Pinecone index with proper configuration."""
    try:
        # Check if index exists
        if PINECONE_INDEX in [index.name for index in pc.list_indexes()]:
            print(f"Index '{PINECONE_INDEX}' already exists. Deleting and recreating...")
            pc.delete_index(PINECONE_INDEX)
            time.sleep(10)  # Wait for deletion to complete

        # Create new index
        print(f"Creating index '{PINECONE_INDEX}'...")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )

        # Wait for index to be ready
        print("Waiting for index to be ready...")
        time.sleep(30)

        print(f"Index '{PINECONE_INDEX}' created successfully!")
        return True

    except Exception as e:
        print(f"Error setting up Pinecone index: {e}")
        return False

def seed_pinecone_data(faqs: List[Dict[str, Any]], batch_size: int = 100):
    """Seed Pinecone with FAQ data in batches."""
    try:
        index = pc.Index(PINECONE_INDEX)

        # Get current index stats
        stats = index.describe_index_stats()
        print(f"Current index stats: {stats.total_vector_count} vectors")

        print(f"Generating embeddings for {len(faqs)} FAQ entries...")

        # Process in batches
        vectors_to_upsert = []

        for i, faq in enumerate(faqs):
            if i % 100 == 0:
                print(f"Processing FAQ {i+1}/{len(faqs)}...")

            try:
                # Generate embedding
                embedding = get_embedding(faq['text'])

                # Prepare vector for upsert
                vector = {
                    'id': faq['id'],
                    'values': embedding,
                    'metadata': {
                        'text': faq['text'][:1000],  # Truncate for metadata size limits
                        'question': faq['question'][:500],
                        'answer': faq['answer'][:1500],
                        'category': faq['category'],
                        'source': faq.get('source', 'unknown')
                    }
                }

                vectors_to_upsert.append(vector)

                # Upsert batch when it reaches batch_size
                if len(vectors_to_upsert) >= batch_size:
                    index.upsert(vectors=vectors_to_upsert)
                    vectors_to_upsert = []
                    time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"Error processing FAQ {faq['id']}: {e}")
                continue

        # Upsert remaining vectors
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)

        # Wait for upserts to complete
        print("Waiting for upserts to complete...")
        time.sleep(10)

        # Get final stats
        final_stats = index.describe_index_stats()
        print(f"Successfully seeded {len(faqs)} FAQ entries to Pinecone!")
        print(f"Final index stats: {final_stats.total_vector_count} vectors")

        return True

    except Exception as e:
        print(f"Error seeding Pinecone: {e}")
        return False

def test_retrieval(query: str, top_k: int = 3):
    """Test retrieval with a sample query."""
    try:
        print(f"\\nTesting with sample query: '{query}'")

        # Get embedding for query
        query_embedding = get_embedding(query)

        # Query Pinecone
        index = pc.Index(PINECONE_INDEX)
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        print(f"Top {top_k} results:")
        for i, match in enumerate(results['matches']):
            score = match['score']
            metadata = match['metadata']
            question = metadata.get('question', 'N/A')
            category = metadata.get('category', 'N/A')
            source = metadata.get('source', 'N/A')

            print(f"  - Score: {score:.3f} | {question[:100]}... | Category: {category} | Source: {source}")

    except Exception as e:
        print(f"Error testing retrieval: {e}")

def main():
    """Main function to seed Pinecone with enhanced fintech data."""
    parser = argparse.ArgumentParser(description="Seed Pinecone with fintech FAQ data")
    parser.add_argument(
        "--dataset",
        choices=["original", "enhanced", "both"],
        default="enhanced",
        help="Which dataset to use for seeding"
    )
    parser.add_argument(
        "--setup-index",
        action="store_true",
        help="Setup/recreate the Pinecone index"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for upserting vectors"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of FAQs to process (for testing)"
    )

    args = parser.parse_args()

    print("=== Enhanced Pinecone Seeding Process ===")

    # Setup index if requested
    if args.setup_index:
        if not setup_pinecone_index():
            print("Failed to setup Pinecone index. Exiting.")
            return

    # Load FAQ data
    print(f"\\nLoading FAQ data (dataset: {args.dataset})...")

    all_faqs = []

    if args.dataset in ["original", "both"]:
        original_faqs = load_original_faq_data()
        if original_faqs:
            all_faqs.extend(original_faqs)
            print(f"Loaded {len(original_faqs)} original FAQ entries")

    if args.dataset in ["enhanced", "both"]:
        enhanced_faqs = load_enhanced_faq_data()
        if enhanced_faqs:
            all_faqs.extend(enhanced_faqs)
            print(f"Loaded {len(enhanced_faqs)} enhanced FAQ entries")

    if not all_faqs:
        print("No FAQ data loaded. Exiting.")
        return

    # Apply limit if specified
    if args.limit:
        all_faqs = all_faqs[:args.limit]
        print(f"Limited to {len(all_faqs)} FAQ entries for testing")

    print(f"\\nTotal FAQ entries to process: {len(all_faqs)}")

    # Display category breakdown
    categories = {}
    sources = {}
    for faq in all_faqs:
        cat = faq['category']
        src = faq.get('source', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
        sources[src] = sources.get(src, 0) + 1

    print("\\nCategory breakdown:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count} entries")

    print("\\nSource breakdown:")
    for source, count in sorted(sources.items()):
        print(f"  - {source}: {count} entries")

    # Seed Pinecone
    print(f"\\nSeeding Pinecone with batch size {args.batch_size}...")
    success = seed_pinecone_data(all_faqs, args.batch_size)

    if success:
        # Test retrieval
        test_queries = [
            "How do I reset my password?",
            "What documents do I need for account verification?",
            "How do I transfer money to another account?",
            "What should I do if my card is stolen?"
        ]

        for query in test_queries:
            test_retrieval(query)

    print("\\n=== Enhanced Pinecone Seeding Complete ===")

if __name__ == "__main__":
    main()