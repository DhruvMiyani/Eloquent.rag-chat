#!/usr/bin/env python3
"""
Seed Pinecone with a diverse sample from the enhanced dataset.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time
import random

# Add parent directory to path to import from api
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pinecone import Pinecone
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

def load_diverse_sample(sample_size: int = 300) -> List[Dict[str, Any]]:
    """Load a diverse sample from enhanced FAQ data."""
    enhanced_file = Path(__file__).parent / "enhanced_fintech_faq_data.json"

    with open(enhanced_file, 'r') as f:
        data = json.load(f)

    # Get sample from each category
    diverse_sample = []

    for category_data in data['faqs']:
        category = category_data['category']
        questions = category_data['questions']

        # Calculate sample size per category
        category_sample_size = min(50, len(questions))  # Max 50 per category
        if category == "Account & Registration":
            category_sample_size = min(100, len(questions))  # More for account questions

        # Random sample from category
        category_sample = random.sample(questions, category_sample_size)

        for qa in category_sample:
            diverse_sample.append({
                'id': qa['id'],
                'category': category,
                'question': qa['question'],
                'answer': qa['answer'],
                'source': qa.get('source', 'enhanced'),
                'text': f"Question: {qa['question']}\\nAnswer: {qa['answer']}"
            })

    # Shuffle and limit
    random.shuffle(diverse_sample)
    return diverse_sample[:sample_size]

def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def seed_diverse_sample():
    """Seed Pinecone with diverse sample."""
    print("Loading diverse sample...")

    # Load diverse sample
    faqs = load_diverse_sample(300)

    print(f"Loaded {len(faqs)} diverse FAQ entries")

    # Show category breakdown
    categories = {}
    for faq in faqs:
        cat = faq['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("Category breakdown:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count} entries")

    # Seed Pinecone
    print("\\nSeeding Pinecone...")

    try:
        index = pc.Index(PINECONE_INDEX)

        # Clear existing data
        print("Clearing existing vectors...")
        index.delete(delete_all=True)
        time.sleep(10)

        vectors_to_upsert = []

        for i, faq in enumerate(faqs):
            if i % 50 == 0:
                print(f"Processing FAQ {i+1}/{len(faqs)}...")

            try:
                # Generate embedding
                embedding = get_embedding(faq['text'])

                # Prepare vector
                vector = {
                    'id': faq['id'],
                    'values': embedding,
                    'metadata': {
                        'text': faq['text'][:1000],
                        'question': faq['question'][:500],
                        'answer': faq['answer'][:1500],
                        'category': faq['category'],
                        'source': faq.get('source', 'unknown')
                    }
                }

                vectors_to_upsert.append(vector)

                # Upsert in batches of 50
                if len(vectors_to_upsert) >= 50:
                    index.upsert(vectors=vectors_to_upsert)
                    vectors_to_upsert = []
                    time.sleep(1)

            except Exception as e:
                print(f"Error processing FAQ {faq['id']}: {e}")
                continue

        # Upsert remaining vectors
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)

        # Wait for completion
        time.sleep(10)

        # Get final stats
        stats = index.describe_index_stats()
        print(f"\\nSuccessfully seeded {stats.total_vector_count} vectors!")

        return True

    except Exception as e:
        print(f"Error seeding Pinecone: {e}")
        return False

def test_diverse_retrieval():
    """Test retrieval with diverse queries."""
    queries = [
        "How do I activate my card?",
        "What are the transfer limits?",
        "How do I report fraud?",
        "What documents do I need for verification?",
        "How to change my password?",
        "What are the fees for international transactions?"
    ]

    try:
        index = pc.Index(PINECONE_INDEX)

        for query in queries:
            print(f"\\nQuery: '{query}'")

            # Get embedding
            query_embedding = get_embedding(query)

            # Search
            results = index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )

            print("Top 3 results:")
            for i, match in enumerate(results['matches']):
                score = match['score']
                metadata = match['metadata']
                question = metadata.get('question', 'N/A')
                category = metadata.get('category', 'N/A')

                print(f"  {i+1}. Score: {score:.3f} | Category: {category}")
                print(f"     Question: {question[:100]}...")

    except Exception as e:
        print(f"Error testing retrieval: {e}")

def main():
    """Main function."""
    print("=== Diverse Sample Pinecone Seeding ===")

    # Set random seed for reproducibility
    random.seed(42)

    # Seed diverse sample
    success = seed_diverse_sample()

    if success:
        # Test retrieval
        print("\\n=== Testing Diverse Retrieval ===")
        test_diverse_retrieval()

    print("\\n=== Seeding Complete ===")

if __name__ == "__main__":
    main()