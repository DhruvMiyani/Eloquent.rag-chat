#!/bin/bash

set -e

# Configuration
UNIQUE_ID="20250918012018"
BUCKET_NAME="eloquent-ai-frontend-$UNIQUE_ID"

# Get the new backend IP (you'll need to provide this after running deploy-backend-with-env.sh)
if [ -z "$1" ]; then
    echo "Usage: $0 <NEW_BACKEND_IP>"
    echo "Example: $0 3.89.59.19"
    exit 1
fi

NEW_BACKEND_IP="$1"
echo "🚀 Updating frontend to use new backend IP: $NEW_BACKEND_IP"

# Update the environment variable for the build
cd eloquent-ai-frontend
export NEXT_PUBLIC_API_URL="http://$NEW_BACKEND_IP"

echo "🔨 Building frontend with new API URL: $NEXT_PUBLIC_API_URL"

# Build the frontend
npm run build

# Deploy to S3
echo "📦 Deploying updated frontend to S3..."
aws s3 sync out/ s3://$BUCKET_NAME --delete

echo "✅ Frontend updated successfully!"
echo "🌐 Frontend URL: http://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
echo "🔗 New Backend URL: http://$NEW_BACKEND_IP"