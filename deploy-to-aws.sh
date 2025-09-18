#!/bin/bash
set -e

echo "🚀 Starting AWS Free Tier Deployment"

# Configuration
UNIQUE_ID=$(date +%Y%m%d%H%M%S)
S3_BUCKET="eloquent-ai-frontend-${UNIQUE_ID}"
KEY_NAME="eloquent-keypair-${UNIQUE_ID}"
SECURITY_GROUP_NAME="eloquent-sg-${UNIQUE_ID}"

echo "Using unique ID: ${UNIQUE_ID}"

# Step 1: Create EC2 Key Pair
echo "📑 Creating EC2 Key Pair..."
aws ec2 create-key-pair \
    --key-name ${KEY_NAME} \
    --query 'KeyMaterial' \
    --output text > ${KEY_NAME}.pem

chmod 400 ${KEY_NAME}.pem
echo "✅ Key pair created: ${KEY_NAME}.pem"

# Step 2: Create Security Group
echo "🔒 Creating Security Group..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name ${SECURITY_GROUP_NAME} \
    --description "Security group for Eloquent AI" \
    --query 'GroupId' \
    --output text)

echo "✅ Security Group created: ${SECURITY_GROUP_ID}"

# Step 3: Configure Security Group Rules
echo "🔧 Configuring Security Group Rules..."

# Allow HTTP
aws ec2 authorize-security-group-ingress \
    --group-id ${SECURITY_GROUP_ID} \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id ${SECURITY_GROUP_ID} \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow SSH (from your current IP)
YOUR_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
    --group-id ${SECURITY_GROUP_ID} \
    --protocol tcp \
    --port 22 \
    --cidr ${YOUR_IP}/32

echo "✅ Security Group configured (SSH access from ${YOUR_IP})"

# Step 4: Launch EC2 Instance
echo "🖥️  Launching EC2 Instance (t2.micro)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c474afa8921e5b99 \
    --instance-type t2.micro \
    --key-name ${KEY_NAME} \
    --security-group-ids ${SECURITY_GROUP_ID} \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eloquent-backend}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ EC2 Instance launched: ${INSTANCE_ID}"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids ${INSTANCE_ID}

# Get instance public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids ${INSTANCE_ID} \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance is running at: ${PUBLIC_IP}"

# Step 5: Create S3 Bucket
echo "🪣 Creating S3 Bucket..."
aws s3 mb s3://${S3_BUCKET}
echo "✅ S3 Bucket created: ${S3_BUCKET}"

# Step 6: Configure S3 for static hosting
echo "🌐 Configuring S3 for static hosting..."
aws s3 website s3://${S3_BUCKET} \
    --index-document index.html \
    --error-document error.html

# Create bucket policy
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${S3_BUCKET} \
    --policy file://bucket-policy.json

echo "✅ S3 static hosting configured"

# Save deployment info
cat > deployment-info.txt << EOF
🎉 Deployment Information

EC2 Instance:
- Instance ID: ${INSTANCE_ID}
- Public IP: ${PUBLIC_IP}
- Key Pair: ${KEY_NAME}.pem
- Security Group: ${SECURITY_GROUP_ID}

S3 Bucket:
- Bucket Name: ${S3_BUCKET}
- Website URL: http://${S3_BUCKET}.s3-website-us-east-1.amazonaws.com

Next Steps:
1. Connect to EC2: ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}
2. Deploy backend on EC2
3. Build and upload frontend to S3
4. Update frontend API URL to point to EC2

Estimated Monthly Cost: \$0 (within free tier limits)
EOF

echo "✅ Deployment complete! Check deployment-info.txt for details"
cat deployment-info.txt