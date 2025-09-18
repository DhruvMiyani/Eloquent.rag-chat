"""
Local RAG Demo - Search FAQ data without Pinecone
Demonstrates RAG functionality using local keyword search
"""

import json
import re
from typing import List, Dict, Any

class LocalRAGDemo:
    def __init__(self, faq_file_path: str = "fintech_faq_data.json"):
        """Initialize with local FAQ data."""
        with open(faq_file_path, 'r', encoding='utf-8') as f:
            self.faq_data = json.load(f)
        self.faqs = []

        # Flatten FAQ structure for searching
        for category in self.faq_data['faqs']:
            for question_data in category['questions']:
                self.faqs.append({
                    'id': question_data['id'],
                    'category': category['category'],
                    'question': question_data['question'],
                    'answer': question_data['answer'],
                    'keywords': question_data.get('keywords', [])
                })

        print(f"📚 Loaded {len(self.faqs)} FAQ entries")

    def search_faqs(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search FAQs using keyword matching."""
        query_lower = query.lower()
        scored_faqs = []

        for faq in self.faqs:
            score = 0

            # Check question similarity
            if query_lower in faq['question'].lower():
                score += 10

            # Check keywords
            for keyword in faq['keywords']:
                if keyword.lower() in query_lower:
                    score += 5

            # Check answer similarity (partial match)
            answer_words = faq['answer'].lower().split()
            query_words = query_lower.split()
            common_words = set(answer_words) & set(query_words)
            score += len(common_words)

            if score > 0:
                scored_faqs.append({
                    **faq,
                    'similarity_score': score / 10.0  # Normalize score
                })

        # Sort by score and return top_k
        scored_faqs.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_faqs[:top_k]

    def generate_response(self, query: str) -> Dict[str, Any]:
        """Generate RAG response using local search."""
        similar_faqs = self.search_faqs(query, top_k=3)

        if not similar_faqs:
            return {
                'response': "I couldn't find specific information about that. Please try rephrasing your question or contact our support team.",
                'context_used': [],
                'method': 'local_search_fallback'
            }

        # Use the best matching FAQ
        best_match = similar_faqs[0]

        if best_match['similarity_score'] > 0.5:
            # High confidence - return direct answer
            response = f"{best_match['answer']}"
        else:
            # Lower confidence - provide contextual response
            response = f"Based on our FAQ: {best_match['answer']}"

        return {
            'response': response,
            'context_used': similar_faqs,
            'method': 'local_search',
            'confidence': best_match['similarity_score']
        }

# Test the local RAG
if __name__ == "__main__":
    print("🧪 Testing Local RAG Demo")
    print("=" * 40)

    demo = LocalRAGDemo()

    test_queries = [
        "How do I create an account?",
        "What are the transfer limits?",
        "How do I reset my password?",
        "Is my money insured?",
        "How do I enable 2FA?"
    ]

    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = demo.generate_response(query)
        print(f"🤖 Response: {result['response'][:100]}...")
        print(f"📊 Method: {result['method']}, Confidence: {result.get('confidence', 'N/A')}")
        print(f"📝 Context: {len(result['context_used'])} FAQs used")