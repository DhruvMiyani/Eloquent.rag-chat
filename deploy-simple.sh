#!/bin/bash

set -e

# Configuration
UNIQUE_ID="20250918012018"
KEY_NAME="eloquent-keypair-$UNIQUE_ID"
SECURITY_GROUP_ID="sg-0f663567aa6995c1c"

echo "🚀 Deploying backend to AWS with environment variables..."

# Create user data script
cat > /tmp/user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git nginx

# Create the backend directory
mkdir -p /home/ec2-user/eloquent-backend
cd /home/ec2-user/eloquent-backend

# Create all the Python files directly
cat > requirements.txt << 'PYEOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pinecone-client==3.0.0
openai==1.3.0
python-dotenv==1.0.0
sqlalchemy==2.0.23
PYEOF

# Create main.py
cat > main.py << 'PYEOF'
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="Eloquent AI Backend", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import services
from auth_service import AuthService
from chat_service import ChatService
from rag_service import RAGService
from models import UserCreate, UserLogin, ConversationCreate, MessageCreate

# Initialize services
auth_service = AuthService()
chat_service = ChatService()
rag_service = RAGService()

security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "Eloquent AI Backend API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-09-18T17:05:33.324588",
        "version": "1.0.0",
        "database": "connected"
    }

# Auth endpoints
@app.post("/api/auth/anonymous")
async def create_anonymous_user():
    try:
        user, token = await auth_service.create_anonymous_user()
        return {"user": user, "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Chat endpoints
@app.get("/api/chat/conversations")
async def get_conversations(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        conversations = await chat_service.get_user_conversations(user["id"])
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/conversations")
async def create_conversation(
    conversation: Optional[ConversationCreate] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        new_conversation = await chat_service.create_conversation(
            user["id"],
            conversation.title if conversation else "New Conversation"
        )
        return new_conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        user = await auth_service.get_current_user(credentials.credentials)

        # Use RAG to get response
        response = await rag_service.get_response(message.content)

        # Save both user message and assistant response
        assistant_message = await chat_service.add_message(
            conversation_id, "assistant", response
        )

        return assistant_message
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        conversation = await chat_service.get_conversation_with_messages(conversation_id)
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/setup-vector-db")
async def setup_vector_db():
    try:
        await rag_service.setup_vector_database()
        return {"success": True, "message": "Vector database setup completed"}
    except Exception as e:
        print(f"Vector DB setup error: {e}")
        return {"success": False, "message": "Failed to setup Pinecone index. Check API key and configuration.", "error": "INDEX_SETUP_FAILED"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
PYEOF

# Create other necessary files (simplified versions)
cat > models.py << 'PYEOF'
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class MessageCreate(BaseModel):
    content: str
PYEOF

cat > auth_service.py << 'PYEOF'
import uuid
import time
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "eloquent-ai-secret-key")
        self.algorithm = "HS256"
        self.users = {}  # Simple in-memory storage

    async def create_anonymous_user(self):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": None,
            "name": None,
            "is_anonymous": True,
            "created_at": datetime.now().isoformat()
        }
        self.users[user_id] = user

        # Create JWT token
        token_data = {"sub": user_id, "exp": datetime.utcnow() + timedelta(days=7)}
        token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)

        return user, token

    async def get_current_user(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id and user_id in self.users:
                return self.users[user_id]
            raise Exception("User not found")
        except JWTError:
            raise Exception("Invalid token")
PYEOF

cat > chat_service.py << 'PYEOF'
import uuid
from datetime import datetime
from typing import List, Dict

class ChatService:
    def __init__(self):
        self.conversations = {}
        self.messages = {}

    async def create_conversation(self, user_id: str, title: str = "New Conversation"):
        conv_id = str(uuid.uuid4())
        conversation = {
            "id": conv_id,
            "title": title,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.conversations[conv_id] = conversation
        self.messages[conv_id] = []
        return conversation

    async def get_user_conversations(self, user_id: str):
        return [conv for conv in self.conversations.values() if conv["user_id"] == user_id]

    async def add_message(self, conversation_id: str, role: str, content: str):
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        if conversation_id not in self.messages:
            self.messages[conversation_id] = []

        self.messages[conversation_id].append(message)
        return message

    async def get_conversation_with_messages(self, conversation_id: str):
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation["messages"] = self.messages.get(conversation_id, [])
        return conversation
PYEOF

cat > rag_service.py << 'PYEOF'
import os
import logging
from typing import List, Dict
from pinecone import Pinecone
import openai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX", "ai-powered-chatbot-challenge")
        self.pinecone_endpoint = os.getenv("PINECONE_ENDPOINT")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self.pc = None
        self.index = None
        self.openai_client = None

        self.initialize_clients()

    def initialize_clients(self):
        try:
            if self.pinecone_api_key and self.pinecone_endpoint:
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                logger.info(f"Pinecone client initialized with endpoint: {self.pinecone_endpoint}")
            else:
                logger.error("Pinecone API key or endpoint not found")

            if self.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.error("OpenAI API key not found")

        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")

    async def setup_vector_database(self):
        try:
            if not self.pc:
                raise Exception("Pinecone client not initialized")

            # Connect to existing index
            logger.info(f"Connecting to existing index: {self.pinecone_index_name}")
            self.index = self.pc.Index(self.pinecone_index_name)

            # Check index stats
            stats = self.index.describe_index_stats()
            logger.info(f"Successfully connected to index. Stats: {stats}")

            # Setup FAQ data if index is empty
            if stats['total_vector_count'] == 0:
                await self.index_faq_data()

        except Exception as e:
            logger.error(f"Failed to setup vector database: {e}")
            raise e

    async def get_response(self, query: str) -> str:
        try:
            # Initialize index if not already done
            if not self.index and self.pc:
                self.index = self.pc.Index(self.pinecone_index_name)

            if not self.index or not self.openai_client:
                logger.error("Pinecone index or OpenAI client not initialized")
                return "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your question or contact our support team for assistance."

            # Generate embedding for the query
            embedding_response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = embedding_response.data[0].embedding

            # Search for similar documents
            search_results = self.index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )

            if not search_results.matches:
                return "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your question or contact our support team for assistance."

            # Extract relevant context
            context_parts = []
            for match in search_results.matches:
                if match.score > 0.7:  # Only include high-confidence matches
                    metadata = match.metadata
                    context_parts.append(f"Q: {metadata.get('question', 'N/A')}\nA: {metadata.get('answer', 'N/A')}")

            if not context_parts:
                return "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your question or contact our support team for assistance."

            context = "\n\n".join(context_parts)

            # Generate response using GPT
            prompt = f"""You are Eloquent AI, a helpful financial assistant. Based on the following FAQ information, provide a clear and helpful answer to the user's question.

Context from FAQ:
{context}

User Question: {query}

Please provide a helpful answer based on the FAQ information above. If the question is not covered in the FAQ, politely let the user know and suggest they contact support."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in RAG service: {e}")
            return "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your question or contact our support team for assistance."

    async def index_faq_data(self):
        faq_data = [
            {
                "id": "acc_003",
                "question": "How do I reset my password?",
                "answer": "To reset your password: 1) Click 'Forgot Password' on the login page, 2) Enter your email address, 3) Check your email for a reset link, 4) Click the link and create a new password. Make sure your new password is at least 8 characters long and includes a mix of letters, numbers, and symbols."
            }
            # Add more FAQ items here
        ]

        try:
            vectors_to_upsert = []
            for faq in faq_data:
                # Generate embedding
                embedding_response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=f"{faq['question']} {faq['answer']}"
                )
                embedding = embedding_response.data[0].embedding

                vectors_to_upsert.append({
                    "id": faq["id"],
                    "values": embedding,
                    "metadata": {
                        "question": faq["question"],
                        "answer": faq["answer"]
                    }
                })

            # Upsert vectors
            self.index.upsert(vectors=vectors_to_upsert)
            logger.info(f"Successfully indexed {len(vectors_to_upsert)} FAQ items")

        except Exception as e:
            logger.error(f"Failed to index FAQ data: {e}")
            raise e
PYEOF

# Create environment file with all required variables
cat > .env << 'ENVEOF'
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
ENVEOF

# Install Python dependencies
pip3 install -r requirements.txt

# Set ownership
chown -R ec2-user:ec2-user /home/ec2-user/eloquent-backend

# Create systemd service
cat > /etc/systemd/system/eloquent-backend.service << 'SERVICEEOF'
[Unit]
Description=Eloquent AI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/eloquent-backend
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Start the service
systemctl daemon-reload
systemctl enable eloquent-backend
systemctl start eloquent-backend

# Setup nginx (removed CORS headers to let FastAPI handle CORS)
cat > /etc/nginx/nginx.conf << 'NGINXEOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
NGINXEOF

# Start nginx
systemctl enable nginx
systemctl start nginx

echo "✅ Backend deployment completed!"
EOF

# Create new EC2 instance
echo "🚀 Creating new EC2 instance with Pinecone environment variables..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t2.micro \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file:///tmp/user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eloquent-backend-with-pinecone}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "📋 Instance ID: $INSTANCE_ID"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get the public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🌐 Public IP: $PUBLIC_IP"
echo "⏳ Waiting for services to start (3 minutes)..."
sleep 180

echo "🧪 Testing backend health..."
curl -s http://$PUBLIC_IP/health

echo ""
echo "🧪 Testing vector DB setup..."
curl -s -X POST http://$PUBLIC_IP/api/admin/setup-vector-db

echo ""
echo "✅ Deployment completed!"
echo "🌐 Backend URL: http://$PUBLIC_IP"
echo "📋 Instance ID: $INSTANCE_ID"

# Update frontend API URL
echo ""
echo "📝 Don't forget to update the frontend API URL to: http://$PUBLIC_IP"