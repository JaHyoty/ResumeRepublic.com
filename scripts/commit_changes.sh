#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  Staging and Committing in Logical Chunks"
echo "============================================="

# 1. Infrastructure Migration
echo ""
echo "=== 1. Committing Infrastructure Migration ==="
git add infrastructure/ scripts/ .gitignore
git commit -m "feat(infra): migrate infrastructure to serverless (API Gateway, Lambda, DynamoDB) and archive legacy VPC/ECS modules"

# 2. Backend Core, Handlers & DynamoDB
echo ""
echo "=== 2. Committing Backend DynamoDB & Lambda Handlers ==="
git add backend/Dockerfile \
        backend/Dockerfile.pdf \
        backend/Dockerfile.scraper \
        backend/lambda_handler.py \
        backend/pdf_handler.py \
        backend/scraper_handler.py \
        backend/requirements*.txt \
        backend/alembic/ \
        backend/alembic.ini \
        backend/app/core/ \
        backend/app/models/ \
        backend/app/api/ \
        backend/app/main.py \
        backend/app/services/webhook_service.py \
        backend/app/services/s3_service.py \
        backend/app/services/job_posting_heuristic_extractor.py \
        backend/app/services/job_posting_parser.py \
        backend/app/services/job_posting_web_scraper.py
git commit -m "feat(backend): migrate from SQLAlchemy/PostgreSQL to DynamoDB single-table design with multi-worker Lambdas"

# 3. Resume Generation, LaTeX & Publications
echo ""
echo "=== 3. Committing Resume Generation & LaTeX Updates ==="
git add backend/app/schemas/ \
        backend/app/templates/ResumeTemplate1.tex \
        backend/app/services/latex_service.py \
        backend/app/services/llm_service.py \
        backend/app/services/resume_generation_service.py \
        backend/app/utils/template_utils.py
git commit -m "fix(resume): enforce \resumeSubheading formatting for publications and fix certification date schemas"

# 4. Frontend Fixes
echo ""
echo "=== 4. Committing Frontend Fixes ==="
git add frontend/
git commit -m "fix(frontend): update API base URL configuration, webhook listener, and certification form validation"

# 5. Documentation & CI/CD cleanup
echo ""
echo "=== 5. Committing Documentation & Cleanup ==="
git add README.md
git add -u .github/ 2>/dev/null || true
git commit -m "docs: update README for serverless architecture, remove GitHub Actions in favor of deploy script"

# Clean up this temporary helper script before pushing
rm -f scripts/commit_changes.sh

# 6. Push to remote
echo ""
echo "=== 6. Pushing to origin main ==="
git push origin main

echo ""
echo "============================================="
echo "  All changes committed and pushed! 🎉"
echo "============================================="
