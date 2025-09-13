# ResumeRepublic Deployment Quick Reference

## Prerequisites

Before deploying, ensure you have:
- AWS CLI configured (`aws configure`)
- Terraform installed (v1.0+)
- Docker running
- Node.js installed (v18+)
- jq installed

## Quick Start

1. **Validate deployment readiness:**
   ```bash
   ./scripts/validate-deployment.sh --check-all --fix
   ```

2. **Deploy infrastructure:**
   ```bash
   ./scripts/deploy-infrastructure.sh prod apply
   ```

3. **Deploy backend:**
   ```bash
   ./scripts/deploy-backend.sh
   ```

4. **Run database migrations:**
   ```bash
   ./scripts/run-database-migration.sh
   ```

5. **Deploy frontend:**
   ```bash
   ./scripts/deploy-frontend.sh
   ```

## Individual Scripts

### Infrastructure Deployment
```bash
# Deploy to production
./scripts/deploy-infrastructure.sh prod apply

# Deploy to development
./scripts/deploy-infrastructure.sh dev apply

# Plan deployment (dry run)
./scripts/deploy-infrastructure.sh prod plan

# Destroy infrastructure
./scripts/deploy-infrastructure.sh prod destroy
```

### Backend Deployment
```bash
# Deploy to detected environment
./scripts/deploy-backend.sh

# Deploy to specific environment
./scripts/deploy-backend.sh --environment prod

# Force deployment (skip change detection)
./scripts/deploy-backend.sh --force

# Deploy without building (use existing image)
./scripts/deploy-backend.sh --no-build
```

### Database Migration
```bash
# Run migrations to latest
./scripts/run-database-migration.sh

# Run migrations to specific target
./scripts/run-database-migration.sh --target head-1

# Dry run (show what would be migrated)
./scripts/run-database-migration.sh --dry-run

# Run on specific environment
./scripts/run-database-migration.sh --environment prod
```

### Database Rollback
```bash
# Rollback one migration
./scripts/rollback-database-migration.sh

# Rollback to specific target
./scripts/rollback-database-migration.sh --target base

# Dry run rollback
./scripts/rollback-database-migration.sh --dry-run

# Force rollback (skip confirmation)
./scripts/rollback-database-migration.sh --force
```

### Frontend Deployment
```bash
# Deploy to detected environment
./scripts/deploy-frontend.sh

# Deploy to specific environment
./scripts/deploy-frontend.sh --environment prod

# Build only (don't upload)
./scripts/deploy-frontend.sh --no-upload

# Deploy without building
./scripts/deploy-frontend.sh --no-build

# Skip CloudFront invalidation
./scripts/deploy-frontend.sh --no-invalidation
```

### Validation
```bash
# Validate detected environment
./scripts/validate-deployment.sh

# Validate specific environment
./scripts/validate-deployment.sh --environment prod

# Validate all environments
./scripts/validate-deployment.sh --check-all

# Attempt to fix common issues
./scripts/validate-deployment.sh --fix
```

## Common Commands

### Check Deployment Status
```bash
# Check ECS service status
aws ecs describe-services --cluster resumerepublic-cluster --services resumerepublic-backend-service

# Check CloudFront distribution
aws cloudfront list-distributions

# Check S3 bucket contents
aws s3 ls s3://your-bucket-name
```

### View Logs
```bash
# Backend logs
aws logs tail /ecs/resumerepublic-backend --follow

# Migration logs
aws logs tail /ecs/resumerepublic-migration --follow
```

### Test Deployment
```bash
# Test backend health
curl https://your-api-domain.com/health

# Test frontend
curl https://your-domain.com
```

## Troubleshooting

### Common Issues

1. **AWS CLI not configured:**
   ```bash
   aws configure
   ```

2. **Docker not running:**
   ```bash
   # Start Docker service
   sudo systemctl start docker
   ```

3. **Terraform not initialized:**
   ```bash
   cd infrastructure/terraform/environments/production
   terraform init
   ```

4. **Missing dependencies:**
   ```bash
   # Install jq
   sudo apt-get install jq  # Ubuntu/Debian
   brew install jq          # macOS
   ```

5. **Frontend build fails:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

### Environment Variables

Required in `terraform.tfvars`:
```hcl
project_name = "resumerepublic"
domain_name  = "yourdomain.com"
db_password  = "your-secure-password"
secret_key   = "your-secret-key"
```

Optional:
```hcl
google_client_id     = "your-google-client-id"
google_client_secret = "your-google-client-secret"
github_client_id     = "your-github-client-id"
github_client_secret = "your-github-client-secret"
openrouter_api_key   = "your-openrouter-api-key"
```

## Emergency Procedures

### Rollback Backend
```bash
# Rollback to previous ECS task definition
aws ecs update-service --cluster resumerepublic-cluster --service resumerepublic-backend-service --task-definition previous-task-definition
```

### Rollback Database
```bash
# Rollback one migration
./scripts/rollback-database-migration.sh

# Rollback to specific migration
./scripts/rollback-database-migration.sh --target abc123
```

### Destroy Everything
```bash
# Destroy infrastructure (WARNING: This deletes everything!)
./scripts/deploy-infrastructure.sh prod destroy
```

## Monitoring

### Health Checks
- Backend: `https://your-api-domain.com/health`
- Frontend: `https://your-domain.com`

### CloudWatch Logs
- Backend: `/ecs/resumerepublic-backend`
- Migration: `/ecs/resumerepublic-migration`

### CloudWatch Metrics
- ECS: CPU, Memory, Task Count
- RDS: CPU, Memory, Connections
- ALB: Request Count, Response Time
- CloudFront: Request Count, Error Rate

## Support

For issues:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Check Terraform state for infrastructure issues
4. Verify all prerequisites are met
5. Run validation script: `./scripts/validate-deployment.sh --check-all`
