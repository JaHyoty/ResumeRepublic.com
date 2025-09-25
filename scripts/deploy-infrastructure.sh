#!/bin/bash

# Infrastructure Deployment Script for ResumeRepublic
# Deploys AWS infrastructure using Terraform with comprehensive validation and error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="resumerepublic"
AWS_REGION="us-east-1"
TERRAFORM_DIR="infrastructure/terraform"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to display usage
usage() {
    echo "Usage: $0 [ENVIRONMENT] [ACTION]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  dev, development    Deploy development environment"
    echo "  prod, production    Deploy production environment"
    echo ""
    echo "ACTION:"
    echo "  plan                Plan the deployment (default)"
    echo "  apply               Apply the deployment (auto-detects count dependencies)"
    echo "  destroy             Destroy the environment"
    echo "  init                Initialize Terraform"
    echo "  validate            Validate Terraform configuration"
    echo ""
    echo "FEATURES:"
    echo "  🎯 Targeted Deployment: Automatically detects count dependency issues"
    echo "     and uses targeted deployment (DNS + Networking first, then rest)"
    echo "  🔍 Smart Detection: Checks for 'Invalid count argument' errors"
    echo "  🚀 Production Ready: Handles complex Terraform dependencies gracefully"
    echo ""
    echo "Examples:"
    echo "  $0 dev plan         Plan development environment"
    echo "  $0 prod apply       Deploy production environment (with auto-targeting)"
    echo "  $0 dev destroy      Destroy development environment"
    echo ""
    echo "Targeted Deployment Process:"
    echo "  1. Detects count dependency issues automatically"
    echo "  2. Phase 1: Deploys Networking module (excluding HTTPS listener)"
    echo "  3. Phase 2: Deploys DNS module (creates ACM certificate)"
    echo "  4. Phase 3: Deploys remaining infrastructure (including HTTPS listener)"
    echo "  5. Provides detailed progress and error handling"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed. Please install Terraform first.${NC}"
        echo "Visit: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is not installed. Please install jq first.${NC}"
        echo "Ubuntu/Debian: sudo apt-get install jq"
        echo "macOS: brew install jq"
        exit 1
    fi
    
    # Check AWS permissions
    echo -e "${YELLOW}🔐 Checking AWS permissions...${NC}"
    if ! aws iam get-user > /dev/null 2>&1; then
        echo -e "${RED}❌ Insufficient AWS permissions. Please ensure your user has necessary IAM permissions.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Function to validate environment configuration
validate_environment() {
    local env_dir=$1
    local env_path="$TERRAFORM_DIR/environments/$env_dir"
    
    echo -e "${YELLOW}🔍 Validating environment configuration...${NC}"
    
    # Check if environment directory exists
    if [ ! -d "$env_path" ]; then
        echo -e "${RED}❌ Environment directory not found: $env_path${NC}"
        exit 1
    fi
    
    # Check if terraform.tfvars exists
    if [ ! -f "$env_path/terraform.tfvars" ]; then
        echo -e "${RED}❌ terraform.tfvars not found in $env_path${NC}"
        echo -e "${YELLOW}📝 Please create terraform.tfvars with required variables:${NC}"
        echo ""
        echo "Required variables:"
        echo "  project_name = \"$PROJECT_NAME\""
        echo "  domain_name  = \"yourdomain.com\""
        echo "  db_password  = \"your-secure-password\""
        echo "  secret_key   = \"your-secret-key\""
        echo ""
        echo "Optional variables:"
        echo "  google_client_id     = \"your-google-client-id\""
        echo "  google_client_secret = \"your-google-client-secret\""
        echo "  github_client_id     = \"your-github-client-id\""
        echo "  github_client_secret = \"your-github-client-secret\""
        echo "  openrouter_api_key   = \"your-openrouter-api-key\""
        echo ""
        echo "Example:"
        echo "  cp $env_path/terraform.tfvars.example $env_path/terraform.tfvars"
        echo "  # Edit $env_path/terraform.tfvars with your values"
        exit 1
    fi
    
    # Validate required variables
    echo -e "${YELLOW}🔍 Validating required variables...${NC}"
    cd "$env_path"
    
    # Check if required variables are set
    if ! terraform console -var-file="terraform.tfvars" <<< "var.project_name" > /dev/null 2>&1; then
        echo -e "${RED}❌ Failed to validate terraform.tfvars. Please check the file format.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Environment configuration valid${NC}"
}

# Function to initialize Terraform
init_terraform() {
    local env_path=$1
    
    echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
    cd "$env_path"
    
    # Initialize Terraform
    if ! terraform init; then
        echo -e "${RED}❌ Terraform initialization failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Terraform initialized successfully${NC}"
}

# Function to validate Terraform configuration
validate_terraform() {
    local env_path=$1
    
    echo -e "${YELLOW}🔍 Validating Terraform configuration...${NC}"
    cd "$env_path"
    
    if ! terraform validate; then
        echo -e "${RED}❌ Terraform configuration validation failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Terraform configuration valid${NC}"
}

# Function to plan deployment
plan_deployment() {
    local env_path=$1
    local env_name=$2
    
    echo -e "${YELLOW}📋 Planning $env_name infrastructure deployment...${NC}"
    cd "$env_path"
    
    if ! terraform plan -out=tfplan; then
        echo -e "${RED}❌ Terraform plan failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Plan completed successfully${NC}"
    echo -e "${BLUE}ℹ️  To apply this plan, run: $0 $ENVIRONMENT apply${NC}"
}

# Function to check for count dependency issues
check_count_dependency() {
    local env_path=$1
    
    echo -e "${YELLOW}🔍 Checking for count dependency issues...${NC}"
    cd "$env_path"
    
    # Try to plan and check for count dependency errors
    if terraform plan -out=tfplan 2>&1 | grep -q "Invalid count argument"; then
        echo -e "${YELLOW}⚠️  Count dependency detected. Using targeted deployment approach.${NC}"
        return 0  # Count dependency found
    else
        return 1  # No count dependency
    fi
}

# Function to apply deployment with targeted approach for count dependencies
apply_deployment_targeted() {
    local env_path=$1
    local env_name=$2
    
    echo -e "${YELLOW}🚀 Deploying $env_name infrastructure with targeted approach...${NC}"
    cd "$env_path"
    
    echo -e "${BLUE}📋 Phase 1: Deploying Networking module (VPC, subnets, security groups)...${NC}"
    # Deploy networking module but exclude the HTTPS listener that has count dependency
    if ! terraform apply -target=module.networking -target=-module.networking.aws_lb_listener.backend_https -auto-approve; then
        echo -e "${RED}❌ Phase 1 deployment failed${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Phase 2: Deploying DNS module...${NC}"
    if ! terraform apply -target=module.dns -auto-approve; then
        echo -e "${RED}❌ Phase 2 deployment failed${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Phase 3: Deploying remaining infrastructure...${NC}"
    if ! terraform apply -auto-approve; then
        echo -e "${RED}❌ Phase 3 deployment failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully with targeted approach!${NC}"
}

# Function to apply deployment
apply_deployment() {
    local env_path=$1
    local env_name=$2
    
    echo -e "${YELLOW}📋 Planning $env_name infrastructure deployment...${NC}"
    cd "$env_path"
    
    # Check for count dependency issues first
    if check_count_dependency "$env_path"; then
        echo -e "${YELLOW}⚠️  Count dependency detected. This is normal for production deployments.${NC}"
        echo -e "${BLUE}ℹ️  Using targeted deployment to resolve count dependency issues.${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Do you want to proceed with targeted deployment? (y/N)${NC}"
        read -p "> " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}ℹ️  Infrastructure deployment cancelled.${NC}"
            exit 0
        fi
        
        apply_deployment_targeted "$env_path" "$env_name"
    else
        # Normal deployment
        if ! terraform plan -out=tfplan; then
            echo -e "${RED}❌ Terraform plan failed${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}⚠️  Review the plan above. Do you want to proceed with infrastructure deployment? (y/N)${NC}"
        read -p "> " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}ℹ️  Infrastructure deployment cancelled.${NC}"
            exit 0
        fi
        
        echo -e "${YELLOW}🚀 Deploying $env_name infrastructure...${NC}"
        
        if ! terraform apply tfplan; then
            echo -e "${RED}❌ Infrastructure deployment failed${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
    fi
    
    # Get outputs
    echo -e "${YELLOW}📊 Getting deployment outputs...${NC}"
    VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "N/A")
    RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "N/A")
    ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "N/A")
    CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain 2>/dev/null || echo "N/A")
    ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "N/A")
    ALB_DNS_NAME=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")
    
    echo ""
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo "  Environment: $env_name"
    echo "  VPC ID: $VPC_ID"
    echo "  RDS Endpoint: $RDS_ENDPOINT"
    echo "  ECS Cluster: $ECS_CLUSTER_NAME"
    echo "  CloudFront Domain: $CLOUDFRONT_DOMAIN"
    echo "  ECR Repository: $ECR_REPOSITORY_URL"
    echo "  ALB DNS Name: $ALB_DNS_NAME"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "  1. Deploy backend: ./scripts/deploy-backend.sh"
    echo "  2. Run migrations: ./scripts/run-database-migration.sh"
    echo "  3. Deploy frontend: ./scripts/deploy-frontend.sh"
}

# Function to destroy infrastructure
destroy_infrastructure() {
    local env_path=$1
    local env_name=$2
    
    echo -e "${RED}⚠️  WARNING: This will destroy the $env_name environment!${NC}"
    echo -e "${YELLOW}This action cannot be undone and will delete all resources and data.${NC}"
    echo -e "${YELLOW}Are you sure? Type 'yes' to confirm:${NC}"
    read -p "> " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${BLUE}ℹ️  Destruction cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}🗑️  Destroying $env_name infrastructure...${NC}"
    cd "$env_path"
    
    if ! terraform destroy -auto-approve; then
        echo -e "${RED}❌ Infrastructure destruction failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Infrastructure destroyed successfully${NC}"
}

# Main script logic
main() {
    # Check arguments
    if [ $# -lt 1 ]; then
        echo -e "${RED}❌ Error: Environment is required${NC}"
        usage
    fi
    
    ENVIRONMENT=$1
    ACTION=${2:-plan}
    
    # Validate environment
    case $ENVIRONMENT in
        dev|development)
            ENV_DIR="development"
            ENV_NAME="development"
            ;;
        prod|production)
            ENV_DIR="production"
            ENV_NAME="production"
            ;;
        *)
            echo -e "${RED}❌ Error: Invalid environment '$ENVIRONMENT'${NC}"
            usage
            ;;
    esac
    
    # Validate action
    case $ACTION in
        plan|apply|destroy|init|validate)
            ;;
        *)
            echo -e "${RED}❌ Error: Invalid action '$ACTION'${NC}"
            usage
            ;;
    esac
    
    echo -e "${BLUE}🏗️  ResumeRepublic Infrastructure Deployment${NC}"
    echo "============================================="
    echo -e "Environment: ${YELLOW}$ENV_NAME${NC}"
    echo -e "Action: ${YELLOW}$ACTION${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Set environment path
    ENV_PATH="$PROJECT_ROOT/$TERRAFORM_DIR/environments/$ENV_DIR"
    
    # Validate environment configuration
    validate_environment "$ENV_DIR"
    
    # Handle different actions
    case $ACTION in
        init)
            init_terraform "$ENV_PATH"
            ;;
        validate)
            init_terraform "$ENV_PATH"
            validate_terraform "$ENV_PATH"
            ;;
        plan)
            init_terraform "$ENV_PATH"
            validate_terraform "$ENV_PATH"
            plan_deployment "$ENV_PATH" "$ENV_NAME"
            ;;
        apply)
            init_terraform "$ENV_PATH"
            validate_terraform "$ENV_PATH"
            apply_deployment "$ENV_PATH" "$ENV_NAME"
            ;;
        destroy)
            init_terraform "$ENV_PATH"
            destroy_infrastructure "$ENV_PATH" "$ENV_NAME"
            ;;
    esac
}

# Run main function
main "$@"