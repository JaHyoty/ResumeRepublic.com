#!/bin/bash

# Database Migration Runner for ResumeRepublic
# Runs database migrations using Alembic in ECS with automatic rollback on failure
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
    echo "  --target TARGET      Migration target (default: head)"
    echo "  --dry-run            Show what would be migrated without executing"
    echo "  --no-rollback        Disable automatic rollback on failure"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Run migrations to latest"
    echo "  $0 --target head-1           Rollback one migration"
    echo "  $0 --dry-run                 Show what would be migrated"
    echo "  $0 --environment prod        Run on production"
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
    
    # Get ECS task role for migration
    ECS_TASK_ROLE_ARN=$(terraform output -raw ecs_task_role_arn 2>/dev/null || echo "")
    if [ -z "$ECS_TASK_ROLE_ARN" ]; then
        echo -e "${RED}❌ Could not get ECS task role ARN. Make sure infrastructure is deployed.${NC}"
        exit 1
    fi
    
    # Get ECS execution role for migration
    ECS_EXECUTION_ROLE_ARN=$(terraform output -raw ecs_execution_role_arn 2>/dev/null || echo "")
    if [ -z "$ECS_EXECUTION_ROLE_ARN" ]; then
        echo -e "${RED}❌ Could not get ECS execution role ARN. Make sure infrastructure is deployed.${NC}"
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
    echo -e "${GREEN}✅ ECS Task Role: $ECS_TASK_ROLE_ARN${NC}"
    echo -e "${GREEN}✅ ECS Execution Role: $ECS_EXECUTION_ROLE_ARN${NC}"
    echo -e "${GREEN}✅ ECR Repository: $ECR_REPOSITORY${NC}"
    echo -e "${GREEN}✅ Private Subnets: $PRIVATE_SUBNETS${NC}"
    echo -e "${GREEN}✅ Security Group: $MIGRATION_SG${NC}"
}

# Function to build and push migration image
build_and_push_image() {
    local ecr_repository=$1
    
    echo -e "${YELLOW}🐳 Building migration Docker image...${NC}"
    
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
    
    echo -e "${GREEN}✅ Migration image built successfully!${NC}"
    
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
    docker tag ${PROJECT_NAME}-backend:latest ${ecr_repository}:migration-${TIMESTAMP}
    
    echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
    if ! docker push ${ecr_repository}:latest; then
        echo -e "${RED}❌ Failed to push latest image to ECR${NC}"
        exit 1
    fi
    
    if ! docker push ${ecr_repository}:migration-${TIMESTAMP}; then
        echo -e "${RED}❌ Failed to push timestamped image to ECR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Migration image pushed to ECR!${NC}"
    echo -e "${BLUE}ℹ️  Image version: migration-${TIMESTAMP}${NC}"
    
    cd - > /dev/null
}

# Function to run migration task
run_migration_task() {
    local ecs_cluster_name=$1
    local ecs_task_role_arn=$2
    local ecs_execution_role_arn=$3
    local ecr_repository=$4
    local private_subnets=$5
    local migration_sg=$6
    local target=$7
    local dry_run=$8
    local no_rollback=$9
    
    echo -e "${YELLOW}🚀 Running database migration task...${NC}"
    
    # Prepare migration command
    local migration_command
    if [ "$dry_run" = "true" ]; then
        migration_command="alembic show $target"
        echo -e "${YELLOW}🔍 Dry run mode: Showing what would be migrated${NC}"
    else
        migration_command="alembic upgrade $target"
        echo -e "${YELLOW}🔄 Running migration to: $target${NC}"
    fi
    
    # Prepare rollback command
    local rollback_command=""
    if [ "$no_rollback" = "false" ] && [ "$dry_run" = "false" ]; then
        rollback_command="alembic downgrade -1"
    fi
    
    # Prepare migration commands
    local migration_cmd
    if [ "$dry_run" = "true" ]; then
        migration_cmd="alembic show $target"
    else
        migration_cmd="alembic upgrade $target"
    fi
    
    # Create task definition for migration
    echo -e "${YELLOW}📋 Creating migration task definition...${NC}"
    
    # Get AWS account ID
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    
    # Create task definition JSON file
    local task_definition_file="/tmp/migration-task-definition.json"
    cat > "$task_definition_file" <<EOF
{
    "family": "${PROJECT_NAME}-migration-$(date +%s)",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "${ecs_execution_role_arn}",
    "taskRoleArn": "${ecs_task_role_arn}",
    "containerDefinitions": [
        {
            "name": "migration",
            "image": "${ecr_repository}:latest",
            "essential": true,
            "command": ["/bin/bash", "-c", "cd /app && python -c 'import sys; sys.path.append(\"/app\"); from app.core.database import _get_database_url, _get_connection_args; from sqlalchemy import create_engine, text; engine = create_engine(_get_database_url(), connect_args=_get_connection_args()); conn = engine.connect(); conn.execute(text(\"SELECT 1\")); print(\"Database connection successful\"); conn.close()' && alembic current && $migration_cmd && echo 'Migration completed successfully'"],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/${PROJECT_NAME}-${ENV_NAME}-backend",
                    "awslogs-region": "${AWS_REGION}",
                    "awslogs-stream-prefix": "migration"
                }
            },
            "environment": [
                {"name": "ENVIRONMENT", "value": "${ENV_NAME}"},
                {"name": "AWS_REGION", "value": "${AWS_REGION}"},
                {"name": "DATABASE_PORT", "value": "5432"},
                {"name": "USE_IAM_DATABASE_AUTH", "value": "false"},
                {"name": "DATABASE_CREDENTIALS_CACHE_TTL", "value": "300"},
                {"name": "DATABASE_CREDENTIALS_SECRET_ARN", "value": "arn:aws:secretsmanager:${AWS_REGION}:${aws_account_id}:secret:rds!db-d13de373-8f34-44fa-88fe-01086d8ed1bb-Sl2naV"}
            ],
            "secrets": [
                {"name": "DATABASE_HOST", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${aws_account_id}:parameter/${PROJECT_NAME}/${ENV_NAME}/database/host"},
                {"name": "DATABASE_NAME", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${aws_account_id}:parameter/${PROJECT_NAME}/${ENV_NAME}/database/name"},
                {"name": "DATABASE_USER", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${aws_account_id}:parameter/${PROJECT_NAME}/${ENV_NAME}/database/user"}
            ]
        }
    ]
}
EOF
    
    # Register the task definition
    local task_definition_arn
    task_definition_arn=$(aws ecs register-task-definition --cli-input-json file://"$task_definition_file" --query 'taskDefinition.taskDefinitionArn' --output text)
    
    # Clean up temporary file
    rm -f "$task_definition_file"
    
    if [ -z "$task_definition_arn" ] || [ "$task_definition_arn" = "None" ]; then
        echo -e "${RED}❌ Failed to register migration task definition${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Migration task definition created: $task_definition_arn${NC}"
    
    # Run the ECS task
    echo -e "${YELLOW}🚀 Starting ECS migration task...${NC}"
    
    local task_arn
    task_arn=$(aws ecs run-task \
        --cluster $ecs_cluster_name \
        --task-definition $task_definition_arn \
        --network-configuration "awsvpcConfiguration={subnets=[$private_subnets],securityGroups=[$migration_sg],assignPublicIp=DISABLED}" \
        --query 'tasks[0].taskArn' \
        --output text)
    
    if [ -z "$task_arn" ] || [ "$task_arn" = "None" ]; then
        echo -e "${RED}❌ Failed to start migration task${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Migration task started: $task_arn${NC}"
    
    # Wait for task to complete
    echo -e "${YELLOW}⏳ Waiting for migration to complete...${NC}"
    if ! aws ecs wait tasks-stopped --cluster $ecs_cluster_name --tasks $task_arn; then
        echo -e "${RED}❌ Task did not complete within timeout${NC}"
        echo -e "${YELLOW}📋 Check task status and logs:${NC}"
        echo "  aws ecs describe-tasks --cluster $ecs_cluster_name --tasks $task_arn"
        echo "  aws logs tail /ecs/${PROJECT_NAME}-${ENV_NAME}-backend --follow"
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
        echo -e "${GREEN}✅ Database migration completed successfully!${NC}"
        
        # Show task logs
        echo -e "${YELLOW}📋 Migration logs:${NC}"
        aws logs get-log-events \
            --log-group-name "/ecs/${PROJECT_NAME}-${ENV_NAME}-backend" \
            --log-stream-name "migration/${task_arn##*/}" \
            --query 'events[*].message' \
            --output text
        
        echo ""
        echo -e "${GREEN}🎉 Database migration completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Next Steps:${NC}"
        echo "  1. Deploy your backend application"
        echo "  2. Test database connectivity from your backend"
        echo "  3. Verify schema changes were applied correctly"
        
    else
        echo -e "${RED}❌ Database migration failed with exit code: $exit_code${NC}"
        
        # Show task logs
        echo -e "${YELLOW}📋 Migration logs:${NC}"
        aws logs get-log-events \
            --log-group-name "/ecs/${PROJECT_NAME}-${ENV_NAME}-backend" \
            --log-stream-name "migration/${task_arn##*/}" \
            --query 'events[*].message' \
            --output text
        
        echo ""
        echo -e "${RED}⚠️  Migration failed!${NC}"
        echo ""
        echo -e "${BLUE}📋 Troubleshooting:${NC}"
        echo "  1. Check the logs above for specific errors"
        echo "  2. Verify database connectivity"
        echo "  3. Check if all required parameters are set in Parameter Store"
        echo "  4. Run rollback if necessary: ./scripts/rollback-database-migration.sh"
        
        exit 1
    fi
}

# Function to display summary
display_summary() {
    local target=$1
    local dry_run=$2
    
    echo ""
    if [ "$dry_run" = "true" ]; then
        echo -e "${GREEN}🎉 Migration dry run completed!${NC}"
        echo -e "${BLUE}ℹ️  No changes were made to the database${NC}"
    else
        echo -e "${GREEN}🎉 Database migration completed successfully!${NC}"
    fi
    echo ""
    echo -e "${BLUE}📊 Migration Summary:${NC}"
    echo "  Target: $target"
    echo "  Dry Run: $dry_run"
    echo "  ECS Cluster: $ECS_CLUSTER_NAME"
    echo "  ECS Task Role: $ECS_TASK_ROLE_ARN"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "  1. Deploy backend: ./scripts/deploy-backend.sh"
    echo "  2. Deploy frontend: ./scripts/deploy-frontend.sh"
    echo "  3. Test your application"
}

# Main script logic
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    TARGET="head"
    DRY_RUN="false"
    NO_ROLLBACK="false"
    
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
            --no-rollback)
                NO_ROLLBACK="true"
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
    
    echo -e "${BLUE}🗄️  ResumeRepublic Database Migration${NC}"
    echo "====================================="
    echo -e "Environment: ${YELLOW}$ENV_NAME${NC}"
    echo -e "Target: ${YELLOW}$TARGET${NC}"
    echo -e "Dry Run: ${YELLOW}$DRY_RUN${NC}"
    echo -e "No Rollback: ${YELLOW}$NO_ROLLBACK${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Get infrastructure details
    get_infrastructure_details "$ENV_DIR"
    
    # Build and push migration image
    build_and_push_image "$ECR_REPOSITORY"
    
    # Run migration task
    run_migration_task "$ECS_CLUSTER_NAME" "$ECS_TASK_ROLE_ARN" "$ECS_EXECUTION_ROLE_ARN" "$ECR_REPOSITORY" "$PRIVATE_SUBNETS" "$MIGRATION_SG" "$TARGET" "$DRY_RUN" "$NO_ROLLBACK"
    
    # Display summary
    display_summary "$TARGET" "$DRY_RUN"
}

# Run main function
main "$@"