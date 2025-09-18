"""
RAG Service for Fintech FAQ Retrieval-Augmented Generation
Handles vector database operations and AI response generation.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
import openai
import tiktoken
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize RAG service with Pinecone and OpenAI clients."""
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.pinecone_endpoint = os.getenv("PINECONE_ENDPOINT")
        self.index_name = os.getenv("PINECONE_INDEX", "ai-powered-chatbot-challenge")

        # Initialize clients
        self.pc = None
        self.index = None
        self.openai_client = None

        # Token encoder for text chunking
        self.encoding = tiktoken.get_encoding("cl100k_base")

        if self.pinecone_api_key:
            try:
                # Initialize Pinecone with endpoint if provided
                if self.pinecone_endpoint:
                    self.pc = Pinecone(api_key=self.pinecone_api_key)
                    logger.info(f"Pinecone client initialized with endpoint: {self.pinecone_endpoint}")
                else:
                    self.pc = Pinecone(api_key=self.pinecone_api_key)
                    logger.info("Pinecone client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}")
        else:
            logger.warning("PINECONE_API_KEY not found in environment variables")

        if self.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")

    async def setup_index(self) -> bool:
        """Connect to existing Pinecone index."""
        if not self.pc:
            logger.error("Pinecone client not initialized")
            return False

        try:
            # Connect directly to the existing index
            logger.info(f"Connecting to existing index: {self.index_name}")
            self.index = self.pc.Index(self.index_name)

            # Test the connection
            stats = self.index.describe_index_stats()
            logger.info(f"Successfully connected to index. Stats: {stats}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to index: {e}")
            return False

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI."""
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return None

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def index_faq_data(self, faq_file_path: str) -> bool:
        """Index FAQ data into Pinecone vector database."""
        if not self.index:
            if not await self.setup_index():
                return False

        try:
            # Load FAQ data
            with open(faq_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            vectors_to_upsert = []

            for category in data['faqs']:
                category_name = category['category']

                for question_data in category['questions']:
                    question_id = question_data['id']
                    question = question_data['question']
                    answer = question_data['answer']
                    keywords = question_data.get('keywords', [])

                    # Combine question and answer for better context
                    text_to_embed = f"Question: {question}\nAnswer: {answer}"

                    # Get embedding
                    embedding = await self.get_embedding(text_to_embed)
                    if not embedding:
                        logger.warning(f"Failed to generate embedding for {question_id}")
                        continue

                    # Prepare metadata
                    metadata = {
                        'id': question_id,
                        'category': category_name,
                        'question': question,
                        'answer': answer,
                        'keywords': keywords,
                        'indexed_at': datetime.now().isoformat()
                    }

                    vectors_to_upsert.append({
                        'id': question_id,
                        'values': embedding,
                        'metadata': metadata
                    })

                    logger.info(f"Prepared vector for {question_id}: {question[:50]}...")

            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} vectors")

            logger.info(f"Successfully indexed {len(vectors_to_upsert)} FAQ items")
            return True

        except Exception as e:
            logger.error(f"Failed to index FAQ data: {e}")
            return False

    async def search_similar_faqs(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar FAQs using vector similarity."""
        if not self.index:
            logger.error("Pinecone index not initialized")
            return []

        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                return []

            # Search similar vectors
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            similar_faqs = []
            for match in search_results.matches:
                similar_faqs.append({
                    'id': match.metadata['id'],
                    'category': match.metadata['category'],
                    'question': match.metadata['question'],
                    'answer': match.metadata['answer'],
                    'keywords': match.metadata['keywords'],
                    'similarity_score': float(match.score)
                })

            logger.info(f"Found {len(similar_faqs)} similar FAQs for query: {query[:50]}...")
            return similar_faqs

        except Exception as e:
            logger.error(f"Failed to search similar FAQs: {e}")
            return []

    async def generate_rag_response(self, user_query: str) -> Dict[str, Any]:
        """Generate AI response using RAG (Retrieval-Augmented Generation)."""
        try:
            # Step 1: Retrieve relevant context
            similar_faqs = await self.search_similar_faqs(user_query, top_k=3)

            if not similar_faqs:
                return {
                    'response': "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your question or contact our support team for assistance.",
                    'context_used': [],
                    'fallback': True
                }

            # Step 2: Prepare context for AI
            context_text = ""
            for i, faq in enumerate(similar_faqs, 1):
                context_text += f"FAQ {i}:\nQ: {faq['question']}\nA: {faq['answer']}\n\n"

            # Step 3: Generate response using OpenAI
            if not self.openai_client:
                # Fallback to best matching FAQ
                best_match = similar_faqs[0]
                return {
                    'response': best_match['answer'],
                    'context_used': [best_match],
                    'fallback': True,
                    'note': 'This is a direct FAQ match as AI service is not available.'
                }

            # Create prompt for AI
            system_prompt = """You are a helpful customer service assistant for a fintech company.
            Use the provided FAQ context to answer the user's question accurately and helpfully.
            If the context doesn't fully answer the question, use your knowledge while staying relevant to fintech services.
            Be concise, professional, and friendly in your response."""

            user_prompt = f"""Context from our FAQ database:
            {context_text}

            User Question: {user_query}

            Please provide a helpful and accurate response based on the context above."""

            # Generate AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content

            return {
                'response': ai_response,
                'context_used': similar_faqs,
                'fallback': False
            }

        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            return {
                'response': "I'm experiencing technical difficulties. Please try again later or contact our support team.",
                'context_used': [],
                'error': str(e),
                'fallback': True
            }

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index."""
        if not self.index:
            return {'error': 'Index not initialized'}

        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'index_fullness': stats.index_fullness,
                'dimension': stats.dimension
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {'error': str(e)}