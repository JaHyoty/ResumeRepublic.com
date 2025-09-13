#!/bin/bash

# Deployment Validation Script for ResumeRepublic
# Validates all prerequisites, variables, and dependencies for deployment
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

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --environment ENV    Target environment (dev/prod) - auto-detected if not specified"
    echo "  --check-all          Check all environments"
    echo "  --fix                Attempt to fix common issues"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Validate detected environment"
    echo "  $0 --environment prod        Validate production environment"
    echo "  $0 --check-all               Validate all environments"
    echo "  $0 --fix                     Attempt to fix common issues"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    local errors=0
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS CLI is not configured${NC}"
        echo -e "${YELLOW}   Fix: Run 'aws configure'${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ AWS CLI is configured${NC}"
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        echo -e "${YELLOW}   Fix: Install Terraform from https://www.terraform.io/downloads.html${NC}"
        errors=$((errors + 1))
    else
        local terraform_version=$(terraform --version | head -n1 | cut -d' ' -f2 | cut -d'v' -f2)
        echo -e "${GREEN}✅ Terraform is installed (version: $terraform_version)${NC}"
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        echo -e "${YELLOW}   Fix: Start Docker service${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Docker is running${NC}"
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        echo -e "${YELLOW}   Fix: Install Node.js from https://nodejs.org/${NC}"
        errors=$((errors + 1))
    else
        local node_version=$(node --version | cut -d'v' -f2)
        local node_major=$(echo $node_version | cut -d'.' -f1)
        if [ "$node_major" -lt 18 ]; then
            echo -e "${RED}❌ Node.js version 18+ is required (current: $node_version)${NC}"
            echo -e "${YELLOW}   Fix: Update Node.js to version 18 or higher${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Node.js is installed (version: $node_version)${NC}"
        fi
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed${NC}"
        echo -e "${YELLOW}   Fix: Install npm (usually comes with Node.js)${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ npm is installed${NC}"
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is not installed${NC}"
        echo -e "${YELLOW}   Fix: Install jq (Ubuntu/Debian: sudo apt-get install jq)${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ jq is installed${NC}"
    fi
    
    return $errors
}

# Function to check AWS permissions
check_aws_permissions() {
    echo -e "${YELLOW}🔐 Checking AWS permissions...${NC}"
    
    local errors=0
    
    # Check basic IAM permissions
    if ! aws iam get-user > /dev/null 2>&1; then
        echo -e "${RED}❌ Insufficient IAM permissions${NC}"
        echo -e "${YELLOW}   Fix: Ensure your user has necessary IAM permissions${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ IAM permissions are sufficient${NC}"
    fi
    
    # Check ECS permissions
    if ! aws ecs list-clusters > /dev/null 2>&1; then
        echo -e "${RED}❌ Insufficient ECS permissions${NC}"
        echo -e "${YELLOW}   Fix: Ensure your user has ECS permissions${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ ECS permissions are sufficient${NC}"
    fi
    
    # Check S3 permissions
    if ! aws s3 ls > /dev/null 2>&1; then
        echo -e "${RED}❌ Insufficient S3 permissions${NC}"
        echo -e "${YELLOW}   Fix: Ensure your user has S3 permissions${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ S3 permissions are sufficient${NC}"
    fi
    
    # Check ECR permissions
    if ! aws ecr describe-repositories > /dev/null 2>&1; then
        echo -e "${RED}❌ Insufficient ECR permissions${NC}"
        echo -e "${YELLOW}   Fix: Ensure your user has ECR permissions${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ ECR permissions are sufficient${NC}"
    fi
    
    return $errors
}

# Function to check environment configuration
check_environment_config() {
    local env_dir=$1
    local env_name=$2
    local env_path="$TERRAFORM_DIR/environments/$env_dir"
    
    echo -e "${YELLOW}🔍 Checking $env_name environment configuration...${NC}"
    
    local errors=0
    
    # Check if environment directory exists
    if [ ! -d "$env_path" ]; then
        echo -e "${RED}❌ Environment directory not found: $env_path${NC}"
        echo -e "${YELLOW}   Fix: Create environment directory and configuration${NC}"
        errors=$((errors + 1))
        return $errors
    fi
    
    # Check if terraform.tfvars exists
    if [ ! -f "$env_path/terraform.tfvars" ]; then
        echo -e "${RED}❌ terraform.tfvars not found in $env_path${NC}"
        echo -e "${YELLOW}   Fix: Create terraform.tfvars with required variables${NC}"
        errors=$((errors + 1))
        return $errors
    fi
    
    # Check if terraform.tfvars is valid
    cd "$env_path"
    if ! terraform console -var-file="terraform.tfvars" <<< "var.project_name" > /dev/null 2>&1; then
        echo -e "${RED}❌ terraform.tfvars is invalid${NC}"
        echo -e "${YELLOW}   Fix: Check terraform.tfvars syntax and format${NC}"
        errors=$((errors + 1))
        cd - > /dev/null
        return $errors
    fi
    cd - > /dev/null
    
    # Check required variables
    echo -e "${YELLOW}🔍 Checking required variables...${NC}"
    
    local required_vars=("project_name" "domain_name" "db_password" "secret_key")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var" "$env_path/terraform.tfvars"; then
            echo -e "${RED}❌ Required variable '$var' not found in terraform.tfvars${NC}"
            echo -e "${YELLOW}   Fix: Add '$var = \"your-value\"' to terraform.tfvars${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Variable '$var' is configured${NC}"
        fi
    done
    
    # Check optional variables
    echo -e "${YELLOW}🔍 Checking optional variables...${NC}"
    
    local optional_vars=("google_client_id" "google_client_secret" "github_client_id" "github_client_secret" "openrouter_api_key")
    for var in "${optional_vars[@]}"; do
        if grep -q "^$var" "$env_path/terraform.tfvars"; then
            echo -e "${GREEN}✅ Variable '$var' is configured${NC}"
        else
            echo -e "${YELLOW}⚠️  Variable '$var' is not configured (optional)${NC}"
        fi
    done
    
    return $errors
}

# Function to check project structure
check_project_structure() {
    echo -e "${YELLOW}🔍 Checking project structure...${NC}"
    
    local errors=0
    
    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        echo -e "${RED}❌ Backend directory not found${NC}"
        echo -e "${YELLOW}   Fix: Ensure backend directory exists with application code${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Backend directory exists${NC}"
        
        # Check if backend has required files
        if [ ! -f "backend/Dockerfile" ]; then
            echo -e "${RED}❌ Backend Dockerfile not found${NC}"
            echo -e "${YELLOW}   Fix: Create Dockerfile in backend directory${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Backend Dockerfile exists${NC}"
        fi
        
        if [ ! -f "backend/requirements.txt" ]; then
            echo -e "${RED}❌ Backend requirements.txt not found${NC}"
            echo -e "${YELLOW}   Fix: Create requirements.txt in backend directory${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Backend requirements.txt exists${NC}"
        fi
    fi
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        echo -e "${RED}❌ Frontend directory not found${NC}"
        echo -e "${YELLOW}   Fix: Ensure frontend directory exists with React application${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Frontend directory exists${NC}"
        
        # Check if frontend has required files
        if [ ! -f "frontend/package.json" ]; then
            echo -e "${RED}❌ Frontend package.json not found${NC}"
            echo -e "${YELLOW}   Fix: Create package.json in frontend directory${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Frontend package.json exists${NC}"
        fi
        
        if [ ! -f "frontend/vite.config.js" ] && [ ! -f "frontend/vite.config.ts" ]; then
            echo -e "${YELLOW}⚠️  Frontend Vite config not found (optional)${NC}"
        else
            echo -e "${GREEN}✅ Frontend Vite config exists${NC}"
        fi
    fi
    
    # Check if scripts directory exists
    if [ ! -d "scripts" ]; then
        echo -e "${RED}❌ Scripts directory not found${NC}"
        echo -e "${YELLOW}   Fix: Ensure scripts directory exists with deployment scripts${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Scripts directory exists${NC}"
        
        # Check if required scripts exist
        local required_scripts=("deploy-infrastructure.sh" "deploy-backend.sh" "run-database-migration.sh" "deploy-frontend.sh")
        for script in "${required_scripts[@]}"; do
            if [ ! -f "scripts/$script" ]; then
                echo -e "${RED}❌ Required script '$script' not found${NC}"
                echo -e "${YELLOW}   Fix: Create '$script' in scripts directory${NC}"
                errors=$((errors + 1))
            else
                echo -e "${GREEN}✅ Script '$script' exists${NC}"
            fi
        done
    fi
    
    # Check if infrastructure directory exists
    if [ ! -d "infrastructure" ]; then
        echo -e "${RED}❌ Infrastructure directory not found${NC}"
        echo -e "${YELLOW}   Fix: Ensure infrastructure directory exists with Terraform code${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Infrastructure directory exists${NC}"
        
        # Check if Terraform modules exist
        if [ ! -d "infrastructure/terraform/modules" ]; then
            echo -e "${RED}❌ Terraform modules directory not found${NC}"
            echo -e "${YELLOW}   Fix: Ensure Terraform modules directory exists${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Terraform modules directory exists${NC}"
        fi
    fi
    
    return $errors
}

# Function to check infrastructure deployment
check_infrastructure_deployment() {
    local env_dir=$1
    local env_name=$2
    local env_path="$TERRAFORM_DIR/environments/$env_dir"
    
    echo -e "${YELLOW}🔍 Checking $env_name infrastructure deployment...${NC}"
    
    local errors=0
    
    if [ ! -d "$env_path" ]; then
        echo -e "${RED}❌ Environment directory not found: $env_path${NC}"
        errors=$((errors + 1))
        return $errors
    fi
    
    cd "$env_path"
    
    # Check if Terraform is initialized
    if [ ! -d ".terraform" ]; then
        echo -e "${RED}❌ Terraform not initialized${NC}"
        echo -e "${YELLOW}   Fix: Run 'terraform init' in $env_path${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Terraform is initialized${NC}"
    fi
    
    # Check if Terraform state exists
    if [ ! -f "terraform.tfstate" ]; then
        echo -e "${YELLOW}⚠️  Terraform state not found (infrastructure not deployed)${NC}"
        echo -e "${BLUE}ℹ️  This is normal if infrastructure hasn't been deployed yet${NC}"
    else
        echo -e "${GREEN}✅ Terraform state exists${NC}"
        
        # Check if infrastructure is deployed
        if terraform output > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Infrastructure is deployed${NC}"
            
            # Check key outputs
            local outputs=("ecs_cluster_name" "ecr_repository_url" "s3_bucket_name" "alb_dns_name")
            for output in "${outputs[@]}"; do
                if terraform output -raw "$output" > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ Output '$output' is available${NC}"
                else
                    echo -e "${RED}❌ Output '$output' is not available${NC}"
                    errors=$((errors + 1))
                fi
            done
        else
            echo -e "${RED}❌ Infrastructure outputs not available${NC}"
            echo -e "${YELLOW}   Fix: Check Terraform state and re-deploy if needed${NC}"
            errors=$((errors + 1))
        fi
    fi
    
    cd - > /dev/null
    return $errors
}

# Function to attempt to fix common issues
fix_common_issues() {
    echo -e "${YELLOW}🔧 Attempting to fix common issues...${NC}"
    
    local fixes=0
    
    # Make scripts executable
    echo -e "${YELLOW}🔧 Making scripts executable...${NC}"
    if [ -d "scripts" ]; then
        chmod +x scripts/*.sh
        echo -e "${GREEN}✅ Scripts made executable${NC}"
        fixes=$((fixes + 1))
    fi
    
    # Initialize Terraform if needed
    echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
    for env_dir in "development" "production"; do
        local env_path="$TERRAFORM_DIR/environments/$env_dir"
        if [ -d "$env_path" ] && [ ! -d "$env_path/.terraform" ]; then
            cd "$env_path"
            if terraform init > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Terraform initialized in $env_dir${NC}"
                fixes=$((fixes + 1))
            fi
            cd - > /dev/null
        fi
    done
    
    # Install frontend dependencies if needed
    echo -e "${YELLOW}🔧 Installing frontend dependencies...${NC}"
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            if npm install > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
                fixes=$((fixes + 1))
            fi
        fi
        cd - > /dev/null
    fi
    
    echo -e "${GREEN}✅ Fixed $fixes issues${NC}"
}

# Function to display summary
display_summary() {
    local total_errors=$1
    local env_name=$2
    
    echo ""
    echo -e "${BLUE}📊 Validation Summary${NC}"
    echo "=================="
    
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}🎉 All validations passed!${NC}"
        echo -e "${BLUE}ℹ️  $env_name environment is ready for deployment${NC}"
        echo ""
        echo -e "${BLUE}📋 Next steps:${NC}"
        echo "  1. Deploy infrastructure: ./scripts/deploy-infrastructure.sh $env_name apply"
        echo "  2. Deploy backend: ./scripts/deploy-backend.sh"
        echo "  3. Run migrations: ./scripts/run-database-migration.sh"
        echo "  4. Deploy frontend: ./scripts/deploy-frontend.sh"
    else
        echo -e "${RED}❌ $total_errors validation errors found${NC}"
        echo -e "${YELLOW}Please fix the errors above before deploying${NC}"
        echo ""
        echo -e "${BLUE}📋 Common fixes:${NC}"
        echo "  1. Run with --fix to attempt automatic fixes"
        echo "  2. Check the error messages above for specific fixes"
        echo "  3. Ensure all prerequisites are installed and configured"
    fi
}

# Main script logic
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    CHECK_ALL="false"
    FIX="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --check-all)
                CHECK_ALL="true"
                shift
                ;;
            --fix)
                FIX="true"
                shift
                ;;
            --help)
                usage
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                usage
                ;;
        esac
    done
    
    echo -e "${BLUE}🔍 ResumeRepublic Deployment Validation${NC}"
    echo "====================================="
    echo -e "Check All: ${YELLOW}$CHECK_ALL${NC}"
    echo -e "Fix: ${YELLOW}$FIX${NC}"
    echo ""
    
    local total_errors=0
    
    # Check prerequisites
    if ! check_prerequisites; then
        total_errors=$((total_errors + $?))
    fi
    
    # Check AWS permissions
    if ! check_aws_permissions; then
        total_errors=$((total_errors + $?))
    fi
    
    # Check project structure
    if ! check_project_structure; then
        total_errors=$((total_errors + $?))
    fi
    
    # Check environments
    if [ "$CHECK_ALL" = "true" ]; then
        # Check all environments
        for env_dir in "development" "production"; do
            local env_name
            case $env_dir in
                development) env_name="development" ;;
                production) env_name="production" ;;
            esac
            
            if ! check_environment_config "$env_dir" "$env_name"; then
                total_errors=$((total_errors + $?))
            fi
            
            if ! check_infrastructure_deployment "$env_dir" "$env_name"; then
                total_errors=$((total_errors + $?))
            fi
        done
    else
        # Check specific environment
        if [ -z "$ENVIRONMENT" ]; then
            # Auto-detect environment
            if [ -f "$TERRAFORM_DIR/environments/production/terraform.tfvars" ]; then
                ENVIRONMENT="prod"
            elif [ -f "$TERRAFORM_DIR/environments/development/terraform.tfvars" ]; then
                ENVIRONMENT="dev"
            else
                echo -e "${RED}❌ No environment configuration found${NC}"
                exit 1
            fi
        fi
        
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
                echo -e "${YELLOW}Valid environments: dev, development, prod, production${NC}"
                exit 1
                ;;
        esac
        
        if ! check_environment_config "$ENV_DIR" "$ENV_NAME"; then
            total_errors=$((total_errors + $?))
        fi
        
        if ! check_infrastructure_deployment "$ENV_DIR" "$ENV_NAME"; then
            total_errors=$((total_errors + $?))
        fi
    fi
    
    # Attempt to fix issues if requested
    if [ "$FIX" = "true" ]; then
        fix_common_issues
    fi
    
    # Display summary
    display_summary $total_errors "$ENV_NAME"
    
    # Exit with error code if there are errors
    if [ $total_errors -gt 0 ]; then
        exit 1
    fi
}

# Run main function
main "$@"
