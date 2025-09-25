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

# Calculate project root and backend directory before changing directories
SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Get jump host instance ID
echo -e "${YELLOW}📋 Getting jump host instance ID...${NC}"
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
DB_PASSWORD=$(echo "$DB_CREDS" | jq -r '.password')

# Get database name from Terraform output
echo -e "${YELLOW}📋 Getting database name from Terraform...${NC}"
DB_NAME=$(terraform output -raw db_name 2>/dev/null || echo "")
if [ -z "$DB_NAME" ]; then
    echo -e "${RED}❌ Could not get database name from Terraform${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database user: $DB_USER${NC}"
echo -e "${GREEN}✅ Database name: $DB_NAME${NC}"

# Get secret key from SSM Parameter Store
echo -e "${YELLOW}🔑 Getting secret key...${NC}"
SECRET_KEY=$(aws ssm get-parameter --name "/resumerepublic/$ENVIRONMENT/app/secret_key" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo "")

if [ -z "$SECRET_KEY" ]; then
    echo -e "${YELLOW}⚠️  Could not get secret key from SSM Parameter Store${NC}"
    echo -e "${YELLOW}   This may cause issues with production validation${NC}"
else
    echo -e "${GREEN}✅ Secret key retrieved${NC}"
fi

# Set environment variables for Alembic
echo -e "${YELLOW}📋 Setting environment variables for Alembic...${NC}"
export DATABASE_HOST="localhost"
export DATABASE_PORT="$LOCAL_PORT"
export DATABASE_NAME="$DB_NAME"
export DATABASE_USER="$DB_USER"
export DATABASE_PASSWORD="$DB_PASSWORD"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:$LOCAL_PORT/$DB_NAME"
export DATABASE_URL_ASYNC="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost:$LOCAL_PORT/$DB_NAME"
export ENVIRONMENT="$ENVIRONMENT"
# Force use of environment variables instead of Secrets Manager
export DATABASE_CREDENTIALS_SECRET_ARN=""
export USE_IAM_DATABASE_AUTH="false"

echo -e "${GREEN}✅ Environment variables set:${NC}"
echo -e "${BLUE}  DATABASE_HOST=localhost${NC}"
echo -e "${BLUE}  DATABASE_PORT=$LOCAL_PORT${NC}"
echo -e "${BLUE}  DATABASE_NAME=$DB_NAME${NC}"
echo -e "${BLUE}  DATABASE_USER=$DB_USER${NC}"
echo -e "${BLUE}  DATABASE_URL=postgresql://$DB_USER:***@localhost:$LOCAL_PORT/$DB_NAME${NC}"

cd ../../../

# Check if AWS CLI Session Manager plugin is installed
if ! command -v session-manager-plugin &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI Session Manager plugin not found.${NC}"
    echo -e "${YELLOW}Please install it from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html${NC}"
    exit 1
fi

# Create environment setup script
ENV_SCRIPT="/tmp/db-env-${ENVIRONMENT}-${LOCAL_PORT}.sh"
cat > "$ENV_SCRIPT" << EOF
#!/bin/bash
# Database environment variables for $ENVIRONMENT
export DATABASE_HOST="localhost"
export DATABASE_PORT="$LOCAL_PORT"
export DATABASE_NAME="$DB_NAME"
export DATABASE_USER="$DB_USER"
export DATABASE_PASSWORD="$DB_PASSWORD"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:$LOCAL_PORT/$DB_NAME"
export DATABASE_URL_ASYNC="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost:$LOCAL_PORT/$DB_NAME"
export ENVIRONMENT="$ENVIRONMENT"
export DATABASE_CREDENTIALS_SECRET_ARN="$SECRET_ARN"
export USE_IAM_DATABASE_AUTH="false"
export SECRET_KEY="$SECRET_KEY"

echo "🚀 Database environment loaded for $ENVIRONMENT"
echo "📊 Database: $DB_NAME on localhost:$LOCAL_PORT"
echo "🔧 Ready to run Alembic commands!"
echo "🔑 Secret ARN: $SECRET_ARN"
echo "🔐 Secret Key: ${SECRET_KEY:0:10}... (loaded from SSM)"
echo ""
echo "Available commands:"
echo "  alembic current"
echo "  alembic upgrade head"
echo "  alembic history"
echo "  alembic revision --autogenerate -m 'description'"
echo ""
EOF

chmod +x "$ENV_SCRIPT"

# Create connection info file
cat > /tmp/db-connection-info.txt << EOF
Database Connection Info:
- Local port: $LOCAL_PORT
- Remote host: $DB_HOST:5432
- Username: $DB_USER
- Database: $DB_NAME

Environment Variables Set:
- DATABASE_HOST=localhost
- DATABASE_PORT=$LOCAL_PORT
- DATABASE_NAME=$DB_NAME
- DATABASE_USER=$DB_USER
- DATABASE_PASSWORD=*** (hidden)
- DATABASE_URL=postgresql://$DB_USER:***@localhost:$LOCAL_PORT/$DB_NAME
- ENVIRONMENT=$ENVIRONMENT
- DATABASE_CREDENTIALS_SECRET_ARN=$SECRET_ARN

To connect with psql:
psql -h localhost -p $LOCAL_PORT -U $DB_USER -d $DB_NAME

To run Alembic commands in a new terminal:
# Option 1: Use the environment script (recommended)
cd $BACKEND_DIR
source $ENV_SCRIPT
alembic current
alembic upgrade head
alembic history

# Option 2: Use helper script (if available)
./scripts/run-alembic.sh $ENVIRONMENT $LOCAL_PORT current
./scripts/run-alembic.sh $ENVIRONMENT $LOCAL_PORT upgrade head
./scripts/run-alembic.sh $ENVIRONMENT $LOCAL_PORT history

To connect with other tools:
Host: localhost
Port: $LOCAL_PORT
Username: $DB_USER
Database: $DB_NAME
EOF

echo -e "${GREEN}📋 Connection info saved to /tmp/db-connection-info.txt${NC}"
echo -e "${GREEN}📋 Environment script created: $ENV_SCRIPT${NC}"
echo ""

# Detect terminal emulator and open new terminal
TERMINAL_CMD=""
if command -v gnome-terminal &> /dev/null; then
    TERMINAL_CMD="gnome-terminal --tab --title='DB-$ENVIRONMENT' -- bash -c 'cd $BACKEND_DIR; source $ENV_SCRIPT; exec bash'"
elif command -v xterm &> /dev/null; then
    TERMINAL_CMD="xterm -title 'DB-$ENVIRONMENT' -e 'cd $BACKEND_DIR; source $ENV_SCRIPT; bash' &"
elif command -v konsole &> /dev/null; then
    TERMINAL_CMD="konsole --new-tab --title 'DB-$ENVIRONMENT' -e 'cd $BACKEND_DIR; source $ENV_SCRIPT; bash'"
elif command -v alacritty &> /dev/null; then
    TERMINAL_CMD="alacritty --title 'DB-$ENVIRONMENT' -e bash -c 'cd $BACKEND_DIR; source $ENV_SCRIPT; exec bash' &"
elif command -v kitty &> /dev/null; then
    TERMINAL_CMD="kitty --title 'DB-$ENVIRONMENT' bash -c 'cd $BACKEND_DIR; source $ENV_SCRIPT; exec bash' &"
else
    echo -e "${YELLOW}⚠️  No supported terminal emulator found.${NC}"
    echo -e "${YELLOW}Supported terminals: gnome-terminal, xterm, konsole, alacritty, kitty${NC}"
    echo ""
    echo -e "${GREEN}💡 You can manually open a new terminal and run:${NC}"
    echo -e "${BLUE}  cd $BACKEND_DIR${NC}"
    echo -e "${BLUE}  source $ENV_SCRIPT${NC}"
    echo -e "${BLUE}  alembic current${NC}"
    echo ""
fi

if [ -n "$TERMINAL_CMD" ]; then
    echo -e "${GREEN}🚀 Opening new terminal with database environment...${NC}"
    eval "$TERMINAL_CMD"
    echo -e "${GREEN}✅ New terminal opened! You can now run Alembic commands there.${NC}"
    echo ""
fi

echo -e "${YELLOW}🔗 Starting port forwarding session...${NC}"
echo -e "${BLUE}This will forward localhost:$LOCAL_PORT to $DB_HOST:5432${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the session${NC}"
echo ""

# Start the session
aws ssm start-session \
    --target "$INSTANCE_ID" \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "{\"portNumber\":[\"5432\"],\"localPortNumber\":[\"$LOCAL_PORT\"],\"host\":[\"$DB_HOST\"]}"
