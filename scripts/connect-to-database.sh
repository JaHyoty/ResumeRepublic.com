#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
PROJECT_NAME="resumerepublic"
LOCAL_PORT=${2:-5432}

echo -e "${BLUE}🚀 Connecting to database via jump host for $ENVIRONMENT${NC}"

# Get jump host instance ID
echo -e "${YELLOW}📋 Getting jump host instance ID...${NC}"
SCRIPT_DIR="$(dirname "$0")"
TERRAFORM_DIR="$(cd "$SCRIPT_DIR/../infrastructure/terraform/environments/$ENVIRONMENT" && pwd)"
cd "$TERRAFORM_DIR"
INSTANCE_ID=$(terraform output -raw jump_host_instance_id 2>/dev/null || echo "")

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}❌ Could not get jump host instance ID. Make sure the jump host is deployed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Jump host instance ID: $INSTANCE_ID${NC}"

# Get database host from SSM Parameter Store
echo -e "${YELLOW}📋 Getting database host...${NC}"
DB_HOST=$(aws ssm get-parameter --name "/${PROJECT_NAME}/${ENVIRONMENT}/database/host" --query 'Parameter.Value' --output text 2>/dev/null || echo "")

if [ -z "$DB_HOST" ]; then
    echo -e "${RED}❌ Could not get database host from SSM Parameter Store${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database host: $DB_HOST${NC}"

# Get database credentials
echo -e "${YELLOW}📋 Getting database credentials...${NC}"
SECRET_ARN=$(terraform output -raw db_master_user_secret_arn 2>/dev/null || echo "")

if [ -z "$SECRET_ARN" ]; then
    echo -e "${RED}❌ Could not get database secret ARN${NC}"
    exit 1
fi

DB_CREDS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --query SecretString --output text)
DB_USER=$(echo "$DB_CREDS" | jq -r '.username')
DB_NAME=$(echo "$DB_CREDS" | jq -r '.dbname')

echo -e "${GREEN}✅ Database user: $DB_USER${NC}"
echo -e "${GREEN}✅ Database name: $DB_NAME${NC}"

cd ../../../

# Check if AWS CLI Session Manager plugin is installed
if ! command -v session-manager-plugin &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI Session Manager plugin not found.${NC}"
    echo -e "${YELLOW}Please install it from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html${NC}"
    exit 1
fi

# Start port forwarding session
echo -e "${YELLOW}🔗 Starting port forwarding session...${NC}"
echo -e "${BLUE}This will forward localhost:$LOCAL_PORT to $DB_HOST:5432${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the session${NC}"
echo ""

# Create connection info file
cat > /tmp/db-connection-info.txt << EOF
Database Connection Info:
- Local port: $LOCAL_PORT
- Remote host: $DB_HOST:5432
- Username: $DB_USER
- Database: $DB_NAME

To connect with psql:
psql -h localhost -p $LOCAL_PORT -U $DB_USER -d $DB_NAME

To connect with other tools:
Host: localhost
Port: $LOCAL_PORT
Username: $DB_USER
Database: $DB_NAME
EOF

echo -e "${GREEN}📋 Connection info saved to /tmp/db-connection-info.txt${NC}"
echo ""

# Start the session
aws ssm start-session \
    --target "$INSTANCE_ID" \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "{\"portNumber\":[\"5432\"],\"localPortNumber\":[\"$LOCAL_PORT\"],\"host\":[\"$DB_HOST\"]}"
