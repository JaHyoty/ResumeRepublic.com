#!/bin/bash

# Database Migration Rollback Script for ResumeRepublic
# Rolls back database migrations using Alembic with comprehensive validation and error handling
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
    echo "  --target TARGET      Rollback target (default: head-1)"
    echo "  --dry-run            Show what would be rolled back without executing"
    echo "  --force              Skip confirmation prompts"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Rollback one migration"
    echo "  $0 --target base             Rollback to empty database"
    echo "  $0 --target abc123           Rollback to specific migration"
    echo "  $0 --dry-run                 Show what would be rolled back"
    echo "  $0 --environment prod        Rollback on production"
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
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        echo -e "${YELLOW}   Docker is required for building the migration container.${NC}"
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
    
    # Get ECS cluster name
    ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")
    if [ -z "$ECS_CLUSTER_NAME" ]; then
        echo -e "${RED}❌ Could not get ECS cluster name. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    # Get migration task definition
    MIGRATION_TASK_DEFINITION=$(terraform output -raw migration_task_definition_arn 2>/dev/null || echo "")
    if [ -z "$MIGRATION_TASK_DEFINITION" ]; then
        echo -e "${RED}❌ Could not get migration task definition. Make sure database migration module is deployed.${NC}"
        exit 1
    fi
    
    # Get ECR repository URL
    ECR_REPOSITORY=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
    if [ -z "$ECR_REPOSITORY" ]; then
        echo -e "${RED}❌ Could not get ECR repository URL. Make sure storage module is deployed.${NC}"
        exit 1
    fi
    
    # Get private subnets
    PRIVATE_SUBNETS=$(terraform output -json private_subnets | jq -r '.[]' | tr '\n' ',' | sed 's/,$//')
    if [ -z "$PRIVATE_SUBNETS" ]; then
        echo -e "${RED}❌ Could not get private subnets. Make sure networking module is deployed.${NC}"
        exit 1
    fi
    
    # Get security group
    MIGRATION_SG=$(terraform output -raw ecs_security_group_id 2>/dev/null || echo "")
    if [ -z "$MIGRATION_SG" ]; then
        echo -e "${RED}❌ Could not get security group. Make sure compute module is deployed.${NC}"
        exit 1
    fi
    
    cd - > /dev/null
    
    echo -e "${GREEN}✅ ECS Cluster: $ECS_CLUSTER_NAME${NC}"
    echo -e "${GREEN}✅ Migration Task Definition: $MIGRATION_TASK_DEFINITION${NC}"
    echo -e "${GREEN}✅ ECR Repository: $ECR_REPOSITORY${NC}"
    echo -e "${GREEN}✅ Private Subnets: $PRIVATE_SUBNETS${NC}"
    echo -e "${GREEN}✅ Security Group: $MIGRATION_SG${NC}"
}

# Function to build and push rollback image
build_and_push_image() {
    local ecr_repository=$1
    
    echo -e "${YELLOW}🐳 Building rollback Docker image...${NC}"
    
    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        echo -e "${RED}❌ Backend directory not found. Please run from project root.${NC}"
        exit 1
    fi
    
    cd backend
    
    # Build the backend image
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    if ! docker build -t ${PROJECT_NAME}-backend:latest .; then
        echo -e "${RED}❌ Docker build failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Rollback image built successfully!${NC}"
    
    # Login to ECR
    echo -e "${YELLOW}🔐 Logging in to ECR...${NC}"
    if ! aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ecr_repository; then
        echo -e "${RED}❌ ECR login failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Logged in to ECR!${NC}"
    
    # Tag and push image
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    docker tag ${PROJECT_NAME}-backend:latest ${ecr_repository}:latest
    docker tag ${PROJECT_NAME}-backend:latest ${ecr_repository}:rollback-${TIMESTAMP}
    
    echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
    if ! docker push ${ecr_repository}:latest; then
        echo -e "${RED}❌ Failed to push latest image to ECR${NC}"
        exit 1
    fi
    
    if ! docker push ${ecr_repository}:rollback-${TIMESTAMP}; then
        echo -e "${RED}❌ Failed to push timestamped image to ECR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Rollback image pushed to ECR!${NC}"
    echo -e "${BLUE}ℹ️  Image version: rollback-${TIMESTAMP}${NC}"
    
    cd - > /dev/null
}

# Function to confirm rollback
confirm_rollback() {
    local target=$1
    local force=$2
    
    if [ "$force" = "true" ]; then
        echo -e "${YELLOW}🔄 Force rollback requested${NC}"
        return 0
    fi
    
    echo -e "${RED}⚠️  WARNING: This will rollback database migrations!${NC}"
    echo -e "${YELLOW}This action cannot be undone and may result in data loss.${NC}"
    echo ""
    echo -e "${BLUE}Rollback Details:${NC}"
    echo "  Target: $target"
    echo "  Environment: $ENV_NAME"
    echo ""
    echo -e "${YELLOW}Are you sure you want to proceed? (yes/NO)${NC}"
    read -p "> " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${BLUE}ℹ️  Rollback cancelled.${NC}"
        exit 0
    fi
}

# Function to run rollback task
run_rollback_task() {
    local ecs_cluster_name=$1
    local migration_task_definition=$2
    local ecr_repository=$3
    local private_subnets=$4
    local migration_sg=$5
    local target=$6
    local dry_run=$7
    
    echo -e "${YELLOW}🚀 Running database rollback task...${NC}"
    
    # Prepare rollback command
    local rollback_command
    if [ "$dry_run" = "true" ]; then
        rollback_command="alembic show $target"
        echo -e "${YELLOW}🔍 Dry run mode: Showing what would be rolled back${NC}"
    else
        rollback_command="alembic downgrade $target"
        echo -e "${YELLOW}🔄 Running rollback to: $target${NC}"
    fi
    
    # Create the command script
    local command_script="
set -e
echo '🔄 Starting database rollback process...'
cd /app

# Test database connection
echo '🔍 Testing database connection...'
python -c \"
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
try:
    db_url = f'postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_CREDENTIALS']}@{os.environ['DATABASE_HOST']}/{os.environ['DATABASE_NAME']}'
    engine = create_engine(db_url)
    conn = engine.connect()
    conn.execute('SELECT 1')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit 1
\"

# Show current migration status
echo '📊 Current migration status:'
alembic current

# Show migration history
echo '📋 Migration history:'
alembic history --verbose

# Run rollback
echo '🔄 Running rollback command: $rollback_command'
if $rollback_command; then
    echo '✅ Rollback completed successfully!'
    echo '📊 New migration status:'
    alembic current
    echo '🎉 Database rollback completed successfully!'
else
    echo '❌ Rollback failed!'
    exit 1
fi
"
    
    # Run the ECS task
    echo -e "${YELLOW}🚀 Starting ECS rollback task...${NC}"
    
    local task_arn
    task_arn=$(aws ecs run-task \
        --cluster $ecs_cluster_name \
        --task-definition $migration_task_definition \
        --network-configuration "awsvpcConfiguration={subnets=[$private_subnets],securityGroups=[$migration_sg],assignPublicIp=DISABLED}" \
        --overrides "{\"containerOverrides\":[{\"name\":\"migration\",\"image\":\"${ecr_repository}:latest\",\"command\":[\"/bin/bash\",\"-c\",\"$command_script\"]}]}" \
        --query 'tasks[0].taskArn' \
        --output text)
    
    if [ -z "$task_arn" ] || [ "$task_arn" = "None" ]; then
        echo -e "${RED}❌ Failed to start rollback task${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Rollback task started: $task_arn${NC}"
    
    # Wait for task to complete
    echo -e "${YELLOW}⏳ Waiting for rollback to complete...${NC}"
    if ! aws ecs wait tasks-stopped --cluster $ecs_cluster_name --tasks $task_arn; then
        echo -e "${RED}❌ Task did not complete within timeout${NC}"
        echo -e "${YELLOW}📋 Check task status and logs:${NC}"
        echo "  aws ecs describe-tasks --cluster $ecs_cluster_name --tasks $task_arn"
        echo "  aws logs tail /ecs/${PROJECT_NAME}-migration --follow"
        exit 1
    fi
    
    # Check task exit code
    local exit_code
    exit_code=$(aws ecs describe-tasks \
        --cluster $ecs_cluster_name \
        --tasks $task_arn \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)
    
    if [ "$exit_code" = "0" ]; then
        echo -e "${GREEN}✅ Database rollback completed successfully!${NC}"
        
        # Show task logs
        echo -e "${YELLOW}📋 Rollback logs:${NC}"
        aws logs get-log-events \
            --log-group-name "/ecs/${PROJECT_NAME}-migration" \
            --log-stream-name "ecs/migration/${task_arn##*/}" \
            --query 'events[*].message' \
            --output text
        
        echo ""
        echo -e "${GREEN}🎉 Database rollback completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Next Steps:${NC}"
        echo "  1. Verify the rollback was successful"
        echo "  2. Fix any issues that caused the migration to fail"
        echo "  3. Re-run the migration when ready"
        
    else
        echo -e "${RED}❌ Database rollback failed with exit code: $exit_code${NC}"
        
        # Show task logs
        echo -e "${YELLOW}📋 Rollback logs:${NC}"
        aws logs get-log-events \
            --log-group-name "/ecs/${PROJECT_NAME}-migration" \
            --log-stream-name "ecs/migration/${task_arn##*/}" \
            --query 'events[*].message' \
            --output text
        
        echo ""
        echo -e "${RED}⚠️  Rollback failed! Manual intervention may be required.${NC}"
        echo ""
        echo -e "${BLUE}📋 Troubleshooting:${NC}"
        echo "  1. Check the logs above for specific errors"
        echo "  2. Verify database connectivity"
        echo "  3. Check if the rollback target is valid"
        echo "  4. Consider manual database restoration if needed"
        
        exit 1
    fi
}

# Function to display summary
display_summary() {
    local target=$1
    local dry_run=$2
    
    echo ""
    if [ "$dry_run" = "true" ]; then
        echo -e "${GREEN}🎉 Rollback dry run completed!${NC}"
        echo -e "${BLUE}ℹ️  No changes were made to the database${NC}"
    else
        echo -e "${GREEN}🎉 Database rollback completed successfully!${NC}"
    fi
    echo ""
    echo -e "${BLUE}📊 Rollback Summary:${NC}"
    echo "  Target: $target"
    echo "  Dry Run: $dry_run"
    echo "  ECS Cluster: $ECS_CLUSTER_NAME"
    echo "  Task Definition: $MIGRATION_TASK_DEFINITION"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "  1. Verify the rollback was successful"
    echo "  2. Fix any issues that caused the migration to fail"
    echo "  3. Re-run the migration when ready"
}

# Main script logic
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    TARGET="head-1"
    DRY_RUN="false"
    FORCE="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --target)
                TARGET="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
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
    
    echo -e "${RED}⚠️  ResumeRepublic Database Migration Rollback${NC}"
    echo "============================================="
    echo -e "Environment: ${YELLOW}$ENV_NAME${NC}"
    echo -e "Target: ${YELLOW}$TARGET${NC}"
    echo -e "Dry Run: ${YELLOW}$DRY_RUN${NC}"
    echo -e "Force: ${YELLOW}$FORCE${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Get infrastructure details
    get_infrastructure_details "$ENV_DIR"
    
    # Confirm rollback
    confirm_rollback "$TARGET" "$FORCE"
    
    # Build and push rollback image
    build_and_push_image "$ECR_REPOSITORY"
    
    # Run rollback task
    run_rollback_task "$ECS_CLUSTER_NAME" "$MIGRATION_TASK_DEFINITION" "$ECR_REPOSITORY" "$PRIVATE_SUBNETS" "$MIGRATION_SG" "$TARGET" "$DRY_RUN"
    
    # Display summary
    display_summary "$TARGET" "$DRY_RUN"
}

# Run main function
main "$@"