#!/bin/bash

# Frontend Deployment Script for ResumeRepublic
# Deploys React frontend to S3 + CloudFront with comprehensive validation and error handling
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
    echo "  --no-build           Skip build process (use existing dist directory)"
    echo "  --no-upload          Skip S3 upload (build only)"
    echo "  --no-invalidation    Skip CloudFront invalidation"
    echo "  --force              Force deployment even if no changes detected"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Deploy to detected environment"
    echo "  $0 --environment prod        Deploy to production"
    echo "  $0 --no-build                Deploy without rebuilding"
    echo "  $0 --no-upload               Build only, don't upload"
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
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
    
    # Check Node.js version
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo -e "${RED}❌ Node.js version 18+ is required. Current version: $(node --version)${NC}"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is not installed. Please install jq first.${NC}"
        echo "Ubuntu/Debian: sudo apt-get install jq"
        echo "macOS: brew install jq"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Function to detect environment
detect_environment() {
    # Check for terraform.tfvars in both environments
    if [ -f "$TERRAFORM_DIR/environments/production/terraform.tfvars" ]; then
        echo "prod"
    elif [ -f "$TERRAFORM_DIR/environments/development/terraform.tfvars" ]; then
        echo "dev"
    else
        echo -e "${RED}❌ No terraform.tfvars found in any environment directory${NC}"
        echo -e "${YELLOW}Please run infrastructure deployment first:${NC}"
        echo "  ./scripts/deploy-infrastructure.sh prod apply"
        exit 1
    fi
}

# Function to get infrastructure details
get_infrastructure_details() {
    local env_dir=$1
    local env_path="$TERRAFORM_DIR/environments/$env_dir"
    
    echo -e "${YELLOW}📊 Getting infrastructure details...${NC}"
    
    if [ ! -d "$env_path" ]; then
        echo -e "${RED}❌ Environment directory not found: $env_path${NC}"
        exit 1
    fi
    
    cd "$env_path"
    
    # Get S3 bucket name
    S3_BUCKET=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
    if [ -z "$S3_BUCKET" ]; then
        echo -e "${RED}❌ Could not get S3 bucket name. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    # Get ALB DNS name
    ALB_DNS_NAME=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
    
    # Get API domain name
    API_DOMAIN_NAME=$(terraform output -raw api_domain_name 2>/dev/null || echo "")
    
    # Get CloudFront distribution ID
    CLOUDFRONT_DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    
    # Get custom domain
    CUSTOM_DOMAIN=$(terraform output -raw custom_domain 2>/dev/null || echo "")
    WWW_DOMAIN=$(terraform output -raw www_domain 2>/dev/null || echo "")
    CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain 2>/dev/null || echo "")
    
    cd - > /dev/null
    
    # Determine backend URL
    if [ -n "$API_DOMAIN_NAME" ]; then
        BACKEND_URL="https://$API_DOMAIN_NAME"
    elif [ -n "$ALB_DNS_NAME" ]; then
        BACKEND_URL="https://$ALB_DNS_NAME"
    else
        echo -e "${RED}❌ Could not determine backend URL. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ S3 Bucket: $S3_BUCKET${NC}"
    echo -e "${GREEN}✅ Backend URL: $BACKEND_URL${NC}"
    if [ -n "$CUSTOM_DOMAIN" ]; then
        echo -e "${GREEN}✅ Custom Domain: $CUSTOM_DOMAIN${NC}"
    else
        echo -e "${GREEN}✅ CloudFront Domain: $CLOUDFRONT_DOMAIN${NC}"
    fi
}

# Function to check if frontend directory exists
check_frontend_directory() {
    if [ ! -d "frontend" ]; then
        echo -e "${RED}❌ Frontend directory not found. Please run from project root.${NC}"
        exit 1
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        echo -e "${RED}❌ package.json not found in frontend directory.${NC}"
        exit 1
    fi
}

# Function to build frontend
build_frontend() {
    local no_build=$1
    local backend_url=$2
    
    if [ "$no_build" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping build process (--no-build specified)${NC}"
        
        # Check if dist directory exists
        if [ ! -d "frontend/dist" ]; then
            echo -e "${RED}❌ dist directory not found. Please build the frontend first.${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Using existing dist directory${NC}"
        return
    fi
    
    echo -e "${YELLOW}🏗️  Building frontend...${NC}"
    
    cd frontend
    
    # Install dependencies
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    if ! npm ci; then
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
    
    # Build the application with backend URL
    echo -e "${YELLOW}🔨 Building React application...${NC}"
    echo -e "${BLUE}Setting VITE_API_BASE_URL=$backend_url${NC}"
    
    # Set environment variable and build
    if ! VITE_API_BASE_URL=$backend_url npm run build; then
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
    
    # Check if build was successful
    if [ ! -d "dist" ]; then
        echo -e "${RED}❌ Build failed. No dist directory found.${NC}"
        exit 1
    fi
    
    # Check if index.html exists
    if [ ! -f "dist/index.html" ]; then
        echo -e "${RED}❌ Build failed. index.html not found in dist directory.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Frontend built successfully!${NC}"
    
    # Show build size
    BUILD_SIZE=$(du -sh dist | cut -f1)
    echo -e "${BLUE}ℹ️  Build size: $BUILD_SIZE${NC}"
    
    cd - > /dev/null
}

# Function to check if deployment is needed
check_deployment_needed() {
    local s3_bucket=$1
    local force=$2
    
    if [ "$force" = "true" ]; then
        echo -e "${YELLOW}🔄 Force deployment requested${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}🔍 Checking if deployment is needed...${NC}"
    
    # Check if S3 bucket exists
    if ! aws s3 ls s3://$s3_bucket > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  S3 bucket not found or not accessible. Deployment needed.${NC}"
        return 0
    fi
    
    # Check if index.html exists in S3
    if ! aws s3 ls s3://$s3_bucket/index.html > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  index.html not found in S3. Deployment needed.${NC}"
        return 0
    fi
    
    # Compare local and remote build timestamps
    LOCAL_BUILD_TIME=$(stat -c %Y frontend/dist/index.html 2>/dev/null || echo "0")
    REMOTE_BUILD_TIME=$(aws s3api head-object --bucket $s3_bucket --key index.html --query 'LastModified' --output text 2>/dev/null || echo "1970-01-01T00:00:00.000Z")
    REMOTE_BUILD_TIME=$(date -d "$REMOTE_BUILD_TIME" +%s 2>/dev/null || echo "0")
    
    if [ "$LOCAL_BUILD_TIME" -gt "$REMOTE_BUILD_TIME" ]; then
        echo -e "${YELLOW}⚠️  Local build is newer than remote. Deployment needed.${NC}"
        return 0
    fi
    
    echo -e "${GREEN}✅ No deployment needed. Frontend is up to date.${NC}"
    echo -e "${BLUE}ℹ️  Use --force to deploy anyway${NC}"
    return 1
}

# Function to upload to S3
upload_to_s3() {
    local s3_bucket=$1
    local no_upload=$2
    
    if [ "$no_upload" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping S3 upload (--no-upload specified)${NC}"
        return
    fi
    
    echo -e "${YELLOW}📤 Uploading frontend to S3...${NC}"
    
    # Upload files to S3
    if ! aws s3 sync frontend/dist/ s3://$s3_bucket --delete; then
        echo -e "${RED}❌ Failed to upload to S3${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Frontend uploaded to S3!${NC}"
    
    # Set proper content types
    echo -e "${YELLOW}🔧 Setting content types...${NC}"
    
    # Set HTML content type
    aws s3 cp s3://$s3_bucket/index.html s3://$s3_bucket/index.html --content-type "text/html" --metadata-directive REPLACE
    
    # Set CSS content type
    aws s3 cp s3://$s3_bucket/assets/ s3://$s3_bucket/assets/ --recursive --exclude "*" --include "*.css" --content-type "text/css" --metadata-directive REPLACE
    
    # Set JS content type
    aws s3 cp s3://$s3_bucket/assets/ s3://$s3_bucket/assets/ --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --metadata-directive REPLACE
    
    echo -e "${GREEN}✅ Content types set successfully!${NC}"
}

# Function to create CloudFront invalidation
create_cloudfront_invalidation() {
    local cloudfront_distribution_id=$1
    local no_invalidation=$2
    
    if [ "$no_invalidation" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping CloudFront invalidation (--no-invalidation specified)${NC}"
        return
    fi
    
    if [ -z "$cloudfront_distribution_id" ]; then
        echo -e "${YELLOW}⚠️  CloudFront distribution ID not found. Skipping invalidation.${NC}"
        return
    fi
    
    echo -e "${YELLOW}🔄 Creating CloudFront invalidation...${NC}"
    
    # Create invalidation
    local invalidation_id
    invalidation_id=$(aws cloudfront create-invalidation \
        --distribution-id $cloudfront_distribution_id \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    if [ -z "$invalidation_id" ]; then
        echo -e "${RED}❌ Failed to create CloudFront invalidation${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ CloudFront invalidation created: $invalidation_id${NC}"
    
    # Wait for invalidation to complete
    echo -e "${YELLOW}⏳ Waiting for invalidation to complete...${NC}"
    if ! aws cloudfront wait invalidation-completed \
        --distribution-id $cloudfront_distribution_id \
        --id $invalidation_id; then
        echo -e "${YELLOW}⚠️  Invalidation did not complete within timeout${NC}"
        echo -e "${BLUE}ℹ️  Check invalidation status:${NC}"
        echo "  aws cloudfront get-invalidation --distribution-id $cloudfront_distribution_id --id $invalidation_id"
    else
        echo -e "${GREEN}✅ CloudFront invalidation completed!${NC}"
    fi
}

# Function to test deployment
test_deployment() {
    local custom_domain=$1
    local www_domain=$2
    local cloudfront_domain=$3
    
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    
    # Determine frontend URL
    local frontend_url
    if [ -n "$custom_domain" ]; then
        frontend_url="https://$custom_domain"
    else
        frontend_url="https://$cloudfront_domain"
    fi
    
    # Wait a bit for CloudFront to propagate
    echo -e "${YELLOW}⏳ Waiting for CloudFront propagation...${NC}"
    sleep 30
    
    # Test frontend
    echo -e "${YELLOW}🔍 Testing frontend...${NC}"
    if curl -f -s "$frontend_url" > /dev/null; then
        echo -e "${GREEN}✅ Frontend is accessible!${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend may not be accessible yet. CloudFront propagation can take up to 15 minutes.${NC}"
    fi
    
    # Test www domain if it exists
    if [ -n "$www_domain" ]; then
        echo -e "${YELLOW}🔍 Testing www domain...${NC}"
        if curl -f -s "https://$www_domain" > /dev/null; then
            echo -e "${GREEN}✅ WWW domain is accessible!${NC}"
        else
            echo -e "${YELLOW}⚠️  WWW domain may not be accessible yet.${NC}"
        fi
    fi
}

# Function to display summary
display_summary() {
    local custom_domain=$1
    local www_domain=$2
    local cloudfront_domain=$3
    local s3_bucket=$4
    local backend_url=$5
    
    echo ""
    echo -e "${GREEN}🎉 Frontend deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Your frontend is now available at:${NC}"
    if [ -n "$custom_domain" ]; then
        echo "  https://$custom_domain"
        if [ -n "$www_domain" ]; then
            echo "  https://$www_domain"
        fi
    else
        echo "  https://$cloudfront_domain"
    fi
    echo ""
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo "  S3 Bucket: $s3_bucket"
    echo "  Backend URL: $backend_url"
    echo "  CloudFront Domain: $cloudfront_domain"
    if [ -n "$custom_domain" ]; then
        echo "  Custom Domain: $custom_domain"
    fi
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "  1. Test your frontend application"
    echo "  2. Update OAuth redirect URIs with the new domain"
    echo "  3. Monitor CloudFront metrics and logs"
    echo "  4. Set up monitoring and alerts"
}

# Main script logic
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    NO_BUILD="false"
    NO_UPLOAD="false"
    NO_INVALIDATION="false"
    FORCE="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --no-build)
                NO_BUILD="true"
                shift
                ;;
            --no-upload)
                NO_UPLOAD="true"
                shift
                ;;
            --no-invalidation)
                NO_INVALIDATION="true"
                shift
                ;;
            --force)
                FORCE="true"
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
    
    # Auto-detect environment if not specified
    if [ -z "$ENVIRONMENT" ]; then
        ENVIRONMENT=$(detect_environment)
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
    
    echo -e "${BLUE}🎨 ResumeRepublic Frontend Deployment${NC}"
    echo "====================================="
    echo -e "Environment: ${YELLOW}$ENV_NAME${NC}"
    echo -e "No Build: ${YELLOW}$NO_BUILD${NC}"
    echo -e "No Upload: ${YELLOW}$NO_UPLOAD${NC}"
    echo -e "No Invalidation: ${YELLOW}$NO_INVALIDATION${NC}"
    echo -e "Force: ${YELLOW}$FORCE${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Check frontend directory
    check_frontend_directory
    
    # Get infrastructure details
    get_infrastructure_details "$ENV_DIR"
    
    # Check if deployment is needed
    if ! check_deployment_needed "$S3_BUCKET" "$FORCE"; then
        exit 0
    fi
    
    # Build frontend
    build_frontend "$NO_BUILD" "$BACKEND_URL"
    
    # Upload to S3
    upload_to_s3 "$S3_BUCKET" "$NO_UPLOAD"
    
    # Create CloudFront invalidation
    create_cloudfront_invalidation "$CLOUDFRONT_DISTRIBUTION_ID" "$NO_INVALIDATION"
    
    # Test deployment
    test_deployment "$CUSTOM_DOMAIN" "$WWW_DOMAIN" "$CLOUDFRONT_DOMAIN"
    
    # Display summary
    display_summary "$CUSTOM_DOMAIN" "$WWW_DOMAIN" "$CLOUDFRONT_DOMAIN" "$S3_BUCKET" "$BACKEND_URL"
}

# Run main function
main "$@"