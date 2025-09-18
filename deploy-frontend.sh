#!/bin/bash
set -e

echo "🚀 Deploying Frontend to S3"

# Check if deployment info exists
if [ ! -f "deployment-info.txt" ]; then
    echo "❌ deployment-info.txt not found. Run ./deploy-to-aws.sh first!"
    exit 1
fi

# Extract S3 bucket name from deployment info
S3_BUCKET=$(grep "Bucket Name:" deployment-info.txt | cut -d' ' -f3)
EC2_IP=$(grep "Public IP:" deployment-info.txt | cut -d' ' -f3)

echo "Using S3 bucket: ${S3_BUCKET}"
echo "Using EC2 IP: ${EC2_IP}"

# Build frontend with correct API URL
echo "🏗️  Building frontend..."
cd eloquent-ai-frontend

# Update the API URL in the environment
export NEXT_PUBLIC_API_URL="http://${EC2_IP}"

# Install dependencies and build
npm ci
npm run build

# Deploy to S3
echo "📦 Uploading to S3..."
aws s3 sync out/ s3://${S3_BUCKET}/ --delete

echo "✅ Frontend deployed successfully!"
echo ""
echo "🌐 Your application is now live:"
echo "Frontend: http://${S3_BUCKET}.s3-website-us-east-1.amazonaws.com"
echo "Backend:  http://${EC2_IP}"
echo ""
echo "🧪 Test your application:"
echo "1. Visit the frontend URL"
echo "2. Try asking: 'What documents do I need to open an account?'"
echo "3. Check if RAG is working by looking for contextual responses"