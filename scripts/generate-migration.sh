#!/bin/bash

# Generate Alembic Migration from Models
# This script generates a fresh migration using Alembic autogenerate within ECS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗄️  Generating Alembic Migration from Models${NC}"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "backend/alembic.ini" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Backend directory not found.${NC}"
    exit 1
fi

# Get migration message
MIGRATION_MESSAGE=${1:-"Update database schema"}

echo -e "${YELLOW}📊 Generating migration: $MIGRATION_MESSAGE${NC}"

# Use the ECS-based Alembic command runner
echo -e "${YELLOW}🔧 Creating migration using ECS...${NC}"
./scripts/run-alembic-command.sh "revision -m '$MIGRATION_MESSAGE'"

echo ""
echo -e "${GREEN}🎉 Migration generation completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "  1. Review the generated migration file in backend/alembic/versions/"
echo "  2. Edit the migration if needed"
echo "  3. Run the migration using: ./scripts/run-database-migration.sh"
echo "  4. Or check migration status: ./scripts/run-alembic-command.sh current"
