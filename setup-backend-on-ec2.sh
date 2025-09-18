#!/bin/bash
set -e

echo "🚀 Setting up Eloquent AI Backend on EC2"

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install dependencies
echo "🔧 Installing dependencies..."
sudo yum install git python3 python3-pip nginx -y
sudo pip3 install virtualenv

# Clone repository (replace with your actual repo URL)
echo "📥 Cloning repository..."
git clone https://github.com/your-username/your-repo.git eloquent-ai
cd eloquent-ai/eloquent-backend

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Create environment file
echo "⚙️ Creating production environment file..."
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///./chat_database.db

# OpenAI Configuration (you'll need to add these)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Pinecone Configuration (you'll need to add these)
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX=ai-powered-chatbot-challenge
PINECONE_ENDPOINT=your_pinecone_endpoint_here

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
ANONYMOUS_TOKEN_EXPIRE_DAYS=90

# CORS
FRONTEND_URL=http://your-s3-bucket.s3-website-us-east-1.amazonaws.com

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

echo "📝 IMPORTANT: Edit .env file with your actual API keys!"
echo "Run: nano .env"

# Create systemd service
echo "🎯 Creating systemd service..."
sudo tee /etc/systemd/system/eloquent.service << 'EOF'
[Unit]
Description=Eloquent AI Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/eloquent-ai/eloquent-backend
Environment="PATH=/home/ec2-user/eloquent-ai/eloquent-backend/venv/bin"
ExecStart=/home/ec2-user/eloquent-ai/eloquent-backend/venv/bin/gunicorn main:app -w 2 -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/conf.d/eloquent.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Handle preflight requests for CORS
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Root endpoint
    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Enable and start services
echo "🚦 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable eloquent
sudo systemctl enable nginx

# Test configuration
echo "🧪 Testing configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    sudo systemctl start nginx
    echo "✅ Nginx started successfully"
else
    echo "❌ Nginx configuration error"
    exit 1
fi

echo ""
echo "🎉 Backend setup complete!"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Edit .env file with your actual API keys:"
echo "   nano .env"
echo ""
echo "2. Start the backend service:"
echo "   sudo systemctl start eloquent"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status eloquent"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u eloquent -f"
echo ""
echo "5. Test the API:"
echo "   curl http://localhost/health"
echo ""
echo "📊 Monitor your application:"
echo "   - Logs: sudo journalctl -u eloquent -f"
echo "   - Status: sudo systemctl status eloquent"
echo "   - Restart: sudo systemctl restart eloquent"