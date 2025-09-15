#!/bin/bash

# ResumeRepublic Deployment Orchestrator
# Provides a menu-driven interface for deploying the ResumeRepublic application
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ResumeRepublic Deployment Orchestrator${NC}"
echo "============================================="

# Check if scripts exist
if [ ! -f "scripts/deploy-infrastructure.sh" ] || [ ! -f "scripts/deploy-frontend.sh" ] || [ ! -f "scripts/deploy-backend.sh" ]; then
    echo -e "${RED}❌ Deployment scripts not found. Please run from project root.${NC}"
    exit 1
fi

# Ask for environment
echo -e "${YELLOW}Which environment would you like to deploy?${NC}"
echo "1) Development"
echo "2) Production"
echo ""
read -p "Enter your choice (1-2): " env_choice

case $env_choice in
    1)
        ENVIRONMENT="dev"
        ENV_NAME="development"
        ENV_DIR="infrastructure/terraform/environments/development"
        ;;
    2)
        ENVIRONMENT="prod"
        ENV_NAME="production"
        ENV_DIR="infrastructure/terraform/environments/production"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

# Check if environment configuration exists
if [ ! -f "$ENV_DIR/terraform.tfvars" ]; then
    echo -e "${YELLOW}⚠️  No terraform.tfvars found for $ENV_NAME environment.${NC}"
    echo -e "${YELLOW}📝 Please copy the example file and configure it:${NC}"
    echo "  cp $ENV_DIR/terraform.tfvars.example $ENV_DIR/terraform.tfvars"
    echo "  # Edit $ENV_DIR/terraform.tfvars with your values"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Deployment cancelled. Please configure your environment first.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}What would you like to deploy?${NC}"
echo "1) Infrastructure only"
echo "2) Backend only (requires infrastructure)"
echo "3) Frontend only (requires infrastructure)"
echo "4) Backend + Frontend (requires infrastructure)"
echo "5) Destroy infrastructure"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}🏗️  Deploying $ENV_NAME infrastructure...${NC}"
        ./scripts/deploy-infrastructure.sh $ENVIRONMENT apply
        ;;
    2)
        echo -e "${BLUE}⚙️  Deploying backend...${NC}"
        ./scripts/deploy-backend.sh --environment $ENVIRONMENT
        ;;
    3)
        echo -e "${BLUE}🎨 Deploying frontend...${NC}"
        ./scripts/deploy-frontend.sh --environment $ENVIRONMENT
        ;;
    4)
        echo -e "${BLUE}⚙️  Deploying backend...${NC}"
        ./scripts/deploy-backend.sh --environment $ENVIRONMENT --no-build
        echo ""
        echo -e "${BLUE}🎨 Deploying frontend...${NC}"
        ./scripts/deploy-frontend.sh --environment $ENVIRONMENT
        ;;
    5)
        echo -e "${RED}⚠️  WARNING: This will destroy the $ENV_NAME infrastructure!${NC}"
        echo -e "${YELLOW}This action cannot be undone and will delete all resources and data.${NC}"
        echo -e "${YELLOW}Are you sure? Type 'yes' to confirm:${NC}"
        read -p "> " -r
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo -e "${BLUE}🗑️  Destroying $ENV_NAME infrastructure...${NC}"
            ./scripts/deploy-infrastructure.sh $ENVIRONMENT destroy
        else
            echo -e "${BLUE}ℹ️  Destruction cancelled.${NC}"
            exit 0
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Operation completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Quick Commands:${NC}"
echo "  Deploy dev infrastructure:  ./scripts/deploy-infrastructure.sh dev apply"
echo "  Deploy prod infrastructure: ./scripts/deploy-infrastructure.sh prod apply"
echo "  Deploy backend:             ./scripts/deploy-backend.sh --environment prod"
echo "  Deploy frontend:            ./scripts/deploy-frontend.sh --environment prod"
echo "  Run migrations:             ./scripts/run-database-migration.sh --environment prod"
echo "  Validate deployment:        ./scripts/validate-deployment.sh --check-all"
echo "  Full deployment:            ./deploy.sh"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "  Deployment guide:           DEPLOYMENT_GUIDE.md"
echo "  Quick reference:            DEPLOYMENT_QUICK_REFERENCE.md"
echo ""
echo -e "${BLUE}🔧 Configuration:${NC}"
echo "  Dev config:                 infrastructure/terraform/environments/development/terraform.tfvars"
echo "  Prod config:                infrastructure/terraform/environments/production/terraform.tfvars"