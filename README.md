# Banking Chatbot with RAG Implementation

## Local development
https://github.com/DhruvMiyani/Eloquent.rag-chat/tree/local-test
  


✅ **Auto-deployment configured** - GitHub Actions deploys to AWS on push to main branch. (Updated EC2 IP)


<img width="725" height="415" alt="Screenshot 2025-09-18 at 11 56 04 AM" src="https://github.com/user-attachments/assets/d84e9f94-e0f2-40a2-82c1-a1ed6df49b30" />




A production-ready full-stack web application featuring an AI-powered chatbot with Retrieval-Augmented Generation (RAG) for fintech FAQ support.

## 🎯 Project Overview

This application demonstrates a complete RAG implementation for a fintech company's customer support chatbot. The system retrieves relevant information from a comprehensive FAQ knowledge base before generating AI responses, significantly reducing hallucinations and improving answer accuracy.


##  Architecture

```
📦 Project Structure
├── eloquent-ai-frontend/          # Next.js 14 + TypeScript
│   ├── components/               # React components
│   ├── lib/                     # API client & utilities
│   ├── store/                   # Zustand state management
│   └── app/                     # Next.js app router
├── eloquent-backend/             # FastAPI + Python
│   ├── main.py                  # FastAPI application
│   ├── rag_service.py           # RAG implementation
│   ├── setup_vector_db.py       # Database initialization
│   └── fintech_faq_data.json    # Knowledge base
└── README.md
```

### Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.9+
- **OpenAI API Key** (for AI responses)
- **Pinecone API Key** (for vector search)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd eloquent-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file with your API keys:
# OPENAI_API_KEY=your_openai_api_key_here
# PINECONE_API_KEY=your_pinecone_api_key_here
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd eloquent-ai-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Initialize Vector Database

```bash
# In the backend directory
cd eloquent-backend
source venv/bin/activate

# Run the setup script to populate Pinecone
python setup_vector_db.py
```

### 4. Start Both Services

```bash
# Terminal 1: Backend (from eloquent-backend/)
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# Terminal 2: Frontend (from eloquent-ai-frontend/)
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

## 📊 Knowledge Base

The system includes a comprehensive fintech FAQ database with 25+ questions across 5 categories:

1. **Account & Registration** - Account creation, verification, passwords
2. **Payments & Transactions** - Money transfers, limits, fees
3. **Security & Fraud Prevention** - 2FA, fraud reporting, data protection
4. **Regulations & Compliance** - Licensing, insurance, tax reporting
5. **Technical Support** - Login issues, app problems, troubleshooting

## 🧠 RAG Implementation Details

### Vector Database (Pinecone)
- **Embedding Model**: OpenAI text-embedding-ada-002
- **Vector Dimensions**: 1536
- **Similarity Metric**: Cosine similarity
- **Index Type**: Pod-based (p1.x1)

### Response Generation
1. **Query Processing**: User question is converted to embeddings
2. **Similarity Search**: Top 3 most relevant FAQs retrieved
3. **Context Assembly**: Retrieved content formatted for AI prompt
4. **Response Generation**: OpenAI GPT-3.5-turbo generates contextual response
5. **Fallback Handling**: Graceful degradation when services are unavailable

### Example RAG Flow

```python
# User asks: "How do I reset my password?"
# 1. Convert to embeddings
# 2. Search Pinecone for similar questions
# 3. Retrieve top matches:
#    - "How do I reset my password?" (score: 0.98)
#    - "What should I do if I can't login?" (score: 0.85)
# 4. Generate AI response using retrieved context
```

## 🔐 Authentication System

### Anonymous Users
- Instant access without registration
- Temporary session with UUID
- Limited conversation history (session-based)

### Registered Users
- JWT-based authentication
- Persistent conversation history
- Enhanced security features
- Account management capabilities

## 🛠️ API Endpoints

### Authentication
- `POST /api/auth/anonymous` - Create anonymous session
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login

### Chat Management
- `GET /api/chat/conversations` - List conversations
- `POST /api/chat/conversations` - Create new conversation
- `GET /api/chat/conversations/{id}` - Get conversation details
- `POST /api/chat/conversations/{id}/messages` - Send message
- `DELETE /api/chat/conversations/{id}` - Delete conversation

### Admin/Setup
- `POST /api/admin/setup-vector-db` - Initialize vector database
- `GET /api/admin/vector-db-stats` - Get database statistics

## 🔧 Configuration

### Environment Variables

```bash
# Required for full functionality
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional configuration
PINECONE_ENVIRONMENT=us-east-1
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///./chat_database.db
FRONTEND_URL=http://localhost:3001
```

### API Keys Setup

1. **OpenAI API Key**:
   - Visit https://platform.openai.com/api-keys
   - Create new API key
   - Add to `.env` file

2. **Pinecone API Key**:
   - Visit https://app.pinecone.io/
   - Create account and get API key
   - Add to `.env` file

## 🧪 Testing

### Manual Testing
1. Open http://localhost:3001
2. Start a new chat
3. Ask questions like:
   - "How do I create an account?"
   - "What are the transfer limits?"
   - "How do I enable 2FA?"

### API Testing
```bash
# Test health endpoint
curl http://localhost:8002/health

# Test vector database setup
curl -X POST http://localhost:8002/api/admin/setup-vector-db

# Test anonymous auth
curl -X POST http://localhost:8002/api/auth/anonymous
```

## Deployment

### AWS Deployment Strategy

#### Frontend (Vercel/Netlify)
```bash
cd eloquent-ai-frontend
npm run build
# Deploy to Vercel or Netlify
```

#### Backend (AWS Lambda/ECS)
```bash
cd eloquent-backend
# Option 1: AWS Lambda with Mangum
# Option 2: ECS/Fargate container
# Option 3: EC2 with gunicorn + nginx
```

#### Database
- **Development**: SQLite (included)
- **Production**: PostgreSQL with connection pooling

## 📈 Performance & Scalability

### Current Performance
- **Frontend**: Fast load times with Next.js optimization
- **Backend**: Handles concurrent requests efficiently
- **Database**: SQLite sufficient for moderate usage
- **Vector Search**: Sub-second response times

### Scaling Considerations
- **Horizontal Scaling**: Stateless API design
- **Database**: Easy PostgreSQL migration
- **Caching**: Redis integration ready
- **CDN**: Frontend can be distributed globally

## 🛡️ Security Features

### Implemented
- JWT-based authentication
- Secure secret key generation
- CORS protection
- SQL injection protection (SQLAlchemy ORM)
- XSS protection (React sanitization)

### Production Recommendations
- Enable HTTPS
- Add rate limiting
- Implement request size limits
- Set up monitoring and alerting
- Add input validation

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid API Key" errors**
   - Verify OpenAI and Pinecone API keys in `.env`
   - Check API key permissions

2. **ModuleNotFoundError**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

3. **CORS errors**
   - Check frontend URL in backend configuration
   - Verify CORS settings in `main.py`

4. **Vector database setup fails**
   - Verify Pinecone API key and environment
   - Check network connectivity
   - Run `python setup_vector_db.py` manually

## 📝 Development Notes

### Code Quality
- **TypeScript**: Full type safety in frontend
- **Python**: Type hints and proper error handling
- **Linting**: ESLint for frontend, Python best practices
- **Testing**: Ready for unit and integration tests

### Software Engineering Practices
- **Modular Architecture**: Clear separation of concerns
- **Error Handling**: Comprehensive error management
- **Logging**: Structured logging for debugging
- **Documentation**: Extensive inline documentation

## Tech Stack

### Backend
- **FastAPI** (Python) - High-performance API framework
- **OpenAI API** - LLM for response generation and embeddings
- **Pinecone** - Vector database for semantic search
- **SQLite/DynamoDB** - Chat persistence
- **Mangum** - AWS Lambda adapter

### Frontend
- **Next.js** - React framework with TypeScript
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **js-cookie** - Cookie management

## Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key
- Pinecone API key (provided in assignment)
- AWS account (for production deployment)

## Local Development Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd AI-Engineer-Technical-Assignment
```

### 2. Backend Setup

```bash
# Navigate to API directory
cd api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Seed Pinecone Database

```bash
# From project root
cd scripts
python seed_pinecone.py
```

This will embed and upload the fintech FAQ data to Pinecone.

### 4. Start Backend Server

```bash
# From api directory
uvicorn main:app --reload --port 8001
```

The API will be available at http://localhost:8001
API documentation: http://localhost:8001/docs

### 5. Frontend Setup

```bash
# In a new terminal, navigate to app directory
cd app

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

- `POST /api/chat` - Send a message and receive AI response
- `GET /api/chats/{chat_id}` - Get chat history
- `GET /api/chats` - List all chats for a user/device
- `GET /health` - Health check endpoint

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Next.js    │────▶│   FastAPI    │────▶│   Pinecone   │
│   Frontend   │     │   Backend    │     │Vector Search │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   OpenAI     │
                     │     LLM      │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  SQLite/     │
                     │  DynamoDB    │
                     └──────────────┘
```

### RAG Pipeline

1. User sends a query
2. Query is embedded using OpenAI embeddings
3. Semantic search in Pinecone retrieves relevant FAQ content
4. Retrieved context + query sent to OpenAI LLM
5. LLM generates response based only on provided context
6. Response with citations returned to user

## AWS Deployment Architecture

### Infrastructure Design

```
┌─────────────────────────────────────────────────────────────┐
│                         CloudFront                          │
│                    (Global CDN Distribution)                │
└─────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                              ▼
┌──────────────────┐                        ┌──────────────────┐
│   S3 Bucket      │                        │  API Gateway     │
│ (Static Website) │                        │   (REST API)     │
└──────────────────┘                        └──────────────────┘
                                                      │
                                                      ▼
                                            ┌──────────────────┐
                                            │  Lambda Function │
                                            │    (FastAPI)     │
                                            └──────────────────┘
                                                      │
                ┌─────────────────────────────────────┼─────────────────────────┐
                ▼                                     ▼                         ▼
        ┌──────────────────┐            ┌──────────────────┐        ┌──────────────────┐
        │    DynamoDB      │            │    Pinecone      │        │     OpenAI       │
        │  (Chat Storage)  │            │ (Vector Search)  │        │      API         │
        └──────────────────┘            └──────────────────┘        └──────────────────┘
```

### Deployment Components

#### Frontend
- **S3**: Static website hosting for Next.js build
- **CloudFront**: CDN for global distribution and HTTPS
- **Route 53**: DNS management (optional)

#### Backend
- **API Gateway**: RESTful API endpoint management
- **Lambda**: Serverless compute for FastAPI via Mangum
- **DynamoDB**: NoSQL database for chat persistence
  - Partition Key: `chat_id`
  - Sort Key: `timestamp`
  - GSI: `user_id`, `device_id` for user queries

#### Security & Configuration
- **Secrets Manager**: Store API keys (OpenAI, Pinecone)
- **IAM Roles**: Lambda execution role with DynamoDB access
- **SSM Parameter Store**: Environment configuration

### Deployment Steps

#### 1. Build Frontend
```bash
cd app
npm run build
npm run export  # If using static export
```

#### 2. Deploy Frontend to S3
```bash
aws s3 sync out/ s3://your-bucket-name --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

#### 3. Package Lambda Function
```bash
cd api
pip install -r requirements.txt -t package/
cp *.py package/
cd package
zip -r ../function.zip .
```

#### 4. Deploy Lambda
```bash
aws lambda create-function \
  --function-name chatbot-api \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --handler main.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 512
```

#### 5. Configure API Gateway
```bash
# Create REST API
# Configure Lambda proxy integration
# Deploy to stage
```

### Environment Variables (Lambda)

```
OPENAI_API_KEY=<from Secrets Manager>
PINECONE_API_KEY=<from Secrets Manager>
USE_DYNAMODB=true
DYNAMODB_TABLE_PREFIX=chatbot
AWS_REGION=us-east-1
```

### Scaling Considerations

1. **Lambda Concurrency**: Set reserved concurrency for consistent performance
2. **DynamoDB Auto-scaling**: Configure read/write capacity auto-scaling
3. **API Gateway Throttling**: Set rate limits to prevent abuse
4. **CloudFront Caching**: Cache static assets aggressively
5. **Pinecone**: Serverless, scales automatically

### Monitoring & Logging

- **CloudWatch Logs**: Lambda function logs
- **X-Ray**: Distributed tracing for debugging
- **CloudWatch Alarms**: Alert on errors, high latency
- **DynamoDB Metrics**: Monitor capacity utilization

## CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test Backend
        run: |
          cd api
          pip install -r requirements.txt
          pytest
      - name: Test Frontend
        run: |
          cd app
          npm install
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Frontend to S3
        # S3 sync commands
      - name: Deploy Lambda
        # Lambda update commands
```

## Architectural Decisions

### 1. RAG Implementation
- **Pinecone** for vector search: Serverless, low latency, scalable
- **OpenAI embeddings**: Industry standard, high quality
- **Top-k retrieval**: Balance between context and relevance

### 2. Database Choice
- **Development**: SQLite for simplicity
- **Production**: DynamoDB for scalability and AWS integration
- Abstracted database layer for easy switching

### 3. User Management
- **Device ID cookies**: Simple anonymous user tracking
- **JWT ready**: Authentication structure in place for future
- **Graceful degradation**: Works without cookies

### 4. Frontend Architecture
- **Next.js**: SSR capabilities, excellent DX, production ready
- **Component-based**: Reusable chat components
- **Optimistic updates**: Better UX for message sending

### 5. AWS Deployment
- **Serverless**: Cost-effective, auto-scaling
- **Managed services**: Reduce operational overhead
- **Global distribution**: CloudFront for worldwide access

## Trade-offs

1. **SQLite vs DynamoDB**: Simplicity vs scalability
2. **Serverless vs Container**: Cost vs cold starts
3. **Client-side state**: Simplicity vs offline capability
4. **Rate limiting**: Not implemented for MVP simplicity

## Future Enhancements

1. **Authentication**: Full JWT implementation with user accounts
2. **WebSocket**: Real-time streaming responses
3. **Multi-language**: i18n support
4. **Analytics**: Usage tracking and insights
5. **Feedback loop**: User ratings for response quality
6. **Caching layer**: Redis for frequently asked questions
7. **Voice interface**: Speech-to-text integration

## Testing

### Backend Tests
```bash
cd api
pytest tests/
```

### Frontend Tests
```bash
cd app
npm test
```

## License

MIT

## Support

For issues or questions, please open a GitHub issue.
