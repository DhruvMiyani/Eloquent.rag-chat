#!/usr/bin/env python3
"""
Seed Pinecone vector database with fintech FAQ data.
This script embeds FAQ questions and answers and uploads them to Pinecone for RAG.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

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

def load_faq_data() -> List[Dict[str, Any]]:
    """Load FAQ data from JSON file."""
    faq_file = Path(__file__).parent / "fintech_faq_data.json"
    with open(faq_file, 'r') as f:
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
                'text': f"Question: {qa['question']}\\nAnswer: {qa['answer']}"
            })

    return flat_faqs

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI API."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def create_or_get_index():
    """Create Pinecone index if it doesn't exist."""
    index_list = pc.list_indexes()
    index_names = [idx.name for idx in index_list]

    if PINECONE_INDEX not in index_names:
        print(f"Creating index '{PINECONE_INDEX}'...")

        # Determine embedding dimension based on model
        dimension = 1536  # default for text-embedding-3-small
        if "text-embedding-3-large" in EMBEDDING_MODEL:
            dimension = 3072
        elif "text-embedding-ada-002" in EMBEDDING_MODEL:
            dimension = 1536

        pc.create_index(
            name=PINECONE_INDEX,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Index '{PINECONE_INDEX}' created successfully!")
        # Wait for index to be ready
        time.sleep(10)
    else:
        print(f"Index '{PINECONE_INDEX}' already exists.")

    return pc.Index(PINECONE_INDEX)

def seed_pinecone():
    """Main function to seed Pinecone with FAQ data."""
    print("Starting Pinecone seeding process...")

    # Load FAQ data
    print("Loading FAQ data...")
    faqs = load_faq_data()
    print(f"Loaded {len(faqs)} FAQ entries")

    # Get or create index
    index = create_or_get_index()

    # Check current index stats
    stats = index.describe_index_stats()
    print(f"Current index stats: {stats.total_vector_count} vectors")

    # Prepare vectors for upsert
    print("Generating embeddings...")
    vectors = []

    for i, faq in enumerate(faqs):
        if (i + 1) % 10 == 0:
            print(f"Processing FAQ {i + 1}/{len(faqs)}...")

        # Generate embedding for the combined question and answer
        embedding = get_embedding(faq['text'])

        # Create vector record
        vector = {
            'id': faq['id'],
            'values': embedding,
            'metadata': {
                'category': faq['category'],
                'question': faq['question'],
                'answer': faq['answer'],
                'text': faq['text']
            }
        }
        vectors.append(vector)

        # Upsert in batches of 10
        if len(vectors) >= 10:
            index.upsert(vectors=vectors)
            vectors = []

    # Upsert remaining vectors
    if vectors:
        index.upsert(vectors=vectors)

    print(f"Successfully seeded {len(faqs)} FAQ entries to Pinecone!")

    # Verify the upload
    time.sleep(2)  # Wait for eventual consistency
    stats = index.describe_index_stats()
    print(f"Final index stats: {stats.total_vector_count} vectors")

    # Test with a sample query
    print("\\nTesting with sample query...")
    test_query = "How do I reset my password?"
    test_embedding = get_embedding(test_query)
    results = index.query(
        vector=test_embedding,
        top_k=3,
        include_metadata=True
    )

    print(f"Query: '{test_query}'")
    print("Top 3 results:")
    for match in results['matches']:
        print(f"  - Score: {match['score']:.3f} | {match['metadata']['question'][:50]}...")

if __name__ == "__main__":
    try:
        seed_pinecone()
    except Exception as e:
        print(f"Error seeding Pinecone: {e}")
        sys.exit(1)