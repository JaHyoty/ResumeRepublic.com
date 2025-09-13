# ResumeRepublic Terraform Infrastructure

This directory contains the Terraform configuration for the ResumeRepublic application infrastructure, organized in a modular structure for better maintainability and reusability.

## 🏗️ Architecture Overview

The infrastructure is divided into logical modules and environment-specific configurations:

```
infrastructure/terraform/
├── modules/                    # Reusable Terraform modules
│   ├── networking/            # VPC, subnets, security groups, ALB
│   ├── database/              # RDS PostgreSQL instance
│   ├── compute/               # ECS cluster, tasks, services
│   ├── storage/               # S3, CloudFront, ECR
│   ├── iam/                   # IAM roles, policies, SSM parameters
│   └── dns/                   # Route53, ACM certificates
├── environments/              # Environment-specific configurations
│   ├── development/           # Development environment
│   └── production/            # Production environment
├── main.tf                    # Legacy main file (backup)
├── main.tf.backup            # Original monolithic configuration
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured
- AWS account with appropriate permissions

### 1. Choose Your Environment

#### Development Environment
```bash
cd infrastructure/terraform/environments/development
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

#### Production Environment
```bash
cd infrastructure/terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Deploy Infrastructure

Use the provided deployment script:

```bash
# Plan deployment
./scripts/deploy-infrastructure-modular.sh dev plan
./scripts/deploy-infrastructure-modular.sh prod plan

# Apply deployment
./scripts/deploy-infrastructure-modular.sh dev apply
./scripts/deploy-infrastructure-modular.sh prod apply
```

Or use Terraform directly:

```bash
cd infrastructure/terraform/environments/development
terraform init
terraform plan
terraform apply
```

## 📁 Module Details

### Networking Module (`modules/networking/`)

**Purpose**: Manages VPC, subnets, security groups, and load balancer networking.

**Resources**:
- VPC with public/private subnets
- Security groups for RDS, ECS, and ALB
- Application Load Balancer
- Target groups and listeners

**Key Outputs**:
- `vpc_id`: VPC identifier
- `private_subnets`: List of private subnet IDs
- `public_subnets`: List of public subnet IDs
- `alb_dns_name`: ALB DNS name
- Security group IDs for other modules

### Database Module (`modules/database/`)

**Purpose**: Manages RDS PostgreSQL database and related resources.

**Resources**:
- RDS PostgreSQL instance with AWS managed master user password
- DB subnet group
- AWS Secrets Manager secret for database credentials
- Enhanced monitoring (optional)

**Key Outputs**:
- `db_endpoint`: Database endpoint
- `db_name`: Database name
- `db_username`: Database username
- `db_credentials_secret_arn`: ARN of the database credentials secret
- `db_master_user_secret_arn`: ARN of the RDS master user secret

### Compute Module (`modules/compute/`)

**Purpose**: Manages ECS cluster, task definitions, and services.

**Resources**:
- ECS cluster with Fargate
- Task definition for backend application
- ECS service
- CloudWatch log groups

**Key Outputs**:
- `ecs_cluster_name`: ECS cluster name
- `ecs_cluster_arn`: ECS cluster ARN
- `ecs_service_name`: ECS service name

### Storage Module (`modules/storage/`)

**Purpose**: Manages S3 buckets, CloudFront distributions, and ECR repositories.

**Resources**:
- S3 bucket for frontend static files
- CloudFront distribution with OAI
- ECR repository for container images
- ECR lifecycle policies

**Key Outputs**:
- `s3_bucket_name`: S3 bucket name
- `cloudfront_domain_name`: CloudFront domain
- `ecr_repository_url`: ECR repository URL

### IAM Module (`modules/iam/`)

**Purpose**: Manages IAM roles, policies, and SSM parameters for secrets.

**Resources**:
- ECS execution and task roles
- EC2 SSM role (for dev machines)
- SSM parameters for application secrets
- IAM policies for service permissions (including Secrets Manager access)

**Key Outputs**:
- `ecs_execution_role_arn`: ECS execution role ARN
- `ecs_task_role_arn`: ECS task role ARN
- SSM parameter ARNs for secrets

### DNS Module (`modules/dns/`)

**Purpose**: Manages Route53 records and ACM certificates.

**Resources**:
- Route53 hosted zone (optional)
- ACM certificate for HTTPS
- DNS records for domain and subdomains
- Certificate validation

**Key Outputs**:
- `acm_certificate_arn`: ACM certificate ARN
- `route53_zone_id`: Route53 zone ID

## 🌍 Environment Configurations

### Development Environment

**Characteristics**:
- Smaller resource sizes (db.t3.micro, 256 CPU, 512 MB memory)
- Shorter backup retention (1 day)
- Skip final snapshot on destroy
- Optional domain (can use CloudFront domain)
- EC2 SSM role enabled for dev machines
- Debug mode enabled

**Configuration**:
- VPC CIDR: `10.1.0.0/16`
- Database: `resumerepublic_dev`
- Log retention: 3 days

### Production Environment

**Characteristics**:
- Production-ready resource sizes
- Full backup retention (7 days)
- Final snapshot on destroy
- Custom domain required
- Performance monitoring available
- Debug mode disabled

**Configuration**:
- VPC CIDR: `10.0.0.0/16`
- Database: `resumerepublic`
- Log retention: 7 days

## 🔧 Configuration

### Required Variables

All environments require these variables in `terraform.tfvars`:

```hcl
# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "resumerepublic"
domain_name  = "your-domain.com"  # Optional for dev

# Database Configuration (with automatic password rotation)
db_manage_master_user_password = true  # Use AWS managed password
db_password_rotation_days = 30  # Rotate every 30 days
# db_password = ""  # Ignored when manage_master_user_password is true

# Application Secrets
secret_key = "your-secret-key"

# OAuth Configuration
google_client_id     = "your-google-client-id"
google_client_secret = "your-google-client-secret"
github_client_id     = "your-github-client-id"
github_client_secret = "your-github-client-secret"

# External Services
openrouter_api_key = "your-openrouter-api-key"
```

### 🔐 Password Management & Security

The infrastructure uses AWS Secrets Manager for secure password management with automatic rotation:

**Database Passwords**:
- **AWS Managed**: RDS master user password is managed by AWS with automatic rotation
- **Rotation**: Passwords rotate every 30 days (configurable)
- **Encryption**: Secrets are encrypted using AWS KMS
- **Access**: ECS tasks retrieve credentials from Secrets Manager at runtime

**Application Secrets**:
- **SSM Parameters**: OAuth credentials and API keys stored in SSM Parameter Store
- **Encryption**: All secrets are encrypted using AWS managed keys
- **IAM**: Fine-grained access control through IAM policies

**Security Benefits**:
- No hardcoded passwords in configuration files
- Automatic password rotation reduces security risks
- Centralized secret management
- Audit trail for secret access
- Encryption at rest and in transit

### Optional Variables

Many variables have sensible defaults. See the example files for all available options:
- `infrastructure/terraform/environments/development/terraform.tfvars.example`
- `infrastructure/terraform/environments/production/terraform.tfvars.example`

## 🚀 Deployment Workflow

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd career-manager

# Run migration script (if migrating from monolithic)
./scripts/migrate-to-modular.sh
```

### 2. Configure Environment

```bash
# Choose your environment
cd infrastructure/terraform/environments/development  # or production

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Deploy

```bash
# Using the deployment script (recommended)
./scripts/deploy-infrastructure-modular.sh dev plan
./scripts/deploy-infrastructure-modular.sh dev apply

# Or using Terraform directly
terraform init
terraform plan
terraform apply
```

### 4. Verify Deployment

Check the outputs after deployment:
- VPC ID
- RDS endpoint
- ECS cluster name
- CloudFront domain
- ECR repository URL

## 🔄 Migration from Monolithic Structure

If you're migrating from the old monolithic structure:

1. **Run the migration script**:
   ```bash
   ./scripts/migrate-to-modular.sh
   ```

2. **Review generated configurations**:
   - Check `environments/production/terraform.tfvars`
   - Check `environments/development/terraform.tfvars`

3. **Test in development first**:
   ```bash
   ./scripts/deploy-infrastructure-modular.sh dev plan
   ```

4. **Apply changes**:
   ```bash
   ./scripts/deploy-infrastructure-modular.sh dev apply
   ./scripts/deploy-infrastructure-modular.sh prod apply
   ```

## 🛠️ Maintenance

### Updating Modules

To update a module:

1. Edit the module files in `modules/<module-name>/`
2. Test in development environment
3. Apply to production

### Adding New Environments

1. Copy an existing environment directory
2. Modify the configuration as needed
3. Update the deployment script if necessary

### State Management

Consider using Terraform workspaces for better state management:

```bash
# Create workspace
terraform workspace new staging

# Switch workspace
terraform workspace select staging

# Deploy to workspace
terraform apply
```

## 🔍 Troubleshooting

### Common Issues

1. **State file conflicts**: Use different state backends or workspaces
2. **Resource naming conflicts**: Use different project names or environments
3. **Permission issues**: Ensure AWS credentials have sufficient permissions
4. **Module not found**: Run `terraform init` in the environment directory

### Debugging

Enable Terraform debug logging:

```bash
export TF_LOG=DEBUG
terraform plan
```

### Getting Help

- Check Terraform documentation: https://terraform.io/docs/
- Review AWS provider documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Check module documentation in each module directory

## 📚 Additional Resources

- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Module Registry](https://registry.terraform.io/)

## 🤝 Contributing

When making changes to the infrastructure:

1. Test changes in development first
2. Update documentation
3. Follow Terraform best practices
4. Use meaningful commit messages
5. Consider backward compatibility

## 📄 License

This infrastructure code is part of the ResumeRepublic project and follows the same license terms.
