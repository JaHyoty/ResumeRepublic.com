#!/bin/bash

# Secrets setup script for ResumeRepublic AWS deployment
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 ResumeRepublic Secrets Setup${NC}"
echo "=================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Check if terraform.tfvars exists
TFVARS_FILE="infrastructure/terraform/terraform.tfvars"
if [ -f "$TFVARS_FILE" ]; then
    echo -e "${YELLOW}⚠️  terraform.tfvars already exists.${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Keeping existing terraform.tfvars${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}📝 Setting up secrets...${NC}"

# Generate secrets if not provided
DB_PASSWORD=${DB_PASSWORD:-$(generate_password)}
SECRET_KEY=${SECRET_KEY:-$(generate_secret_key)}

# Prompt for OAuth credentials
echo -e "${YELLOW}🔑 OAuth Configuration${NC}"
echo "You'll need to set up OAuth apps for Google and GitHub:"
echo ""

read -p "Google Client ID: " GOOGLE_CLIENT_ID
read -p "Google Client Secret: " -s GOOGLE_CLIENT_SECRET
echo
read -p "GitHub Client ID: " GITHUB_CLIENT_ID
read -p "GitHub Client Secret: " -s GITHUB_CLIENT_SECRET
echo
read -p "OpenRouter API Key: " -s OPENROUTER_API_KEY
echo

# Create terraform.tfvars
cat > "$TFVARS_FILE" << EOF
# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "resumerepublic"
environment  = "production"
domain_name  = "resumerepublic.com"

# Database Configuration
postgres_version = "17.4"
db_password = "$DB_PASSWORD"

# Backend Configuration
backend_desired_count = 1

# Application Configuration (auto-generated)
secret_key = "$SECRET_KEY"

# OAuth Configuration
google_client_id     = "$GOOGLE_CLIENT_ID"
google_client_secret = "$GOOGLE_CLIENT_SECRET"
github_client_id     = "$GITHUB_CLIENT_ID"
github_client_secret = "$GITHUB_CLIENT_SECRET"

# External Services
openrouter_api_key = "$OPENROUTER_API_KEY"
EOF

echo -e "${GREEN}✅ terraform.tfvars created successfully!${NC}"

# Store secrets in AWS Systems Manager Parameter Store
echo -e "${YELLOW}☁️  Storing secrets in AWS Systems Manager...${NC}"

aws ssm put-parameter --name "/resumerepublic/database/password" --value "$DB_PASSWORD" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/app/secret_key" --value "$SECRET_KEY" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/google/client_id" --value "$GOOGLE_CLIENT_ID" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/google/client_secret" --value "$GOOGLE_CLIENT_SECRET" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/github/client_id" --value "$GITHUB_CLIENT_ID" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/github/client_secret" --value "$GITHUB_CLIENT_SECRET" --type "SecureString" --overwrite > /dev/null
aws ssm put-parameter --name "/resumerepublic/openrouter/api_key" --value "$OPENROUTER_API_KEY" --type "SecureString" --overwrite > /dev/null

echo -e "${GREEN}✅ Secrets stored in AWS Systems Manager!${NC}"

# Create GitHub secrets template
echo -e "${YELLOW}📋 GitHub Secrets Setup${NC}"
echo "Add these secrets to your GitHub repository:"
echo "Go to: Settings → Secrets and variables → Actions"
echo ""
echo "Required GitHub Secrets:"
echo "  AWS_ACCESS_KEY_ID: $(aws configure get aws_access_key_id)"
echo "  AWS_SECRET_ACCESS_KEY: [Your AWS Secret Key]"
echo "  DB_PASSWORD: $DB_PASSWORD"
echo "  SECRET_KEY: $SECRET_KEY"
echo "  GOOGLE_CLIENT_ID: $GOOGLE_CLIENT_ID"
echo "  GOOGLE_CLIENT_SECRET: [Hidden]"
echo "  GITHUB_CLIENT_ID: $GITHUB_CLIENT_ID"
echo "  GITHUB_CLIENT_SECRET: [Hidden]"
echo "  OPENROUTER_API_KEY: [Hidden]"

echo ""
echo -e "${GREEN}🎉 Secrets setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "  1. Add GitHub secrets to your repository"
echo "  2. Run: ./scripts/deploy.sh"
echo "  3. Update OAuth app redirect URIs with your CloudFront domain"
