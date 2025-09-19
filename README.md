# Eloquent AI Financial Assistant
A production-ready RAG-powered chatbot for fintech customer support, demonstrating enterprise-grade software architecture with intelligent response generation using retrieval-augmented generation.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key
- Pinecone API key

### Local Development

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd eloquent-ai-chatbot
   ```

2. **Backend Setup**
   ```bash
   cd eloquent-backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Add your API keys to .env file
   ```

3. **Frontend Setup**
   ```bash
   cd eloquent-ai-frontend
   npm install
   ```

4. **Initialize Vector Database**
   ```bash
   cd eloquent-backend
   source venv/bin/activate
   python setup_vector_db.py
   ```

5. **Start Services**
   ```bash
   # Terminal 1: Backend
   cd eloquent-backend
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8002
   
   # Terminal 2: Frontend
   cd eloquent-ai-frontend
   npm run dev
   ```

6. **Access Application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8002
   - API Documentation: http://localhost:8002/docs




## Overview

This application combines vector search with large language models to provide accurate, contextual responses about financial services. By grounding AI responses in a curated knowledge base, the system significantly reduces hallucinations while maintaining conversational fluency.

## Architecture

### System Components
```
┌─────────────────┐    REST API    ┌─────────────────┐    Vector Search    ┌─────────────────┐
│  Next.js 14     │◄──────────────►│  FastAPI        │◄──────────────────►│   Pinecone      │
│  Frontend       │                │  Backend        │                    │  Vector DB      │
└─────────────────┘                └─────────────────┘                    └─────────────────┘
                                           │                                        
                                           ▼                               
                                   ┌─────────────────┐    
                                   │  OpenAI API     │    
                                   │  GPT-4 + Embed  │    
                                   └─────────────────┘    
```

### Tech Stack

**Frontend**
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- Zustand for state management
- Axios for HTTP client

**Backend**
- FastAPI with Python 3.9+
- SQLAlchemy ORM with SQLite
- JWT authentication
- Async request handling

**AI & Vector Search**
- OpenAI GPT-4 for response generation
- OpenAI text-embedding-3-small for embeddings
- Pinecone for vector similarity search
- Custom RAG pipeline

**Database**
- SQLite for development
- PostgreSQL/DynamoDB for production
- Conversation and message persistence



## Features

### Core Functionality
- **RAG-Powered Responses**: Retrieves relevant context from vector database before generating answers
- **Real-time Chat Interface**: ChatGPT-style UI with message history
- **User Authentication**: Anonymous and registered user support
- **Conversation Management**: Create, view, edit, and delete chat sessions
- **Mobile Responsive**: Optimized for all device sizes

### Knowledge Base
Comprehensive fintech FAQ database covering:
- Account creation and verification
- Payments and transactions
- Security and fraud prevention
- Regulations and compliance
- Technical support

### RAG Implementation
1. **Query Processing**: Convert user input to embeddings
2. **Vector Search**: Find similar content in Pinecone database
3. **Context Retrieval**: Extract top-k relevant FAQ entries
4. **Response Generation**: Use OpenAI GPT-4 with retrieved context
5. **Fallback Handling**: Graceful degradation when services unavailable

## API Documentation

### Authentication Endpoints
```
POST /api/auth/anonymous     # Create anonymous session
POST /api/auth/register      # Register new user
POST /api/auth/login         # User login
POST /api/auth/convert       # Convert anonymous to registered
GET  /api/auth/me           # Get current user info
```

### Chat Endpoints
```
GET    /api/chat/conversations              # List conversations
POST   /api/chat/conversations              # Create conversation
GET    /api/chat/conversations/{id}         # Get conversation with messages
PATCH  /api/chat/conversations/{id}         # Update conversation title
DELETE /api/chat/conversations/{id}         # Delete conversation
POST   /api/chat/conversations/{id}/messages # Send message
```

### Admin Endpoints
```
POST /api/admin/setup-vector-db    # Initialize vector database
GET  /api/admin/vector-db-stats    # Get database statistics
```

## Configuration

### Required Environment Variables
```bash
# Backend (.env)
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=ai-powered-chatbot-challenge
SECRET_KEY=your_secure_secret_key
DATABASE_URL=sqlite:///./chat_database.db
FRONTEND_URL=http://localhost:3001
```

### Optional Configuration
```bash
PINECONE_ENDPOINT=your_pinecone_endpoint
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=INFO
```

## Testing

### Manual Testing
Test the application with these sample queries:
- "How do I create an account?"
- "What are the transfer limits?"
- "How do I enable two-factor authentication?"
- "What should I do if I suspect fraud?"

### API Testing
```bash
# Health check
curl http://localhost:8002/health

# Vector database setup
curl -X POST http://localhost:8002/api/admin/setup-vector-db

# Anonymous authentication
curl -X POST http://localhost:8002/api/auth/anonymous
```

## AWS Deployment

### Production Architecture
```
CloudFront (CDN)
    │
    ├── S3 (Frontend Static Assets)
    └── ALB → ECS Fargate (Backend API)
                │
                ├── RDS Aurora (Database)
                ├── Pinecone (Vector Search)
                └── Secrets Manager (API Keys)
```

### Deployment Components
- **Frontend**: S3 static hosting with CloudFront CDN
- **Backend**: ECS Fargate containers with auto-scaling
- **Database**: RDS Aurora Serverless v2
- **Vector Search**: Managed Pinecone service
- **Security**: AWS Secrets Manager for API keys

### CI/CD Pipeline
```yaml
# GitHub Actions workflow
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    # Build and deploy Next.js to S3
  deploy-backend:
    # Build and deploy FastAPI to ECS
```

## Security

### Implemented Security Features
- JWT-based authentication with secure token handling
- CORS protection for cross-origin requests
- SQL injection prevention through ORM
- XSS protection via React sanitization
- Secure secret key generation
- Environment variable configuration for sensitive data

### Production Security Recommendations
- Enable HTTPS/TLS encryption
- Implement rate limiting per user/IP
- Add request size limits
- Set up comprehensive monitoring and alerting
- Use AWS WAF for additional protection

## Performance & Scalability

### Current Performance
- Sub-second vector search response times
- Efficient async request handling
- Optimized database queries with indexes
- Client-side caching and state management

### Scaling Strategy
- Horizontal scaling through stateless API design
- Database connection pooling
- CDN distribution for global performance
- Auto-scaling based on demand metrics

## Development Workflow

### Code Structure
```
eloquent-ai-frontend/
├── components/          # React UI components
├── lib/                # API client and utilities
├── store/              # Zustand state management
├── types/              # TypeScript definitions
└── app/                # Next.js app router

eloquent-backend/
├── main.py             # FastAPI application
├── rag_service.py      # RAG implementation
├── auth_service.py     # Authentication logic
├── models.py           # Database models
└── requirements.txt    # Python dependencies
```

### Development Best Practices
- Comprehensive TypeScript coverage
- Structured error handling and logging
- Clean separation of concerns
- Extensive inline documentation
- Production-ready configuration management

## Troubleshooting

### Common Issues
1. **API Key Errors**: Verify keys are correctly set in .env files
2. **Module Import Errors**: Ensure virtual environment is activated
3. **CORS Issues**: Check frontend URL configuration in backend
4. **Vector DB Setup**: Verify Pinecone connectivity and permissions

### Debugging Tools
- Backend logs: `uvicorn main:app --reload --log-level debug`
- API documentation: http://localhost:8002/docs
- Browser DevTools for frontend debugging
- Database inspection via SQLite browser
