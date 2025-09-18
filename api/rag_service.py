"""RAG (Retrieval-Augmented Generation) service for the chatbot."""

import openai
from typing import List, Tuple, Dict, Any
from pinecone import Pinecone

from config import settings
from models import Citation

# Initialize clients
openai.api_key = settings.OPENAI_API_KEY

# Try to initialize Pinecone, but handle errors gracefully
try:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX)
    pinecone_available = True
except Exception as e:
    print(f"Warning: Could not connect to Pinecone: {e}")
    print("The chatbot will work without RAG functionality")
    index = None
    pinecone_available = False

class RAGService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        response = openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    @staticmethod
    async def retrieve_context(
        query: str,
        top_k: int = settings.VECTOR_SEARCH_TOP_K
    ) -> List[Tuple[str, Citation]]:
        """Retrieve relevant context from Pinecone."""
        # If Pinecone is not available, return empty context
        if not pinecone_available or index is None:
            return []

        # Get embedding for the query
        query_embedding = await RAGService.get_embedding(query)

        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # Process results
        context_citations = []
        for match in results['matches']:
            metadata = match['metadata']
            citation = Citation(
                id=match['id'],
                text=metadata.get('answer', ''),
                category=metadata.get('category', 'General'),
                relevance_score=match['score']
            )
            context_text = metadata.get('text', '')
            context_citations.append((context_text, citation))

        return context_citations

    @staticmethod
    async def generate_response(
        query: str,
        context: List[str],
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate response using OpenAI with retrieved context."""
        # Build the system prompt based on whether we have context
        if context:
            system_prompt = """You are a helpful fintech customer support assistant.
            You answer questions based ONLY on the provided context.
            If the answer is not in the context, politely say you don't have that information.
            Be concise, accurate, and professional.
            When referencing information from the context, be specific about what actions the user should take."""
        else:
            system_prompt = """You are a helpful fintech customer support assistant.
            Note: The knowledge base is currently unavailable, but I'll do my best to help with general information.
            Be concise, accurate, and professional."""

        # Build context string
        context_str = "\\n\\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(context)])

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Only add context if available
        if context_str:
            messages.append({"role": "system", "content": f"Available context:\\n{context_str}"})

        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Add current query
        messages.append({"role": "user", "content": query})

        # Generate response
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=500
        )

        return response.choices[0].message.content

    @staticmethod
    async def process_query(
        query: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, List[Citation]]:
        """Process a query through the full RAG pipeline."""
        # Retrieve context
        context_citations = await RAGService.retrieve_context(query)

        # Extract context texts and citations
        context_texts = [ctx for ctx, _ in context_citations]
        citations = [citation for _, citation in context_citations]

        # Generate response
        response = await RAGService.generate_response(
            query=query,
            context=context_texts,
            chat_history=chat_history
        )

        return response, citations