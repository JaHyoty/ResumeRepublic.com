#!/bin/bash

# Database initialization script for CareerPathPro
# This script helps set up the PostgreSQL database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 CareerPathPro Database Setup${NC}"
echo "=================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not installed. Please install PostgreSQL first.${NC}"
    echo "Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "macOS: brew install postgresql"
    echo "Windows: Download from https://www.postgresql.org/download/"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running. Starting PostgreSQL...${NC}"
    if command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    elif command -v brew &> /dev/null; then
        brew services start postgresql
    else
        echo -e "${RED}❌ Please start PostgreSQL manually and try again.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Database configuration
DB_NAME="careerpathpro"
DB_USER="careerpathpro_user"
DB_PASSWORD="careerpathpro_password"

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${YELLOW}⚠️  Database '$DB_NAME' already exists.${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  Dropping existing database...${NC}"
        psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
    else
        echo -e "${BLUE}ℹ️  Using existing database.${NC}"
        exit 0
    fi
fi

# Create database and user
echo -e "${YELLOW}📦 Creating database and user...${NC}"
psql -c "CREATE DATABASE $DB_NAME;"
psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo -e "${GREEN}✅ Database and user created${NC}"

# Run schema script
echo -e "${YELLOW}📋 Running database schema...${NC}"
psql -d $DB_NAME -f database_schema.sql

echo -e "${GREEN}✅ Database schema created successfully!${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DATABASE_URL_ASYNC=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# Environment
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=$(openssl rand -hex 32)

# External Services
PARSING_SERVICE_URL=http://localhost:8001
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${BLUE}ℹ️  .env file already exists${NC}"
fi

# Test database connection
echo -e "${YELLOW}🔍 Testing database connection...${NC}"
if psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    exit 1
fi

# Show summary
echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo -e "${BLUE}📊 Database Information:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo "  Host: localhost"
echo "  Port: 5432"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "  1. Start the backend: cd backend && uvicorn app.main:app --reload"
echo "  2. Start the frontend: cd frontend && npm run dev"
echo "  3. Start the parsing service: cd parsing-service && uvicorn app.main:app --reload --port 8001"
echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo "  Connect to database: psql -h localhost -U $DB_USER -d $DB_NAME"
echo "  View tables: \dt"
echo "  View sample data: SELECT * FROM users;"
echo "  Exit psql: \q"
