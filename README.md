# AI-Powered Chatbot with RAG

A full-stack web application featuring an AI-powered chatbot using retrieval-augmented generation (RAG) for accurate fintech customer support.

## Features

- **RAG-powered responses**: Retrieves relevant context from Pinecone vector database before generating answers
- **Chat persistence**: Stores conversation history with support for both SQLite and DynamoDB
- **User management**: Supports both anonymous and returning users with device-based identification
- **Modern UI**: Clean, ChatGPT-inspired interface built with Next.js and TypeScript
- **Production-ready**: Designed for AWS deployment with scalability in mind

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