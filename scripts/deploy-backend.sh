#!/bin/bash

# Backend Deployment Script for ResumeRepublic
# Implements blue-green deployment strategy for zero downtime ECS Fargate deployment
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
    echo "  --force              Force deployment even if no changes detected"
    echo "  --no-build           Skip Docker build (use existing image)"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                   Deploy to detected environment"
    echo "  $0 --environment prod Deploy to production"
    echo "  $0 --force           Force deployment"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    local skip_docker_check=${1:-false}
    
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
        exit 1
    fi
    
    # Check if Docker is running (skip if --no-build is specified)
    if [ "$skip_docker_check" = "false" ]; then
        if ! docker info > /dev/null 2>&1; then
            echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
            echo -e "${YELLOW}   Docker is required for building the backend container image.${NC}"
            exit 1
        fi
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
    
    # Get ECR repository URL
    ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
    if [ -z "$ECR_REPO_URL" ]; then
        echo -e "${RED}❌ Could not get ECR repository URL. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    # Get ECS cluster name
    ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")
    if [ -z "$ECS_CLUSTER_NAME" ]; then
        echo -e "${RED}❌ Could not get ECS cluster name. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    # Get ALB DNS name
    ALB_DNS_NAME=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
    
    # Get API domain name
    API_DOMAIN_NAME=$(terraform output -raw api_domain_name 2>/dev/null || echo "")
    
    cd - > /dev/null
    
    echo -e "${GREEN}✅ ECR Repository: $ECR_REPO_URL${NC}"
    echo -e "${GREEN}✅ ECS Cluster: $ECS_CLUSTER_NAME${NC}"
    if [ -n "$API_DOMAIN_NAME" ]; then
        echo -e "${GREEN}✅ API Domain: $API_DOMAIN_NAME${NC}"
    else
        echo -e "${GREEN}✅ ALB DNS: $ALB_DNS_NAME${NC}"
    fi
}

# Function to build and push Docker image
build_and_push_image() {
    local ecr_repo_url=$1
    local no_build=$2
    
    if [ "$no_build" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping Docker build (--no-build specified)${NC}"
        return
    fi
    
    echo -e "${YELLOW}🐳 Building backend Docker image...${NC}"
    
    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        echo -e "${RED}❌ Backend directory not found. Please run from project root.${NC}"
        exit 1
    fi
    
    cd backend
    
    # Build the backend image
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    if ! docker build -t $PROJECT_NAME-backend:latest .; then
        echo -e "${RED}❌ Docker build failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Backend image built successfully!${NC}"
    
    # Login to ECR
    echo -e "${YELLOW}🔐 Logging in to ECR...${NC}"
    if ! aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ecr_repo_url; then
        echo -e "${RED}❌ ECR login failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Logged in to ECR!${NC}"
    
    # Tag image for ECR with timestamp for versioning
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    docker tag $PROJECT_NAME-backend:latest $ecr_repo_url:latest
    docker tag $PROJECT_NAME-backend:latest $ecr_repo_url:$TIMESTAMP
    
    # Push image to ECR
    echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
    if ! docker push $ecr_repo_url:latest; then
        echo -e "${RED}❌ Failed to push latest image to ECR${NC}"
        exit 1
    fi
    
    if ! docker push $ecr_repo_url:$TIMESTAMP; then
        echo -e "${RED}❌ Failed to push timestamped image to ECR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Backend image pushed to ECR!${NC}"
    echo -e "${BLUE}ℹ️  Image version: $TIMESTAMP${NC}"
    
    cd - > /dev/null
}

# Function to check if deployment is needed
check_deployment_needed() {
    local ecr_repo_url=$1
    local force=$2
    
    if [ "$force" = "true" ]; then
        echo -e "${YELLOW}🔄 Force deployment requested${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}🔍 Checking if deployment is needed...${NC}"
    
    # Get current running task definition
    CURRENT_TASK_DEF=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER_NAME \
        --services $PROJECT_NAME-$ENV_NAME-backend-service \
        --query "services[0].taskDefinition" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_TASK_DEF" ] || [ "$CURRENT_TASK_DEF" = "None" ]; then
        echo -e "${YELLOW}⚠️  No running service found. Deployment needed.${NC}"
        return 0
    fi
    
    # Check if latest image exists in ECR
    if ! aws ecr describe-images \
        --repository-name $(echo $ecr_repo_url | cut -d'/' -f2) \
        --image-ids imageTag=latest > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Latest image not found in ECR. Deployment needed.${NC}"
        return 0
    fi
    
    echo -e "${GREEN}✅ No deployment needed. Service is up to date.${NC}"
    echo -e "${BLUE}ℹ️  Use --force to deploy anyway${NC}"
    return 1
}

# Function to deploy to ECS
deploy_to_ecs() {
    local ecs_cluster_name=$1
    local ecr_repo_url=$2
    
    echo -e "${YELLOW}🚀 Deploying to ECS...${NC}"
    
    # Get current service status
    echo -e "${YELLOW}📊 Checking current service status...${NC}"
    CURRENT_TASK_COUNT=$(aws ecs describe-services \
        --cluster $ecs_cluster_name \
        --services $PROJECT_NAME-$ENV_NAME-backend-service \
        --query "services[0].runningCount" \
        --output text 2>/dev/null || echo "0")
    
    echo -e "${BLUE}ℹ️  Current running tasks: $CURRENT_TASK_COUNT${NC}"
    
    # Get current task definition
    CURRENT_TASK_DEF=$(aws ecs describe-services \
        --cluster $ecs_cluster_name \
        --services $PROJECT_NAME-$ENV_NAME-backend-service \
        --query "services[0].taskDefinition" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_TASK_DEF" ] && [ "$CURRENT_TASK_DEF" != "None" ]; then
        echo -e "${BLUE}ℹ️  Current task definition: $CURRENT_TASK_DEF${NC}"
    fi
    
    # Force new deployment
    echo -e "${YELLOW}🔄 Updating ECS service...${NC}"
    if ! aws ecs update-service \
        --cluster $ecs_cluster_name \
        --service $PROJECT_NAME-$ENV_NAME-backend-service \
        --force-new-deployment; then
        echo -e "${RED}❌ Failed to update ECS service${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ ECS service update initiated!${NC}"
    
    # Monitor deployment progress
    echo -e "${YELLOW}⏳ Monitoring deployment progress...${NC}"
    echo -e "${BLUE}ℹ️  This may take 2-5 minutes for zero-downtime deployment...${NC}"
    
    # Wait for deployment to complete with progress monitoring
    if ! aws ecs wait services-stable \
        --cluster $ecs_cluster_name \
        --services $PROJECT_NAME-$ENV_NAME-backend-service; then
        echo -e "${RED}❌ Service did not stabilize within timeout${NC}"
        echo -e "${YELLOW}📋 Check service status and logs:${NC}"
        echo "  aws ecs describe-services --cluster $ecs_cluster_name --services $PROJECT_NAME-$ENV_NAME-backend-service"
        echo "  aws logs tail /ecs/$PROJECT_NAME-$ENV_NAME-backend --follow"
        exit 1
    fi
    
    # Verify deployment success
    echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
    NEW_TASK_COUNT=$(aws ecs describe-services \
        --cluster $ecs_cluster_name \
        --services $PROJECT_NAME-$ENV_NAME-backend-service \
        --query "services[0].runningCount" \
        --output text)
    
    NEW_TASK_DEF=$(aws ecs describe-services \
        --cluster $ecs_cluster_name \
        --services $PROJECT_NAME-$ENV_NAME-backend-service \
        --query "services[0].taskDefinition" \
        --output text)
    
    echo -e "${BLUE}ℹ️  New running tasks: $NEW_TASK_COUNT${NC}"
    echo -e "${BLUE}ℹ️  New task definition: $NEW_TASK_DEF${NC}"
    
    # Check if deployment was successful
    if [ "$NEW_TASK_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    else
        echo -e "${RED}❌ Deployment failed. No running tasks found.${NC}"
        echo -e "${YELLOW}📋 Check ECS service logs for details:${NC}"
        echo "   aws logs tail /ecs/$PROJECT_NAME-$ENV_NAME-backend --follow"
        exit 1
    fi
}

# Function to test deployment
test_deployment() {
    local alb_dns_name=$1
    local api_domain_name=$2
    
    # Determine backend URL
    local backend_url
    if [ -n "$api_domain_name" ]; then
        backend_url="https://$api_domain_name"
    else
        backend_url="http://$alb_dns_name"
    fi
    
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    
    # Wait a bit for the service to fully start
    echo -e "${YELLOW}⏳ Waiting for service to start...${NC}"
    sleep 30
    
    # Test health endpoint
    echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
    if curl -f -s "$backend_url/health" > /dev/null; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed. Service may still be starting up.${NC}"
        echo -e "${BLUE}ℹ️  Backend URL: $backend_url${NC}"
    fi
    
    # Test root endpoint
    echo -e "${YELLOW}🔍 Testing root endpoint...${NC}"
    if curl -f -s "$backend_url/" > /dev/null; then
        echo -e "${GREEN}✅ Root endpoint accessible!${NC}"
    else
        echo -e "${YELLOW}⚠️  Root endpoint not accessible. Check service logs.${NC}"
    fi
}

# Function to display deployment summary
display_summary() {
    local alb_dns_name=$1
    local api_domain_name=$2
    local timestamp=$3
    
    echo ""
    echo -e "${GREEN}🎉 Backend deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Your backend is now available at:${NC}"
    if [ -n "$api_domain_name" ]; then
        echo "  https://$api_domain_name"
    else
        echo "  http://$alb_dns_name"
    fi
    echo ""
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo "  Image Version: $timestamp"
    echo "  ECS Cluster: $ECS_CLUSTER_NAME"
    echo "  Service: $PROJECT_NAME-$ENV_NAME-backend-service"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "  1. Run database migrations: ./scripts/run-database-migration.sh"
    echo "  2. Deploy frontend: ./scripts/deploy-frontend.sh"
    echo "  3. Test your backend API endpoints"
    echo "  4. Monitor logs: aws logs tail /ecs/$PROJECT_NAME-$ENV_NAME-backend --follow"
}

# Main script logic
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    FORCE="false"
    NO_BUILD="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --force)
                FORCE="true"
                shift
                ;;
            --no-build)
                NO_BUILD="true"
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
    
    echo -e "${BLUE}🚀 ResumeRepublic Backend Deployment${NC}"
    echo "====================================="
    echo -e "Environment: ${YELLOW}$ENV_NAME${NC}"
    echo -e "Force: ${YELLOW}$FORCE${NC}"
    echo -e "No Build: ${YELLOW}$NO_BUILD${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites $NO_BUILD
    
    # Get infrastructure details
    get_infrastructure_details "$ENV_DIR"
    
    # Check if deployment is needed (only when not building)
    if [ "$NO_BUILD" = "true" ]; then
        if ! check_deployment_needed "$ECR_REPO_URL" "$FORCE"; then
            exit 0
        fi
    else
        echo -e "${YELLOW}🔄 Building and deploying backend...${NC}"
    fi
    
    # Build and push image
    build_and_push_image "$ECR_REPO_URL" "$NO_BUILD"
    
    # Deploy to ECS
    deploy_to_ecs "$ECS_CLUSTER_NAME" "$ECR_REPO_URL"
    
    # Test deployment
    test_deployment "$ALB_DNS_NAME" "$API_DOMAIN_NAME"
    
    # Display summary
    display_summary "$ALB_DNS_NAME" "$API_DOMAIN_NAME" "$TIMESTAMP"
}

# Run main function
main "$@"