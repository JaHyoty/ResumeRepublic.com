# AWS Deployment Guide for CareerPathPro

This guide explains how to deploy CareerPathPro to AWS using separate services architecture.

## 🏗️ Architecture

```
Internet
    ↓
CloudFront (CDN) → S3 (Frontend Static Files)
    ↓
Application Load Balancer
    ↓
ECS Fargate (Backend API)
    ↓
RDS PostgreSQL (Database)
```

## 📋 Prerequisites

1. **AWS CLI** installed and configured
2. **Terraform** installed
3. **Docker** installed
4. **Node.js** and **npm** installed
5. **AWS Account** with appropriate permissions

## 🔧 Setup

### 1. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 2. Set Environment Variables

```bash
export DB_PASSWORD="your-secure-database-password"
export SECRET_KEY="your-secret-key-for-jwt"
export AWS_ACCOUNT_ID="your-aws-account-id"
```

### 3. Create GitHub Secrets (for CI/CD)

In your GitHub repository, add these secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`
- `DB_PASSWORD`
- `SECRET_KEY`

## 🚀 Deployment

### Option 1: Manual Deployment

```bash
# Deploy everything
./deploy-aws.sh deploy

# Destroy infrastructure
./deploy-aws.sh destroy
```

### Option 2: CI/CD with GitHub Actions

1. Push code to `main` branch
2. GitHub Actions automatically:
   - Runs tests
   - Builds and pushes Docker image
   - Deploys infrastructure
   - Deploys frontend to S3
   - Updates ECS service

## 📊 Services

### Frontend (S3 + CloudFront)
- **Static Files**: S3 bucket
- **CDN**: CloudFront distribution
- **URL**: `https://your-cloudfront-domain.cloudfront.net`

### Backend (ECS Fargate)
- **Container**: ECS Fargate task
- **Load Balancer**: Application Load Balancer
- **URL**: `http://your-alb-domain.elb.amazonaws.com`

### Database (RDS)
- **Engine**: PostgreSQL 15.4
- **Instance**: db.t3.micro
- **Storage**: 20GB GP2 (auto-scaling to 100GB)

## 💰 Cost Estimation

### Monthly Costs (us-east-1):
- **RDS db.t3.micro**: ~$15
- **ECS Fargate (0.25 vCPU, 0.5GB)**: ~$8
- **Application Load Balancer**: ~$16
- **S3 + CloudFront**: ~$1-5
- **Total**: ~$40-45/month

### Cost Optimization:
- Use `db.t3.micro` for development
- Use `db.t3.small` for production
- Enable RDS automated backups
- Use CloudFront for global distribution

## 🔒 Security

### Network Security:
- VPC with public/private subnets
- Security groups with minimal access
- RDS in private subnets
- ECS in private subnets

### Data Security:
- RDS encryption at rest
- S3 bucket encryption
- CloudFront HTTPS only
- IAM roles with least privilege

## 📈 Monitoring

### CloudWatch Logs:
- ECS task logs: `/ecs/careerpathpro-backend`
- Application logs in CloudWatch

### Health Checks:
- ALB health check on `/health` endpoint
- ECS task health check
- RDS automated backups

## 🛠️ Management

### View Logs:
```bash
# ECS logs
aws logs tail /ecs/careerpathpro-backend --follow

# RDS logs
aws rds describe-db-log-files --db-instance-identifier careerpathpro-db
```

### Scale Services:
```bash
# Scale ECS service
aws ecs update-service \
  --cluster careerpathpro-cluster \
  --service careerpathpro-backend-service \
  --desired-count 2
```

### Update Application:
```bash
# Update backend
./deploy-aws.sh deploy

# Update only frontend
cd frontend && npm run build
aws s3 sync dist/ s3://your-bucket-name --delete
```

## 🔍 Troubleshooting

### Common Issues:

1. **ECS Task Failing**:
   - Check CloudWatch logs
   - Verify environment variables
   - Check security group rules

2. **Frontend Not Loading**:
   - Check S3 bucket permissions
   - Verify CloudFront distribution
   - Check CORS settings

3. **Database Connection Issues**:
   - Verify security group rules
   - Check database endpoint
   - Verify credentials

### Debug Commands:
```bash
# Check ECS service status
aws ecs describe-services --cluster careerpathpro-cluster --services careerpathpro-backend-service

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names careerpathpro-backend-tg --query 'TargetGroups[0].TargetGroupArn' --output text)

# Check RDS status
aws rds describe-db-instances --db-instance-identifier careerpathpro-db
```

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [GitHub Actions AWS](https://github.com/aws-actions)
