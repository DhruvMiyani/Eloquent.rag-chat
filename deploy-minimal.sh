#!/bin/bash

set -e

# Configuration
UNIQUE_ID="20250918012018"
KEY_NAME="eloquent-keypair-$UNIQUE_ID"
SECURITY_GROUP_ID="sg-0f663567aa6995c1c"

echo "🚀 Deploying minimal backend to AWS..."

# Create minimal user data script
cat > /tmp/user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y python3 python3-pip nginx

# Create environment variables file
mkdir -p /home/ec2-user
cat > /home/ec2-user/.env << 'ENVEOF'
OPENAI_API_KEY="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"
PINECONE_API_KEY=pcsk_64LjaD_JwmDMGeVYu87sqbA6u6zt2HyPXRvfyp9sa3PNyFnFxnR5oipFqY6rUF3xw2nqiM
PINECONE_INDEX=ai-powered-chatbot-challenge
PINECONE_ENDPOINT=https://ai-powered-chatbot-challenge-5g2nluv.svc.aped-4627-b74a.pinecone.io
SECRET_KEY=eloquent-ai-secret-key-for-development-only
ENVEOF

# Install FastAPI
pip3 install fastapi uvicorn python-dotenv pinecone-client openai python-jose passlib

# Create a simple FastAPI app
cat > /home/ec2-user/app.py << 'APPEOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "pinecone_configured": bool(os.getenv("PINECONE_API_KEY"))}

@app.post("/api/admin/setup-vector-db")
async def setup_vector_db():
    try:
        import pinecone
        from pinecone import Pinecone

        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("ai-powered-chatbot-challenge")
        stats = index.describe_index_stats()

        return {"success": True, "message": f"Pinecone connected! Vectors: {stats['total_vector_count']}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
APPEOF

chown -R ec2-user:ec2-user /home/ec2-user

# Start the app
nohup python3 /home/ec2-user/app.py > /home/ec2-user/app.log 2>&1 &
nohup /usr/local/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --app-dir /home/ec2-user > /home/ec2-user/uvicorn.log 2>&1 &

# Simple nginx config
cat > /etc/nginx/nginx.conf << 'NGINXEOF'
events { worker_connections 1024; }
http {
    server {
        listen 80;
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
    }
}
NGINXEOF

systemctl enable nginx
systemctl start nginx
EOF

echo "🚀 Creating new EC2 instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t2.micro \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file:///tmp/user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eloquent-backend-minimal}]' \
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
echo "⏳ Waiting for services to start (2 minutes)..."
sleep 120

echo "🧪 Testing backend..."
curl -s http://$PUBLIC_IP/health

echo ""
echo "🧪 Testing Pinecone connection..."
curl -s -X POST http://$PUBLIC_IP/api/admin/setup-vector-db

echo ""
echo "✅ Deployment completed!"
echo "🌐 Backend URL: http://$PUBLIC_IP"