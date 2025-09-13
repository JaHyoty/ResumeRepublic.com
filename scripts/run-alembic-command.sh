#!/bin/bash

# Run Alembic Commands in ECS
# This script runs any Alembic command within the ECS task that has database connectivity

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

echo -e "${BLUE}🗄️  ResumeRepublic Alembic Command Runner${NC}"
echo "======================================="

# Check if command is provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <alembic_command>${NC}"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 current                    # Show current migration"
    echo "  $0 history                    # Show migration history"
    echo "  $0 upgrade head               # Upgrade to latest"
    echo "  $0 downgrade -1               # Downgrade one step"
    echo "  $0 revision -m 'Add table'    # Create new migration"
    echo "  $0 show <revision>            # Show specific migration"
    echo ""
    exit 1
fi

ALEMBIC_COMMAND="$*"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Check if infrastructure is deployed
if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    echo -e "${RED}❌ Infrastructure not deployed. Please run './scripts/deploy-infrastructure-modular.sh' first.${NC}"
    exit 1
fi

# Get ECS cluster and task details from Terraform
echo -e "${YELLOW}📊 Getting ECS details...${NC}"
cd $TERRAFORM_DIR

ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")
MIGRATION_TASK_DEFINITION=$(terraform output -raw migration_task_definition_arn 2>/dev/null || echo "")
ECR_REPOSITORY=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")

if [ -z "$ECS_CLUSTER_NAME" ] || [ -z "$MIGRATION_TASK_DEFINITION" ]; then
    echo -e "${RED}❌ Could not get ECS details. Make sure database migration module is deployed.${NC}"
    exit 1
fi

if [ -z "$ECR_REPOSITORY" ]; then
    echo -e "${RED}❌ Could not get ECR repository. Make sure storage module is deployed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ ECS Cluster: $ECS_CLUSTER_NAME${NC}"
echo -e "${GREEN}✅ Migration Task Definition: $MIGRATION_TASK_DEFINITION${NC}"
echo -e "${GREEN}✅ ECR Repository: $ECR_REPOSITORY${NC}"

cd - > /dev/null

# Get the backend image from ECR
echo -e "${YELLOW}🐳 Getting backend Docker image...${NC}"
MIGRATION_IMAGE="${ECR_REPOSITORY}:latest"

# Check if image exists in ECR
if ! aws ecr describe-images --repository-name $(echo $ECR_REPOSITORY | cut -d'/' -f2) --image-ids imageTag=latest > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Image not found in ECR. Building and pushing...${NC}"
    cd backend
    docker build -t ${PROJECT_NAME}-backend:latest .
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY
    docker tag ${PROJECT_NAME}-backend:latest ${ECR_REPOSITORY}:latest
    docker push ${ECR_REPOSITORY}:latest
    cd - > /dev/null
fi

# Get subnet and security group details
echo -e "${YELLOW}🔧 Getting network configuration...${NC}"
cd $TERRAFORM_DIR
PRIVATE_SUBNETS=$(terraform output -json private_subnets | jq -r '.[]' | tr '\n' ',' | sed 's/,$//')
MIGRATION_SG=$(terraform output -raw ecs_security_group_id 2>/dev/null || echo "")

if [ -z "$MIGRATION_SG" ]; then
    echo -e "${YELLOW}⚠️  Migration security group not found. Using ECS task security group.${NC}"
    MIGRATION_SG=$(terraform output -raw ecs_security_group_id 2>/dev/null || echo "")
fi

cd - > /dev/null

# Run the ECS task with the Alembic command
echo -e "${YELLOW}🚀 Running Alembic command: $ALEMBIC_COMMAND${NC}"

# Escape the command for JSON
ESCAPED_COMMAND=$(echo "$ALEMBIC_COMMAND" | sed 's/"/\\"/g')

TASK_ARN=$(aws ecs run-task \
    --cluster $ECS_CLUSTER_NAME \
    --task-definition $MIGRATION_TASK_DEFINITION \
    --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$MIGRATION_SG],assignPublicIp=DISABLED}" \
    --overrides "{\"containerOverrides\":[{\"name\":\"migration\",\"image\":\"$MIGRATION_IMAGE\",\"command\":[\"/bin/bash\",\"-c\",\"set -e && echo '🗄️  Running Alembic command: $ALEMBIC_COMMAND' && cd /app && python -c \\\"import os; from sqlalchemy import create_engine; from sqlalchemy.exc import OperationalError; db_url = f'postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_CREDENTIALS']}@{os.environ['DATABASE_HOST']}/{os.environ['DATABASE_NAME']}'; engine = create_engine(db_url); conn = engine.connect(); conn.execute('SELECT 1'); print('✅ Database connection successful')\\\" && echo '🔧 Running command: alembic $ALEMBIC_COMMAND' && alembic $ALEMBIC_COMMAND && echo '✅ Alembic command completed successfully!' || echo '❌ Alembic command failed!' && exit 1\"]}]}" \
    --query 'tasks[0].taskArn' \
    --output text)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" = "None" ]; then
    echo -e "${RED}❌ Failed to start Alembic command task.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Alembic command task started: $TASK_ARN${NC}"

# Wait for task to complete
echo -e "${YELLOW}⏳ Waiting for command to complete...${NC}"
aws ecs wait tasks-stopped --cluster $ECS_CLUSTER_NAME --tasks $TASK_ARN

# Check task exit code
EXIT_CODE=$(aws ecs describe-tasks \
    --cluster $ECS_CLUSTER_NAME \
    --tasks $TASK_ARN \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

if [ "$EXIT_CODE" = "0" ]; then
    echo -e "${GREEN}✅ Alembic command completed successfully!${NC}"
    
    # Show task logs
    echo -e "${YELLOW}📋 Command output:${NC}"
    aws logs get-log-events \
        --log-group-name "/ecs/${PROJECT_NAME}-migration" \
        --log-stream-name "ecs/migration/${TASK_ARN##*/}" \
        --query 'events[*].message' \
        --output text
    
    echo ""
    echo -e "${GREEN}🎉 Alembic command completed successfully!${NC}"
    
else
    echo -e "${RED}❌ Alembic command failed with exit code: $EXIT_CODE${NC}"
    
    # Show task logs
    echo -e "${YELLOW}📋 Command output:${NC}"
    aws logs get-log-events \
        --log-group-name "/ecs/${PROJECT_NAME}-migration" \
        --log-stream-name "ecs/migration/${TASK_ARN##*/}" \
        --query 'events[*].message' \
        --output text
    
    echo ""
    echo -e "${RED}⚠️  Alembic command failed!${NC}"
    
    exit 1
fi
