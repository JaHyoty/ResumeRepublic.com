# IAM Module
# Handles IAM roles, policies, and SSM parameters

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

# ECS Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for SSM parameter and Secrets Manager access
resource "aws_iam_role_policy" "ecs_execution_secrets_policy" {
  name = "${var.project_name}-${var.environment}-ecs-execution-secrets-policy"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-*"
        ]
      }
    ]
  })
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# ECS Task Role Policy for RDS IAM Authentication
resource "aws_iam_role_policy" "ecs_task_rds_iam_policy" {
  count = var.iam_database_authentication_enabled ? 1 : 0
  name  = "${var.project_name}-${var.environment}-ecs-task-rds-iam-policy"
  role  = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = "arn:aws:rds-db:${var.aws_region}:${data.aws_caller_identity.current.account_id}:dbuser:${var.project_name}-${var.environment}-db/${var.database_user}"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

# EC2 SSM Role for dev machines
resource "aws_iam_role" "ec2_ssm_role" {
  count = var.create_ec2_ssm_role ? 1 : 0
  name  = "${var.project_name}-${var.environment}-ec2-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "ec2_ssm_policy_attachment" {
  count      = var.create_ec2_ssm_role ? 1 : 0
  role       = aws_iam_role.ec2_ssm_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# SSM Parameters for secrets
resource "aws_ssm_parameter" "google_client_id" {
  name  = "/${var.project_name}/${var.environment}/google/client_id"
  type  = "SecureString"
  value = var.google_client_id

  tags = var.common_tags
}

resource "aws_ssm_parameter" "google_client_secret" {
  name  = "/${var.project_name}/${var.environment}/google/client_secret"
  type  = "SecureString"
  value = var.google_client_secret

  tags = var.common_tags
}

resource "aws_ssm_parameter" "github_client_id" {
  name  = "/${var.project_name}/${var.environment}/github/client_id"
  type  = "SecureString"
  value = var.github_client_id

  tags = var.common_tags
}

resource "aws_ssm_parameter" "github_client_secret" {
  name  = "/${var.project_name}/${var.environment}/github/client_secret"
  type  = "SecureString"
  value = var.github_client_secret

  tags = var.common_tags
}

resource "aws_ssm_parameter" "openrouter_api_key" {
  name  = "/${var.project_name}/${var.environment}/openrouter/api_key"
  type  = "SecureString"
  value = var.openrouter_api_key

  tags = var.common_tags
}

resource "aws_ssm_parameter" "database_password" {
  count = var.manage_master_user_password ? 0 : 1
  name  = "/${var.project_name}/${var.environment}/database/password"
  type  = "SecureString"
  value = var.database_password

  tags = var.common_tags
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "/${var.project_name}/${var.environment}/app/secret_key"
  type  = "SecureString"
  value = var.secret_key

  tags = var.common_tags
}

# Additional application secrets

resource "aws_ssm_parameter" "openrouter_llm_model" {
  name  = "/${var.project_name}/${var.environment}/app/openrouter_llm_model"
  type  = "String"
  value = var.openrouter_llm_model

  tags = var.common_tags
}

# AWS credentials (if provided)
resource "aws_ssm_parameter" "aws_access_key_id" {
  count = var.aws_access_key_id != "" ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/aws/access_key_id"
  type  = "SecureString"
  value = var.aws_access_key_id

  tags = var.common_tags
}

resource "aws_ssm_parameter" "aws_secret_access_key" {
  count = var.aws_secret_access_key != "" ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/aws/secret_access_key"
  type  = "SecureString"
  value = var.aws_secret_access_key

  tags = var.common_tags
}

resource "aws_ssm_parameter" "aws_s3_bucket" {
  count = var.aws_s3_bucket != "" ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/aws/s3_bucket"
  type  = "String"
  value = var.aws_s3_bucket

  tags = var.common_tags
}

# SSL/TLS Configuration
resource "aws_ssm_parameter" "ssl_cipher_suites" {
  name  = "/${var.project_name}/${var.environment}/app/ssl_cipher_suites"
  type  = "String"
  value = var.ssl_cipher_suites

  tags = var.common_tags
}

resource "aws_ssm_parameter" "min_tls_version" {
  name  = "/${var.project_name}/${var.environment}/app/min_tls_version"
  type  = "String"
  value = var.min_tls_version

  tags = var.common_tags
}

# Database connection details
resource "aws_ssm_parameter" "database_host" {
  name  = "/${var.project_name}/${var.environment}/database/host"
  type  = "String"
  value = var.database_host

  tags = var.common_tags
}

resource "aws_ssm_parameter" "database_name" {
  name  = "/${var.project_name}/${var.environment}/database/name"
  type  = "String"
  value = var.database_name

  tags = var.common_tags
}

resource "aws_ssm_parameter" "database_user" {
  name  = "/${var.project_name}/${var.environment}/database/user"
  type  = "String"
  value = var.database_user

  tags = var.common_tags
}
