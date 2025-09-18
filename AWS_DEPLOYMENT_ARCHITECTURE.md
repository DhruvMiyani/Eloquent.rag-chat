# AWS Deployment Architecture

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront (CDN)                         │
│                     (Global Content Delivery)                    │
└─────────┬───────────────────────────────┬───────────────────────┘
          │                               │
          ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│    S3 Bucket     │            │  ALB (Load       │
│  (Frontend React)│            │   Balancer)      │
└──────────────────┘            └────────┬─────────┘
                                         │
                               ┌─────────┴─────────┐
                               │                   │
                         ┌─────▼─────┐      ┌─────▼─────┐
                         │   ECS     │      │   ECS     │
                         │ Container │      │ Container │
                         │ (FastAPI) │      │ (FastAPI) │
                         └─────┬─────┘      └─────┬─────┘
                               │                   │
                ┌──────────────┴───────────────────┴──────────────┐
                │                                                  │
         ┌──────▼──────┐  ┌──────────────┐  ┌──────────────────┐
         │  RDS Aurora │  │   Pinecone   │  │  Secrets Manager │
         │ (PostgreSQL)│  │  (External)  │  │   (API Keys)     │
         └─────────────┘  └──────────────┘  └──────────────────┘
```

## 📦 Service Components

### 1. Frontend Deployment (S3 + CloudFront)
```yaml
Service: S3 + CloudFront
Purpose: Host React/Next.js frontend
Configuration:
  - S3 bucket with static website hosting
  - CloudFront distribution for global CDN
  - Route 53 for DNS management
  - ACM certificate for HTTPS
Benefits:
  - Low latency globally
  - High availability (99.99%)
  - Cost-effective for static assets
  - Automatic scaling
```

### 2. Backend Deployment (ECS Fargate)
```yaml
Service: ECS Fargate
Purpose: Host FastAPI backend
Configuration:
  - Containerized application
  - Auto-scaling based on CPU/memory
  - Application Load Balancer (ALB)
  - Target groups for health checks
Benefits:
  - Serverless container management
  - Automatic scaling
  - Pay-per-use pricing
  - Built-in monitoring
```

### 3. Database (RDS Aurora Serverless v2)
```yaml
Service: RDS Aurora PostgreSQL Serverless v2
Purpose: Primary application database
Configuration:
  - Auto-scaling capacity (0.5 - 1 ACU minimum)
  - Multi-AZ deployment for HA
  - Automated backups (7-day retention)
  - Encryption at rest
Benefits:
  - Scales automatically with load
  - MySQL/PostgreSQL compatible
  - High availability
  - Managed service
```

### 4. Vector Database (Pinecone - External)
```yaml
Service: Pinecone (SaaS)
Purpose: Vector similarity search for RAG
Configuration:
  - P1.x1 pod type
  - 1536 dimensions
  - ~100k vectors capacity
  - us-east-1 region
Benefits:
  - Managed vector search
  - Sub-second query times
  - No infrastructure management
```

## 🔐 Security Architecture

### Network Security
```yaml
VPC Configuration:
  - Private subnets for ECS tasks
  - Public subnets for ALB
  - NAT Gateway for outbound internet
  - Security groups with least privilege

WAF Rules:
  - SQL injection protection
  - XSS protection
  - Rate limiting (1000 req/min per IP)
  - Geo-blocking (if required)
```

### Secrets Management
```yaml
AWS Secrets Manager:
  - OpenAI API keys
  - Pinecone API keys
  - Database credentials
  - JWT secrets

IAM Roles:
  - ECS task execution role
  - ECS task role with specific permissions
  - S3 bucket policies
  - CloudFront OAI
```

## 🚀 CI/CD Pipeline

```yaml
GitHub Actions Workflow:
  Frontend:
    - Build React app
    - Run tests
    - Upload to S3
    - Invalidate CloudFront

  Backend:
    - Build Docker image
    - Push to ECR
    - Update ECS task definition
    - Deploy new revision

Infrastructure:
  - Terraform for IaC
  - Separate environments (dev/staging/prod)
  - Blue-green deployments
```

## 📊 Monitoring & Observability

```yaml
CloudWatch:
  - Application logs
  - Custom metrics
  - Alarms for critical events

X-Ray:
  - Distributed tracing
  - Performance bottlenecks
  - Service map

CloudWatch Dashboards:
  - Real-time metrics
  - API response times
  - Error rates
  - Resource utilization
```

## 💰 Cost Optimization

### Estimated Monthly Costs (Production)
```yaml
CloudFront + S3: ~$50
  - 1TB bandwidth
  - 10M requests

ECS Fargate: ~$150
  - 2 tasks (1 vCPU, 2GB RAM each)
  - Auto-scaling 2-10 tasks

RDS Aurora Serverless v2: ~$100
  - 0.5-2 ACUs
  - 20GB storage

Application Load Balancer: ~$25

Secrets Manager: ~$5

Total: ~$330/month
```

### Cost Optimization Strategies
1. **Reserved Capacity**: 1-year commitment for 30% savings
2. **Spot Instances**: For non-critical workloads
3. **S3 Lifecycle Policies**: Archive old data
4. **CloudWatch Log Retention**: 7 days for non-critical logs
5. **Auto-scaling**: Scale down during off-peak hours

## 🔄 Disaster Recovery

### RTO & RPO Targets
- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 15 minutes

### Backup Strategy
```yaml
Database:
  - Automated backups: Daily
  - Manual snapshots: Before major releases
  - Cross-region replication: For DR

Application:
  - Docker images in ECR
  - Infrastructure as Code in Git
  - Configuration in Secrets Manager

Data:
  - S3 versioning enabled
  - Cross-region replication for critical data
```

## 📈 Scaling Strategy

### Horizontal Scaling
```yaml
Frontend:
  - CloudFront: Automatic global scaling
  - S3: Unlimited storage

Backend:
  - ECS Auto-scaling: 2-10 tasks
  - Target tracking: 70% CPU utilization
  - Predictive scaling: Based on patterns

Database:
  - Aurora Serverless: 0.5-16 ACUs
  - Read replicas for read-heavy workloads
```

### Vertical Scaling
```yaml
When to scale up:
  - Consistent high CPU (>80%)
  - Memory pressure
  - Complex queries

Options:
  - Increase task CPU/memory
  - Larger Aurora capacity units
  - Enhanced monitoring
```

## 🛠️ DevOps Best Practices

### Infrastructure as Code
```yaml
Terraform Modules:
  - VPC and networking
  - ECS cluster and services
  - RDS Aurora setup
  - S3 and CloudFront
  - IAM roles and policies

Version Control:
  - Git for all IaC
  - PR reviews for changes
  - Terraform state in S3
```

### Environment Management
```yaml
Environments:
  Development:
    - Single ECS task
    - Smaller RDS instance
    - No multi-AZ

  Staging:
    - Production-like setup
    - Reduced capacity
    - Same architecture

  Production:
    - Full HA setup
    - Auto-scaling enabled
    - Multi-AZ deployment
```

## 🔧 Deployment Commands

### Initial Setup
```bash
# Create AWS infrastructure
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars

# Deploy frontend
npm run build
aws s3 sync build/ s3://eloquent-ai-frontend-prod/
aws cloudfront create-invalidation --distribution-id ABCD1234

# Deploy backend
docker build -t eloquent-backend .
aws ecr get-login-password | docker login --username AWS --password-stdin
docker tag eloquent-backend:latest $ECR_URI:latest
docker push $ECR_URI:latest
aws ecs update-service --cluster prod --service eloquent-api --force-new-deployment
```

## 📋 Pre-Launch Checklist

### Security
- [ ] SSL certificates configured
- [ ] WAF rules enabled
- [ ] Secrets in Secrets Manager
- [ ] IAM roles with least privilege
- [ ] Security groups configured
- [ ] VPC endpoints for AWS services

### Monitoring
- [ ] CloudWatch alarms set
- [ ] Log aggregation configured
- [ ] X-Ray tracing enabled
- [ ] Custom metrics defined
- [ ] Dashboards created

### Performance
- [ ] CDN caching rules
- [ ] Database indexes optimized
- [ ] Auto-scaling policies tested
- [ ] Load testing completed

### Backup & Recovery
- [ ] Automated backups enabled
- [ ] Disaster recovery tested
- [ ] Runbooks documented
- [ ] On-call rotation setup

## 🎯 Production Readiness

### Health Checks
```python
# Backend health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": check_db_connection(),
        "vector_db": check_pinecone_connection()
    }
```

### Graceful Shutdown
```python
# Handle SIGTERM for ECS
import signal
import sys

def signal_handler(sig, frame):
    logger.info("Gracefully shutting down...")
    # Clean up connections
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
```

---

## 📞 Support & Escalation

### Monitoring Alerts
- **P1 (Critical)**: Site down, data loss risk
- **P2 (High)**: Degraded performance, partial outage
- **P3 (Medium)**: Non-critical errors
- **P4 (Low)**: Minor issues

### Escalation Path
1. CloudWatch Alarm → SNS → PagerDuty
2. On-call engineer responds (15 min SLA)
3. Escalate to team lead if needed
4. Post-mortem for P1/P2 incidents