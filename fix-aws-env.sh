#!/bin/bash

# Fix AWS backend environment variables
echo "🔧 Setting up environment variables on AWS backend..."

# Update the backend .env file on EC2
cat > /tmp/backend_env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY="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"
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Pinecone Configuration
PINECONE_API_KEY=pcsk_64LjaD_JwmDMGeVYu87sqbA6u6zt2HyPXRvfyp9sa3PNyFnFxnR5oipFqY6rUF3xw2nqiM
PINECONE_INDEX=ai-powered-chatbot-challenge
PINECONE_ENDPOINT=https://ai-powered-chatbot-challenge-5g2nluv.svc.aped-4627-b74a.pinecone.io

# Database Configuration
DATABASE_URL=sqlite:///./chat_database.db
USE_DYNAMODB=false

# AWS Configuration (for DynamoDB)
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=chatbot

# Security
SECRET_KEY=eloquent-ai-secret-key-for-development-only-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
FRONTEND_URL=http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com
EOF

# Copy environment file to EC2 and restart the service
scp -i ~/.ssh/eloquent-keypair-20250918012018.pem /tmp/backend_env ec2-user@3.89.59.19:/home/ec2-user/eloquent-backend/.env

# Restart the backend service
ssh -i ~/.ssh/eloquent-keypair-20250918012018.pem ec2-user@3.89.59.19 "cd /home/ec2-user/eloquent-backend && sudo systemctl restart eloquent-backend"

echo "✅ Environment variables updated and service restarted!"