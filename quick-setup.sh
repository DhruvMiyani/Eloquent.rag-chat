#!/bin/bash
set -e

echo "🚀 Quick Setup for Eloquent AI Backend on EC2"

# Update system
echo "📦 Installing dependencies..."
sudo yum update -y
sudo yum install python3 python3-pip nginx -y

# Extract backend
echo "📂 Extracting backend code..."
tar -xzf backend.tar.gz
cd eloquent-backend

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file with production settings
echo "⚙️ Creating environment configuration..."
cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./chat_database.db

# OpenAI
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=pcsk_4uxHqv_QzMnXgFD1EbZsYa36wdGXGpxWczP1QFvr3mJ8wVo8VyJHqK2pA8WuRJ6RHyXPPU
PINECONE_INDEX=ai-powered-chatbot-challenge
PINECONE_ENDPOINT=https://ai-powered-chatbot-challenge-5g2nluv.svc.aped-4627-b74a.pinecone.io

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
ANONYMOUS_TOKEN_EXPIRE_DAYS=90

# CORS
FRONTEND_URL=http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com

# Features
ENABLE_ANONYMOUS_USERS=true
ENABLE_USER_REGISTRATION=true
ENABLE_RAG=true
MAX_CONVERSATION_LENGTH=100
MAX_MESSAGE_LENGTH=2000

# Logging
LOG_LEVEL=INFO
EOF

# Run the backend directly (for testing)
echo "🎯 Starting backend server..."
echo "Backend will be available at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"

# Kill any existing Python processes on port 8000
sudo pkill -f "uvicorn main:app" || true

# Start the backend
nohup python main.py > backend.log 2>&1 &

echo ""
echo "✅ Backend is starting! Check status with:"
echo "   tail -f backend.log"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "📱 Your app is now available at:"
echo "   http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com"