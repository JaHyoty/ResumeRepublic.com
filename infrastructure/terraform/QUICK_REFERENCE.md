# Terraform Quick Reference

## 🚀 Common Commands

### Using the Deployment Script

```bash
# Plan development environment
./scripts/deploy-infrastructure-modular.sh dev plan

# Deploy development environment
./scripts/deploy-infrastructure-modular.sh dev apply

# Plan production environment
./scripts/deploy-infrastructure-modular.sh prod plan

# Deploy production environment
./scripts/deploy-infrastructure-modular.sh prod apply

# Destroy development environment
./scripts/deploy-infrastructure-modular.sh dev destroy
```

### Using Terraform Directly

```bash
# Navigate to environment
cd infrastructure/terraform/environments/development  # or production

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Destroy
terraform destroy
```

## 📁 Directory Structure

```
infrastructure/terraform/
├── modules/
│   ├── networking/     # VPC, subnets, ALB, security groups
│   ├── database/       # RDS PostgreSQL
│   ├── compute/        # ECS cluster, tasks, services
│   ├── storage/        # S3, CloudFront, ECR
│   ├── iam/           # IAM roles, policies, SSM
│   └── dns/           # Route53, ACM certificates
├── environments/
│   ├── development/    # Dev environment config
│   └── production/     # Prod environment config
└── scripts/
    ├── deploy-infrastructure-modular.sh
    └── migrate-to-modular.sh
```

## 🔧 Configuration Files

### Required Files

Each environment needs:
- `main.tf` - Main configuration
- `variables.tf` - Variable definitions
- `outputs.tf` - Output definitions
- `terraform.tfvars` - Variable values (copy from .example)

### Example Files

- `terraform.tfvars.example` - Template with all variables
- `main.tf.backup` - Original monolithic configuration

## 🌍 Environment Differences

| Feature | Development | Production |
|---------|-------------|------------|
| VPC CIDR | 10.1.0.0/16 | 10.0.0.0/16 |
| Backend Subnets | 10.1.1.0/24, 10.1.2.0/24 | 10.0.1.0/24, 10.0.2.0/24 |
| Database Subnets | 10.1.10.0/24, 10.1.20.0/24 | 10.0.10.0/24, 10.0.20.0/24 |
| Public Subnets | 10.1.101.0/24, 10.1.102.0/24 | 10.0.101.0/24, 10.0.102.0/24 |
| DB Name | resumerepublic_dev | resumerepublic |
| DB Storage | 10GB (max 50GB) | 20GB (max 100GB) |
| Backup Retention | 1 day | 7 days |
| Log Retention | 3 days | 7 days |
| Final Snapshot | Skip | Create |
| Domain | Optional | Required |
| EC2 SSM Role | Enabled | Disabled |
| Debug Mode | Enabled | Disabled |

## 🔑 Required Variables

```hcl
# Minimum required variables
aws_region = "us-east-1"
project_name = "resumerepublic"
db_manage_master_user_password = true  # Use AWS managed password
secret_key = "your-secret-key"
```

## 🔐 Password Management

**Database Passwords**:
- AWS managed with automatic rotation (every 30 days)
- Stored in AWS Secrets Manager
- No manual password management required
- ECS tasks retrieve credentials at runtime

**Application Secrets**:
- Stored in SSM Parameter Store
- Comprehensive coverage of ALL configuration values
- Encrypted with AWS managed keys
- Includes OAuth, API keys, URLs, SSL config, database details

**Secrets Validation**:
```bash
# Validate all secrets are properly configured
./scripts/validate-secrets.sh

# Check specific secret
aws ssm get-parameter --name "/resumerepublic/database/password" --with-decryption
```
- Fine-grained IAM access control

## 📊 Common Outputs

After deployment, you'll get:
- `vpc_id` - VPC identifier
- `rds_endpoint` - Database endpoint
- `ecs_cluster_name` - ECS cluster name
- `cloudfront_domain` - CloudFront domain
- `ecr_repository_url` - ECR repository URL
- `alb_dns_name` - Load balancer DNS name

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found"**
   ```bash
   cd infrastructure/terraform/environments/development
   terraform init
   ```

2. **"terraform.tfvars not found"**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars
   ```

3. **"AWS credentials not configured"**
   ```bash
   aws configure
   ```

4. **"Resource already exists"**
   - Check if resources exist in AWS console
   - Import existing resources or destroy and recreate

### Debug Commands

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform plan

# Show current state
terraform show

# List resources
terraform state list

# Get specific output
terraform output -raw vpc_id
```

## 🔄 Migration Commands

```bash
# Migrate from monolithic to modular
./scripts/migrate-to-modular.sh

# This will:
# 1. Backup current configuration
# 2. Create environment-specific configs
# 3. Guide you through the process
```

## 📝 State Management

### Using Workspaces

```bash
# Create new workspace
terraform workspace new staging

# List workspaces
terraform workspace list

# Switch workspace
terraform workspace select staging

# Show current workspace
terraform workspace show
```

### Remote State (Recommended)

Add to your `main.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "resumerepublic/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## 🎯 Best Practices

1. **Always plan before apply**
   ```bash
   terraform plan
   terraform apply
   ```

2. **Use version control**
   ```bash
   git add .
   git commit -m "Add new infrastructure module"
   ```

3. **Test in development first**
   ```bash
   ./scripts/deploy-infrastructure-modular.sh dev apply
   ```

4. **Keep secrets in terraform.tfvars**
   - Never commit terraform.tfvars to git
   - Use .gitignore to exclude it

5. **Use meaningful names**
   - Project names should be descriptive
   - Resource names should indicate purpose

## 📞 Getting Help

- Check the main README.md for detailed documentation
- Review module-specific documentation in each module directory
- Check Terraform documentation: https://terraform.io/docs/
- Check AWS provider documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
