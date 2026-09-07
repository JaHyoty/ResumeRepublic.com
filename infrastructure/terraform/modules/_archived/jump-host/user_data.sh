#!/bin/bash
set -e

# Update system
yum update -y

# Install PostgreSQL client (use PostgreSQL 14 which supports SCRAM authentication)
amazon-linux-extras install postgresql14 -y

# Install additional tools
yum install -y htop nano vim

# Create a simple script for database connection
cat > /home/ec2-user/connect-db.sh << 'EOF'
#!/bin/bash
echo "Connecting to database at ${db_host}:${db_port}"
psql14 -h ${db_host} -p ${db_port} -U $1 -d $2
EOF

chmod +x /home/ec2-user/connect-db.sh
chown ec2-user:ec2-user /home/ec2-user/connect-db.sh

# Create a script to show database info
cat > /home/ec2-user/db-info.sh << 'EOF'
#!/bin/bash
echo "=== Database Connection Info ==="
echo "Host: ${db_host}"
echo "Port: ${db_port}"
echo ""
echo "To connect to the database:"
echo "1. Get database credentials from AWS Secrets Manager"
echo "2. Run: psql14 -h ${db_host} -p ${db_port} -U <username> -d <database>"
echo ""
echo "Or use the helper script:"
echo "./connect-db.sh <username> <database>"
EOF

chmod +x /home/ec2-user/db-info.sh
chown ec2-user:ec2-user /home/ec2-user/db-info.sh

# Instance setup completed
echo "Jump host setup completed successfully"
