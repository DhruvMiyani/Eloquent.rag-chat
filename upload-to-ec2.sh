#!/bin/bash
set -e

EC2_IP="3.89.59.19"
KEY_FILE="eloquent-keypair-20250918012018.pem"

echo "🚀 Uploading code to EC2..."

# Create a temporary directory with only backend code
echo "📦 Preparing backend code..."
rm -rf temp-backend
mkdir temp-backend
cp -r eloquent-backend/* temp-backend/

# Add the production environment file
cat > temp-backend/.env << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///./chat_database.db

# OpenAI Configuration
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Pinecone Configuration
PINECONE_API_KEY=pcsk_4uxHqv_QzMnXgFD1EbZsYa36wdGXGpxWczP1QFvr3mJ8wVo8VyJHqK2pA8WuRJ6RHyXPPU
PINECONE_INDEX=ai-powered-chatbot-challenge
PINECONE_ENDPOINT=https://ai-powered-chatbot-challenge-5g2nluv.svc.aped-4627-b74a.pinecone.io

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
ANONYMOUS_TOKEN_EXPIRE_DAYS=90

# CORS
FRONTEND_URL=http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=60

# Features
ENABLE_ANONYMOUS_USERS=true
ENABLE_USER_REGISTRATION=true
ENABLE_RAG=true
MAX_CONVERSATION_LENGTH=100
MAX_MESSAGE_LENGTH=2000

# Logging
LOG_LEVEL=INFO
EOF

# Upload files to EC2
echo "📤 Uploading files to EC2..."
scp -i ${KEY_FILE} -o StrictHostKeyChecking=no -r temp-backend/ ec2-user@${EC2_IP}:~/

echo "✅ Code uploaded successfully!"
echo ""
echo "Next: Connect to EC2 and setup the backend:"
echo "ssh -i ${KEY_FILE} ec2-user@${EC2_IP}"

# Clean up
rm -rf temp-backend