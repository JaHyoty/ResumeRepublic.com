#!/bin/bash

# Database setup script for CareerPathPro
# This script sets up the PostgreSQL database with the required schema

set -e

echo "🚀 Setting up CareerPathPro Database..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp env.example .env
    echo -e "${YELLOW}📝 Please edit .env file with your configuration before continuing.${NC}"
    echo -e "${YELLOW}   Press Enter when ready to continue...${NC}"
    read
fi

# Start database services
echo -e "${YELLOW}🐳 Starting database services...${NC}"
cd infrastructure/docker
docker-compose up -d postgres redis

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
sleep 10

# Check if database is ready
until docker-compose exec postgres pg_isready -U user -d careerpathpro; do
    echo -e "${YELLOW}⏳ Waiting for database...${NC}"
    sleep 2
done

echo -e "${GREEN}✅ Database is ready!${NC}"

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
cd ../../backend
pip install -r requirements.txt

# Run database migrations
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
alembic upgrade head

# Create initial data (optional)
echo -e "${YELLOW}🌱 Creating initial data...${NC}"
python scripts/init_db.py

echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo -e "${GREEN}📊 Database URL: postgresql://user:password@localhost:5432/careerpathpro${NC}"
echo -e "${GREEN}🔗 Adminer: http://localhost:8080 (user: user, password: password, server: postgres)${NC}"

# Show next steps
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "   1. Start the backend: cd backend && uvicorn app.main:app --reload"
echo -e "   2. Start the frontend: cd frontend && npm run dev"
echo -e "   3. Start the parsing service: cd parsing-service && uvicorn app.main:app --reload --port 8001"
