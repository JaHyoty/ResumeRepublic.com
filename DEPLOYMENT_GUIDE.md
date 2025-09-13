# ResumeRepublic Deployment Guide

This guide provides step-by-step instructions for deploying the ResumeRepublic application to AWS using Terraform and ECS Fargate.

## Prerequisites

Before starting the deployment, ensure you have the following installed and configured:

### Required Tools
- **AWS CLI** (v2.0+) - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** (v1.0+) - [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- **Docker** - [Installation Guide](https://docs.docker.com/get-docker/)
- **Node.js** (v18+) - [Installation Guide](https://nodejs.org/)
- **jq** - JSON processor for shell scripts

### AWS Configuration
1. Configure AWS CLI with appropriate credentials:
   ```bash
   aws configure
   ```
2. Ensure your AWS account has the necessary permissions for:
   - ECS (Elastic Container Service)
   - ECR (Elastic Container Registry)
   - RDS (Relational Database Service)
   - S3 (Simple Storage Service)
   - CloudFront
   - Route53
   - Systems Manager Parameter Store
   - IAM (Identity and Access Management)

### Domain Setup (Optional)
If you want to use a custom domain:
1. Register a domain or use an existing one
2. Create a Route53 hosted zone for your domain
3. Update the domain configuration in the Terraform variables

## Deployment Steps

The deployment process consists of 4 independent steps that can be run separately:

### Step 1: Deploy Infrastructure to AWS with Terraform

This step creates all AWS resources including VPC, RDS database, ECS cluster, S3 bucket, CloudFront distribution, and IAM roles.

**Script:** `./scripts/deploy-infrastructure.sh`

**What it does:**
- Creates VPC with public and private subnets
- Sets up RDS PostgreSQL database
- Creates ECS cluster and task definitions
- Configures Application Load Balancer
- Sets up S3 bucket for frontend hosting
- Creates CloudFront distribution
- Configures IAM roles and policies
- Sets up Systems Manager Parameter Store for secrets

**Prerequisites:**
- AWS CLI configured
- Terraform installed
- Domain name (if using custom domain)

**Usage:**
```bash
# Deploy to production
./scripts/deploy-infrastructure.sh prod apply

# Deploy to development
./scripts/deploy-infrastructure.sh dev apply

# Plan deployment (dry run)
./scripts/deploy-infrastructure.sh prod plan
```

**Required Variables:**
- `project_name`: Name of your project
- `domain_name`: Your domain name
- `db_password`: Database password
- `secret_key`: Application secret key
- OAuth credentials (Google, GitHub)
- External service API keys

### Step 2: Deploy Backend to ECS Service using Fargate

This step builds the backend Docker image, pushes it to ECR, and deploys it to ECS Fargate.

**Script:** `./scripts/deploy-backend.sh`

**What it does:**
- Builds backend Docker image
- Pushes image to ECR
- Updates ECS service with new image
- Performs zero-downtime deployment
- Monitors deployment health

**Prerequisites:**
- Infrastructure deployed (Step 1)
- Docker running
- Backend code ready

**Usage:**
```bash
./scripts/deploy-backend.sh
```

**Features:**
- Blue-green deployment strategy
- Automatic health checks
- Rollback capability on failure
- Version tagging for images

### Step 3: Run Database Migration with One-time ECS Task

This step runs database migrations using Alembic in a one-time ECS task with automatic rollback on failure.

**Script:** `./scripts/run-database-migration.sh`

**What it does:**
- Builds backend image with migration tools
- Runs Alembic migrations in ECS task
- Automatically rolls back on failure
- Provides detailed migration logs
- Validates database connectivity

**Prerequisites:**
- Infrastructure deployed (Step 1)
- Backend code with Alembic migrations
- Database accessible from ECS

**Usage:**
```bash
# Run migrations
./scripts/run-database-migration.sh

# Rollback migrations
./scripts/rollback-database-migration.sh

# Run custom Alembic command
./scripts/run-alembic-command.sh "upgrade head"
```

**Features:**
- Automatic rollback on failure
- Database connectivity validation
- Detailed logging and error reporting
- Support for custom Alembic commands

### Step 4: Build and Deploy Frontend to S3 and CloudFront

This step builds the React frontend and deploys it to S3 with CloudFront distribution.

**Script:** `./scripts/deploy-frontend.sh`

**What it does:**
- Builds React application
- Configures API endpoints
- Uploads to S3 bucket
- Creates CloudFront invalidation
- Sets up custom domain (if configured)

**Prerequisites:**
- Infrastructure deployed (Step 1)
- Backend deployed (Step 2)
- Node.js and npm installed

**Usage:**
```bash
./scripts/deploy-frontend.sh
```

**Features:**
- Automatic API endpoint configuration
- CloudFront cache invalidation
- Custom domain support
- Environment-specific builds

## Configuration

### Environment Variables

The application uses environment variables for configuration. These are automatically set by the deployment scripts:

**Backend Environment Variables:**
- `ENVIRONMENT`: production/development
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Application secret key
- `ALLOWED_ORIGINS`: CORS allowed origins
- `ALLOWED_HOSTS`: Trusted hosts
- OAuth credentials (Google, GitHub)
- External service API keys

**Frontend Environment Variables:**
- `VITE_API_BASE_URL`: Backend API URL

### Terraform Variables

Key variables that need to be configured in `terraform.tfvars`:

```hcl
# Project Configuration
project_name = "resumerepublic"
domain_name  = "yourdomain.com"
api_domain_name = "api.yourdomain.com"

# Database Configuration
db_password = "your-secure-password"
db_instance_class = "db.t3.micro"

# Application Configuration
secret_key = "your-secret-key"

# OAuth Configuration
google_client_id     = "your-google-client-id"
google_client_secret = "your-google-client-secret"
github_client_id     = "your-github-client-id"
github_client_secret = "your-github-client-secret"

# External Services
openrouter_api_key = "your-openrouter-api-key"
```

## Monitoring and Troubleshooting

### Health Checks

**Backend Health Check:**
```bash
curl https://your-api-domain.com/health
```

**Frontend Health Check:**
```bash
curl https://your-domain.com
```

### Logs

**Backend Logs:**
```bash
aws logs tail /ecs/resumerepublic-backend --follow
```

**Migration Logs:**
```bash
aws logs tail /ecs/resumerepublic-migration --follow
```

### Common Issues

1. **Database Connection Issues:**
   - Check RDS security groups
   - Verify database credentials in Parameter Store
   - Ensure ECS tasks can reach RDS

2. **ECS Service Issues:**
   - Check task definition and container logs
   - Verify IAM roles and permissions
   - Check resource limits (CPU/Memory)

3. **Frontend Issues:**
   - Verify S3 bucket permissions
   - Check CloudFront distribution status
   - Ensure API endpoints are correct

4. **Migration Issues:**
   - Check database connectivity
   - Verify Alembic configuration
   - Review migration logs for errors

## Security Considerations

- All secrets are stored in AWS Systems Manager Parameter Store
- Database credentials are managed by AWS RDS
- IAM roles follow least privilege principle
- HTTPS is enforced for all external communications
- Database is in private subnets
- ECS tasks run in private subnets

## Cost Optimization

- Use appropriate instance sizes for your workload
- Enable auto-scaling for ECS services
- Use CloudFront for global content delivery
- Monitor and optimize database performance
- Set up billing alerts

## Backup and Recovery

- RDS automated backups are enabled
- Database snapshots can be created manually
- Infrastructure can be recreated using Terraform
- Application data should be backed up separately

## Scaling

- ECS services can be scaled horizontally
- RDS can be scaled vertically or with read replicas
- CloudFront provides global scaling
- Consider using Application Load Balancer for high availability

## Cleanup

To destroy the infrastructure:

```bash
./scripts/deploy-infrastructure.sh prod destroy
```

**Warning:** This will permanently delete all resources and data.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Check Terraform state for infrastructure issues
4. Verify all prerequisites are met

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/deploy-infrastructure.sh prod apply` | Deploy infrastructure |
| `./scripts/deploy-backend.sh` | Deploy backend |
| `./scripts/run-database-migration.sh` | Run migrations |
| `./scripts/deploy-frontend.sh` | Deploy frontend |
| `./scripts/rollback-database-migration.sh` | Rollback migrations |
| `./scripts/run-alembic-command.sh "current"` | Check migration status |
