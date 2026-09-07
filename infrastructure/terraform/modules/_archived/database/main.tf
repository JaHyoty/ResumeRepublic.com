# Database Module
# Handles RDS PostgreSQL instance, subnet groups, and related resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Generate random password if not provided
resource "random_password" "db_password" {
  count   = var.manage_master_user_password ? 0 : 1
  length  = 32
  special = true
}

# AWS Secrets Manager secret for database credentials
# Only create if not using managed master user password
resource "aws_secretsmanager_secret" "db_credentials" {
  count       = var.manage_master_user_password ? 0 : 1
  name        = "${var.project_name}-${var.environment}-db-credentials"
  description = "Database credentials for ${var.project_name}"

  tags = var.common_tags
}

# Store database credentials in Secrets Manager
# Only create if not using managed master user password
resource "aws_secretsmanager_secret_version" "db_credentials" {
  count     = var.manage_master_user_password ? 0 : 1
  secret_id = aws_secretsmanager_secret.db_credentials[0].id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password != "" ? var.db_password : random_password.db_password[0].result
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    dbname   = var.db_name
  })

  depends_on = [aws_db_instance.main]
}

# RDS Subnet Group (only created if database_subnet_group_name is not provided)
resource "aws_db_subnet_group" "main" {
  count      = var.database_subnet_group_name == null ? 1 : 0
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  })
}

# Local value to determine which subnet group to use
locals {
  db_subnet_group_name = var.database_subnet_group_name != null ? var.database_subnet_group_name : aws_db_subnet_group.main[0].name
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  
  # Use AWS managed master user password for automatic rotation
  manage_master_user_password = var.manage_master_user_password
  password = var.manage_master_user_password ? null : (var.db_password != "" ? var.db_password : random_password.db_password[0].result)
  
  # Reference to the master user secret
  master_user_secret_kms_key_id = var.manage_master_user_password ? var.kms_key_id : null
  
  # Enable IAM database authentication
  iam_database_authentication_enabled = var.iam_database_authentication_enabled

  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = local.db_subnet_group_name

  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window

  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Performance Insights
  performance_insights_enabled = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention_period : null

  # Monitoring
  monitoring_interval = var.monitoring_interval
  monitoring_role_arn = var.monitoring_interval > 0 ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-db"
  })
}

# IAM Role for RDS IAM Database Authentication
resource "aws_iam_role" "rds_iam_auth_role" {
  count = var.iam_database_authentication_enabled ? 1 : 0
  name  = "${var.project_name}-${var.environment}-rds-iam-auth-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# IAM Policy for RDS IAM Database Authentication
resource "aws_iam_role_policy" "rds_iam_auth_policy" {
  count = var.iam_database_authentication_enabled ? 1 : 0
  name  = "${var.project_name}-${var.environment}-rds-iam-auth-policy"
  role  = aws_iam_role.rds_iam_auth_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.main.identifier}/${var.db_username}"
      }
    ]
  })
}

# Data sources for current region and account
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Enhanced monitoring role (only created if monitoring is enabled)
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.monitoring_interval > 0 ? 1 : 0
  name  = "${var.project_name}-${var.environment}-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count      = var.monitoring_interval > 0 ? 1 : 0
  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
