#!/bin/bash

# AWS Deployment Script for CareerPathPro

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_status "All prerequisites found!"
}

# Get AWS account ID
get_aws_account_id() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "Failed to get AWS account ID. Please check your AWS credentials."
        exit 1
    fi
    print_status "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Create ECR repositories
create_ecr_repos() {
    print_step "Creating ECR repositories..."
    
    # Backend repository
    aws ecr create-repository \
        --repository-name careerpathpro-backend \
        --region us-east-1 \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        2>/dev/null || print_warning "Backend repository already exists"
    
    print_status "ECR repositories created!"
}

# Build and push backend image
build_and_push_backend() {
    print_step "Building and pushing backend image..."
    
    # Get ECR login token
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
    
    # Build backend image
    cd ../backend
    docker build -t careerpathpro-backend .
    
    # Tag and push
    docker tag careerpathpro-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/careerpathpro-backend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/careerpathpro-backend:latest
    
    cd ../aws-deployment
    print_status "Backend image pushed to ECR!"
}

# Build and deploy frontend
build_and_deploy_frontend() {
    print_step "Building and deploying frontend..."
    
    # Build frontend
    cd ../frontend
    npm run build
    
    # Get S3 bucket name from Terraform output
    S3_BUCKET=$(cd ../aws-deployment/terraform && terraform output -raw s3_bucket_name)
    
    # Sync to S3
    aws s3 sync dist/ s3://$S3_BUCKET --delete
    
    # Invalidate CloudFront cache
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[0].DomainName=='$S3_BUCKET.s3.amazonaws.com'].Id" --output text)
    if [ ! -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
        aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
    fi
    
    cd ../aws-deployment
    print_status "Frontend deployed to S3 and CloudFront!"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_step "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -var="aws_account_id=$AWS_ACCOUNT_ID" -var="db_password=$DB_PASSWORD" -var="secret_key=$SECRET_KEY"
    
    # Apply deployment
    terraform apply -var="aws_account_id=$AWS_ACCOUNT_ID" -var="db_password=$DB_PASSWORD" -var="secret_key=$SECRET_KEY" -auto-approve
    
    cd ..
    print_status "Infrastructure deployed!"
}

# Get deployment outputs
show_outputs() {
    print_step "Deployment outputs:"
    
    cd terraform
    echo ""
    echo "🌐 Frontend URL:"
    terraform output -raw cloudfront_domain
    echo ""
    echo "🔧 Backend API URL:"
    terraform output -raw alb_dns_name
    echo ""
    echo "🗄️ Database Endpoint:"
    terraform output -raw db_endpoint
    echo ""
    cd ..
}

# Main deployment function
deploy_all() {
    print_step "Starting AWS deployment..."
    
    # Check if required variables are set
    if [ -z "$DB_PASSWORD" ]; then
        print_error "DB_PASSWORD environment variable is required"
        print_error "Example: export DB_PASSWORD='your-secure-password'"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        print_error "SECRET_KEY environment variable is required"
        print_error "Example: export SECRET_KEY='your-secret-key'"
        exit 1
    fi
    
    check_prerequisites
    get_aws_account_id
    create_ecr_repos
    build_and_push_backend
    deploy_infrastructure
    build_and_deploy_frontend
    show_outputs
    
    print_status "🎉 Deployment completed successfully!"
}

# Destroy infrastructure
destroy_infrastructure() {
    print_step "Destroying infrastructure..."
    
    cd terraform
    terraform destroy -var="aws_account_id=$AWS_ACCOUNT_ID" -var="db_password=$DB_PASSWORD" -var="secret_key=$SECRET_KEY" -auto-approve
    cd ..
    
    print_status "Infrastructure destroyed!"
}

# Show help
show_help() {
    echo "AWS Deployment Script for CareerPathPro"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy   Deploy the entire application to AWS"
    echo "  destroy  Destroy the AWS infrastructure"
    echo "  help     Show this help message"
    echo ""
    echo "Required Environment Variables:"
    echo "  DB_PASSWORD  Database password"
    echo "  SECRET_KEY   Application secret key"
    echo ""
    echo "Example:"
    echo "  export DB_PASSWORD='my-secure-password'"
    echo "  export SECRET_KEY='my-secret-key'"
    echo "  $0 deploy"
}

# Main script logic
case "${1:-help}" in
    "deploy")
        deploy_all
        ;;
    "destroy")
        get_aws_account_id
        destroy_infrastructure
        ;;
    "help"|*)
        show_help
        ;;
esac
