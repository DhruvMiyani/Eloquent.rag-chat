#!/bin/bash

set -e

# Configuration
UNIQUE_ID="20250918012018"
KEY_NAME="eloquent-keypair-$UNIQUE_ID"
SECURITY_GROUP_ID="sg-0f663567aa6995c1c"

# Source environment variables from local .env file
if [ -f "eloquent-backend/.env" ]; then
    echo "📄 Loading environment variables from eloquent-backend/.env"
    source eloquent-backend/.env
elif [ -f "api/.env" ]; then
    echo "📄 Loading environment variables from api/.env"
    source api/.env
else
    echo "❌ Error: No .env file found. Please create eloquent-backend/.env or api/.env with required environment variables."
    exit 1
fi

# Validate required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not found in .env file"
    exit 1
fi

if [ -z "$PINECONE_API_KEY" ]; then
    echo "❌ Error: PINECONE_API_KEY not found in .env file"
    exit 1
fi

echo "🚀 Deploying backend to AWS with environment variables..."
echo "🔑 Using OpenAI API Key ending with: ${OPENAI_API_KEY: -10}"

# Create user data script with environment variables
cat > /tmp/user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git nginx

# Clone the repository
cd /home/ec2-user
git clone https://github.com/yourusername/eloquent-backend.git eloquent-backend || echo "Repository already exists"
cd eloquent-backend

# Create environment file with variables from local .env
cat > .env << ENVEOF
# OpenAI Configuration
OPENAI_API_KEY="$OPENAI_API_KEY"
OPENAI_MODEL=\${OPENAI_MODEL:-gpt-4o-mini}
EMBEDDING_MODEL=\${EMBEDDING_MODEL:-text-embedding-3-small}

# Pinecone Configuration
PINECONE_API_KEY=$PINECONE_API_KEY
PINECONE_INDEX=\${PINECONE_INDEX:-ai-powered-chatbot-challenge}
PINECONE_ENDPOINT=\${PINECONE_ENDPOINT:-https://ai-powered-chatbot-challenge-5g2nluv.svc.aped-4627-b74a.pinecone.io}

# Database Configuration
DATABASE_URL=sqlite:///./chat_database.db
USE_DYNAMODB=false

# AWS Configuration (for DynamoDB)
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=chatbot

# Security
SECRET_KEY=\${SECRET_KEY:-eloquent-ai-secret-key-for-development-only-change-in-production}
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

# Configure nginx
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

            # Handle OPTIONS requests (CORS preflight)
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' 'http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com' always;
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
                add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept, Authorization' always;
                add_header 'Access-Control-Allow-Credentials' 'true' always;
                add_header 'Content-Length' 0;
                add_header 'Content-Type' text/plain;
                return 204;
            }

            # CORS headers for actual requests
            add_header 'Access-Control-Allow-Origin' 'http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept, Authorization' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
        }
    }
}
NGINXEOF

# Start nginx
systemctl enable nginx
systemctl start nginx

echo "✅ Backend deployment completed!"
EOF

# Wait for instance to be terminated
echo "⏳ Waiting for previous instance to terminate..."
aws ec2 wait instance-terminated --instance-ids i-030e78a9105ee0fa6

# Create new EC2 instance with environment variables
echo "🚀 Creating new EC2 instance with environment variables..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t2.micro \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file:///tmp/user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eloquent-backend-with-env}]' \
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

# Wait a bit for the services to start
echo "⏳ Waiting for services to start (3 minutes)..."
sleep 180

# Test the backend
echo "🧪 Testing backend..."
curl -s http://$PUBLIC_IP/health || echo "Backend not ready yet, please wait a few more minutes"

echo "✅ Deployment completed!"
echo "🌐 Backend URL: http://$PUBLIC_IP"
echo "📋 Instance ID: $INSTANCE_ID"