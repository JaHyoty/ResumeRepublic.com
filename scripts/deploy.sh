#!/bin/bash
###############################################################################
# Deployment script for ResumeRepublic (Serverless Architecture)
#
# Usage:
#   ./scripts/deploy.sh                 # Deploy everything (Lambdas + Terraform + Frontend)
#   ./scripts/deploy.sh --backend-only  # Deploy all 3 Lambdas + Terraform (no frontend)
#   ./scripts/deploy.sh --frontend-only # Deploy only frontend to S3 + CloudFront
#   ./scripts/deploy.sh --api-only      # Build, push & update API Lambda only
#   ./scripts/deploy.sh --pdf-only      # Build, push & update PDF Lambda only
#   ./scripts/deploy.sh --scraper-only  # Build, push & update Scraper Lambda only
#   ./scripts/deploy.sh --skip-terraform # Build & update containers without terraform apply
#   ./scripts/deploy.sh --skip-frontend  # Build containers + terraform without frontend
###############################################################################

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-jahyoty-admin}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
TF_DIR="$ROOT_DIR/infrastructure/terraform/environments/production"

# Flags
BUILD_API=true
BUILD_PDF=true
BUILD_SCRAPER=true
RUN_TERRAFORM=true
BUILD_FRONTEND=true

for arg in "$@"; do
    case $arg in
        --api-only)
            BUILD_API=true; BUILD_PDF=false; BUILD_SCRAPER=false
            RUN_TERRAFORM=false; BUILD_FRONTEND=false ;;
        --pdf-only)
            BUILD_API=false; BUILD_PDF=true; BUILD_SCRAPER=false
            RUN_TERRAFORM=false; BUILD_FRONTEND=false ;;
        --scraper-only)
            BUILD_API=false; BUILD_PDF=false; BUILD_SCRAPER=true
            RUN_TERRAFORM=false; BUILD_FRONTEND=false ;;
        --backend-only)
            BUILD_API=true; BUILD_PDF=true; BUILD_SCRAPER=true
            RUN_TERRAFORM=true; BUILD_FRONTEND=false ;;
        --frontend-only)
            BUILD_API=false; BUILD_PDF=false; BUILD_SCRAPER=false
            RUN_TERRAFORM=false; BUILD_FRONTEND=true ;;
        --skip-terraform)
            RUN_TERRAFORM=false ;;
        --skip-frontend)
            BUILD_FRONTEND=false ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  (no flags)         Deploy everything (all 3 Lambdas + Terraform + Frontend)"
            echo "  --backend-only     Deploy all 3 Lambdas and Terraform (skip frontend)"
            echo "  --frontend-only    Deploy only frontend (skip container builds & Terraform)"
            echo "  --api-only         Build, push & update API Lambda only"
            echo "  --pdf-only         Build, push & update PDF Lambda only"
            echo "  --scraper-only     Build, push & update Scraper Lambda only"
            echo "  --skip-terraform   Skip running terraform apply"
            echo "  --skip-frontend    Skip building and deploying frontend"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use $0 --help for usage details"
            exit 1
            ;;
    esac
done

echo "============================================="
echo "  ResumeRepublic Deployment"
echo "  Profile: $AWS_PROFILE"
echo "  Region:  $REGION"
echo "============================================="

# Detect Account ID
ACCOUNT_ID=$(aws --profile "$AWS_PROFILE" sts get-caller-identity --query Account --output text 2>/dev/null || echo "637423509675")
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Read Terraform outputs if needed
get_tf_output() {
    local key="$1"
    (cd "$TF_DIR" && aws --profile "$AWS_PROFILE" terraform output -raw "$key" 2>/dev/null) || echo ""
}

# --- Step 1: ECR Login & Container Builds ---
if $BUILD_API || $BUILD_PDF || $BUILD_SCRAPER; then
    echo ""
    echo "=== 1. Logging into Amazon ECR ==="
    aws --profile "$AWS_PROFILE" ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "$ECR_BASE"
fi

if $BUILD_API; then
    echo ""
    echo "=== Building API Lambda Image (resumerepublic-backend) ==="
    docker build -t resumerepublic-backend -f "$BACKEND_DIR/Dockerfile" "$BACKEND_DIR"
    docker tag resumerepublic-backend:latest "${ECR_BASE}/resumerepublic-backend:latest"
    echo "Pushing API Lambda Image..."
    docker push "${ECR_BASE}/resumerepublic-backend:latest"
    
    echo "Updating resumerepublic-api Lambda..."
    aws --profile "$AWS_PROFILE" lambda update-function-code \
        --function-name resumerepublic-api \
        --image-uri "${ECR_BASE}/resumerepublic-backend:latest" >/dev/null
    aws --profile "$AWS_PROFILE" lambda wait function-updated \
        --function-name resumerepublic-api
    echo "resumerepublic-api Lambda updated successfully."
fi

if $BUILD_PDF; then
    echo ""
    echo "=== Building PDF Lambda Image (resumerepublic-pdf) ==="
    docker build -t resumerepublic-pdf -f "$BACKEND_DIR/Dockerfile.pdf" "$BACKEND_DIR"
    docker tag resumerepublic-pdf:latest "${ECR_BASE}/resumerepublic-pdf:latest"
    echo "Pushing PDF Lambda Image..."
    docker push "${ECR_BASE}/resumerepublic-pdf:latest"
    
    echo "Updating resumerepublic-pdf Lambda..."
    aws --profile "$AWS_PROFILE" lambda update-function-code \
        --function-name resumerepublic-pdf \
        --image-uri "${ECR_BASE}/resumerepublic-pdf:latest" >/dev/null
    aws --profile "$AWS_PROFILE" lambda wait function-updated \
        --function-name resumerepublic-pdf
    echo "resumerepublic-pdf Lambda updated successfully."
fi

if $BUILD_SCRAPER; then
    echo ""
    echo "=== Building Scraper Lambda Image (resumerepublic-scraper) ==="
    docker build -t resumerepublic-scraper -f "$BACKEND_DIR/Dockerfile.scraper" "$BACKEND_DIR"
    docker tag resumerepublic-scraper:latest "${ECR_BASE}/resumerepublic-scraper:latest"
    echo "Pushing Scraper Lambda Image..."
    docker push "${ECR_BASE}/resumerepublic-scraper:latest"
    
    echo "Updating resumerepublic-scraper Lambda..."
    aws --profile "$AWS_PROFILE" lambda update-function-code \
        --function-name resumerepublic-scraper \
        --image-uri "${ECR_BASE}/resumerepublic-scraper:latest" >/dev/null
    aws --profile "$AWS_PROFILE" lambda wait function-updated \
        --function-name resumerepublic-scraper
    echo "resumerepublic-scraper Lambda updated successfully."
fi

# --- Step 2: Terraform Infrastructure Apply ---
if $RUN_TERRAFORM; then
    echo ""
    echo "=== 2. Applying Terraform Infrastructure ==="
    cd "$TF_DIR"
    AWS_PROFILE="$AWS_PROFILE" terraform apply -auto-approve
    cd "$ROOT_DIR"
fi

# --- Step 3: Frontend Build & Deployment ---
if $BUILD_FRONTEND; then
    echo ""
    echo "=== 3. Deploying Frontend ==="
    
    # Retrieve outputs from Terraform
    API_URL=$(get_tf_output "api_gateway_endpoint")
    S3_BUCKET=$(get_tf_output "s3_bucket_name")
    DISTRIBUTION_ID=$(get_tf_output "cloudfront_distribution_id")

    if [ -z "$API_URL" ]; then
        API_URL="https://xem0v9bjlk.execute-api.us-east-1.amazonaws.com"
    fi
    if [ -z "$S3_BUCKET" ]; then
        S3_BUCKET="resumerepublic-production-frontend-7jdtmx2y"
    fi
    if [ -z "$DISTRIBUTION_ID" ]; then
        DISTRIBUTION_ID="EGZO4SXGU8GGJ"
    fi

    echo "Building frontend with API URL: $API_URL"
    cd "$FRONTEND_DIR"
    npm ci
    API_BASE_URL="$API_URL" npm run build
    cd "$ROOT_DIR"

    echo "Syncing frontend bundle to s3://$S3_BUCKET..."
    aws --profile "$AWS_PROFILE" s3 sync "$FRONTEND_DIR/dist/" "s3://${S3_BUCKET}" --delete

    echo "Invalidating CloudFront cache (Distribution: $DISTRIBUTION_ID)..."
    aws --profile "$AWS_PROFILE" cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*" >/dev/null
    echo "CloudFront cache invalidation created."
fi

echo ""
echo "============================================="
echo "  Deployment Complete! 🎉"
echo "============================================="
