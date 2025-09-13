# Quick Start Guide

## 🚀 Deploy ResumeRepublic to AWS

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform installed
- Node.js 18+ installed
- Docker installed (for backend deployment)

### 1. Set Up Secrets
```bash
./scripts/setup-secrets.sh
```

### 2. Deploy Everything
```bash
./deploy.sh
```
Choose option 5 (Everything) from the menu.

### 3. Deploy Separately (Recommended)

#### Infrastructure First
```bash
./scripts/deploy-infrastructure.sh
```

#### Frontend (No Docker needed)
```bash
./scripts/deploy-frontend.sh
```

#### Backend (Requires Docker)
```bash
./scripts/deploy-backend.sh
```

## 📋 Script Overview

| Script | Purpose | Requirements | Output |
|--------|---------|--------------|--------|
| `./scripts/setup-secrets.sh` | Configure secrets | AWS CLI | `terraform.tfvars` + AWS Parameter Store |
| `./scripts/deploy-infrastructure.sh` | Deploy AWS infrastructure | Terraform | VPC, RDS, ECS, S3, CloudFront, ALB |
| `./scripts/deploy-frontend.sh` | Deploy React frontend | Node.js | S3 + CloudFront |
| `./scripts/deploy-backend.sh` | Deploy FastAPI backend | Docker | ECS Fargate |
| `./deploy.sh` | Interactive deployment | All above | Everything |

## 🔧 Development Workflow

### First Time Setup
1. `./scripts/setup-secrets.sh`
2. `./scripts/deploy-infrastructure.sh`
3. `./scripts/deploy-frontend.sh`
4. `./scripts/deploy-backend.sh`

### Frontend Updates
```bash
./scripts/deploy-frontend.sh
```

### Backend Updates
```bash
./scripts/deploy-backend.sh
```

### Infrastructure Changes
```bash
./scripts/deploy-infrastructure.sh
```

## 🌐 Access Your Application

After deployment, you'll get:
- **Frontend**: `https://your-cloudfront-domain.com`
- **Backend API**: `http://your-alb-domain.com`

## 🆘 Troubleshooting

### Common Issues
- **"Docker not running"**: Start Docker Desktop
- **"AWS not configured"**: Run `aws configure`
- **"Terraform not found"**: Install Terraform
- **"Node not found"**: Install Node.js 18+

### Quick Fixes
```bash
# Check AWS connection
aws sts get-caller-identity

# Check Docker
docker info

# Check Node.js
node --version

# Check Terraform
terraform --version
```

## 📚 More Information

- [Full Deployment Guide](DEPLOYMENT.md)
- [Secrets Management](SECRETS.md)
- [GitHub Actions Setup](.github/workflows/deploy.yml)
