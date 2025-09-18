# AWS Free Tier Deployment Guide

## 🎯 Free Tier Optimized Architecture

```
┌──────────────────────────────────────────────────┐
│            CloudFront (Free Tier)                │
│         (1TB/month transfer free)                │
└────────┬──────────────────────────┬──────────────┘
         │                          │
    ┌────▼────┐              ┌─────▼─────┐
    │   S3    │              │    EC2    │
    │(Frontend)│             │  t2.micro │
    │  FREE   │              │   (FREE)  │
    └─────────┘              └─────┬─────┘
                                   │
                            ┌──────▼──────┐
                            │   SQLite    │
                            │ (Local File) │
                            └─────────────┘
```

## 📋 Step-by-Step Deployment Guide

### Prerequisites
```bash
# Install AWS CLI
brew install awscli  # Mac
# or
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# Configure AWS CLI
aws configure
# Enter your Access Key ID, Secret Access Key, Region (us-east-1)
```

### Step 1: Deploy Frontend to S3 + CloudFront

```bash
# 1. Build the frontend
cd eloquent-ai-frontend
npm run build

# 2. Create S3 bucket
aws s3 mb s3://eloquent-ai-frontend-[your-unique-id]

# 3. Configure bucket for static hosting
aws s3 website s3://eloquent-ai-frontend-[your-unique-id] \
  --index-document index.html \
  --error-document error.html

# 4. Create bucket policy file
cat > bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::eloquent-ai-frontend-[your-unique-id]/*"
        }
    ]
}
EOF

# 5. Apply bucket policy
aws s3api put-bucket-policy \
  --bucket eloquent-ai-frontend-[your-unique-id] \
  --policy file://bucket-policy.json

# 6. Upload frontend files
aws s3 sync out/ s3://eloquent-ai-frontend-[your-unique-id]/ --delete

# 7. Create CloudFront distribution (Free tier: 1TB/month)
aws cloudfront create-distribution \
  --origin-domain-name eloquent-ai-frontend-[your-unique-id].s3-website-us-east-1.amazonaws.com \
  --default-root-object index.html
```

### Step 2: Deploy Backend to EC2 (t2.micro - Free Tier)

```bash
# 1. Create EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55731490381 \
  --instance-type t2.micro \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxx \
  --subnet-id subnet-xxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eloquent-backend}]'

# 2. Connect to EC2
ssh -i your-key.pem ec2-user@your-ec2-public-ip

# 3. Install dependencies on EC2
sudo yum update -y
sudo yum install git python3 python3-pip nginx -y
sudo pip3 install virtualenv

# 4. Clone and setup application
git clone https://github.com/yourusername/your-repo.git
cd your-repo/eloquent-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 5. Create systemd service
sudo tee /etc/systemd/system/eloquent.service << 'EOF'
[Unit]
Description=Eloquent AI Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/your-repo/eloquent-backend
Environment="PATH=/home/ec2-user/your-repo/eloquent-backend/venv/bin"
ExecStart=/home/ec2-user/your-repo/eloquent-backend/venv/bin/gunicorn main:app -w 2 -b 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
EOF

# 6. Configure Nginx
sudo tee /etc/nginx/conf.d/eloquent.conf << 'EOF'
server {
    listen 80;
    server_name your-ec2-public-ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# 7. Start services
sudo systemctl start eloquent
sudo systemctl enable eloquent
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 3: Setup Security Group

```bash
# Create security group
aws ec2 create-security-group \
  --group-name eloquent-sg \
  --description "Security group for Eloquent AI"

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-name eloquent-sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-name eloquent-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH (restrict to your IP)
aws ec2 authorize-security-group-ingress \
  --group-name eloquent-sg \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32
```

## 💰 Free Tier Resources Used

| Service | Free Tier Limit | Your Usage |
|---------|----------------|------------|
| EC2 t2.micro | 750 hrs/month | 24/7 = 720 hrs ✅ |
| S3 Storage | 5 GB | ~50 MB ✅ |
| S3 Requests | 20,000 GET | Varies ✅ |
| CloudFront | 1 TB transfer | Likely <100 GB ✅ |
| CloudFront | 2M requests | Likely <500K ✅ |

## 🔧 Environment Variables Setup

```bash
# On EC2, create .env file
cd /home/ec2-user/your-repo/eloquent-backend
cat > .env << 'EOF'
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_ENDPOINT=your_endpoint_here
DATABASE_URL=sqlite:///./chat_database.db
SECRET_KEY=$(openssl rand -hex 32)
FRONTEND_URL=https://your-cloudfront-url.cloudfront.net
EOF
```

## 📊 Monitoring (Free Tier)

```bash
# CloudWatch Monitoring (Basic metrics free)
aws cloudwatch put-metric-alarm \
  --alarm-name cpu-high \
  --alarm-description "Alarm when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --evaluation-periods 2
```

## 🚨 Important Free Tier Limits

### Stay Within Free Tier:
1. **EC2**: Max 750 hours/month (one t2.micro running 24/7)
2. **S3**: 5GB storage, 20,000 GET requests
3. **CloudFront**: 1TB data transfer out
4. **RDS**: 750 hours db.t2.micro (optional, not used here)

### Cost Saving Tips:
1. Use SQLite instead of RDS (saves $15/month)
2. Stop EC2 when not in use
3. Use CloudWatch alarms to monitor usage
4. Set up billing alerts

## 🔄 Alternative: Elastic Beanstalk (Also Free Tier)

```bash
# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk
cd eloquent-backend
eb init -p python-3.9 eloquent-ai-app

# Create environment (uses t2.micro free tier)
eb create eloquent-env --single --instance-type t2.micro

# Deploy
eb deploy

# Open application
eb open
```

## 🛠️ Maintenance Commands

```bash
# View logs
ssh -i your-key.pem ec2-user@your-ec2-ip
sudo journalctl -u eloquent -f

# Restart backend
sudo systemctl restart eloquent

# Update code
cd /home/ec2-user/your-repo
git pull
source eloquent-backend/venv/bin/activate
pip install -r eloquent-backend/requirements.txt
sudo systemctl restart eloquent

# Check disk space
df -h

# Monitor memory
free -m

# Check application status
curl http://localhost:8000/health
```

## ⚠️ Free Tier Expiration

After 12 months, you'll need to:
1. Migrate to t3.micro (slightly cheaper than t2)
2. Or use AWS Lambda (pay-per-request)
3. Or move to other providers (Heroku, Railway, Render)

## 🎯 Next Steps

1. **Get Domain Name** (Optional)
   - Use Route 53 ($12/year for .com)
   - Or use free subdomain services

2. **SSL Certificate**
   - Use AWS Certificate Manager (free)
   - Or Let's Encrypt on EC2

3. **Backup Strategy**
   - S3 for database backups (within 5GB free)
   - GitHub for code

4. **Monitoring**
   - Set up billing alerts immediately!
   - Use CloudWatch free tier metrics

## 📱 Testing Your Deployment

```bash
# Test backend health
curl http://your-ec2-public-ip/health

# Test frontend
open https://your-cloudfront-url.cloudfront.net

# Test API from frontend
# Update frontend's API URL to point to EC2
```

## 🆘 Troubleshooting

### If backend doesn't start:
```bash
# Check logs
sudo journalctl -u eloquent -n 100

# Check port
sudo netstat -tulpn | grep 8000

# Test locally
curl http://localhost:8000/health
```

### If frontend doesn't load:
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket your-bucket

# Check CloudFront status
aws cloudfront get-distribution --id your-distribution-id
```

---

## 💡 Pro Tips

1. **Use Elastic IP** (free while attached to running instance)
2. **Enable CloudWatch Logs** (free tier: 5GB)
3. **Use Parameter Store** for secrets (free up to 10,000 parameters)
4. **Set up SNS alerts** (1,000 emails free/month)
5. **Use AWS Free Tier Calculator** to track usage

## 🎉 Congratulations!

You now have a production-ready deployment on AWS Free Tier!

Total Monthly Cost: **$0** (within free tier limits)
After Free Tier: ~$15-20/month