###############################################################################
# IAM Module — Serverless version (Lambda execution role)
# Replaces ECS execution/task roles with Lambda execution role
###############################################################################

data "aws_caller_identity" "current" {}

# Generate a random secret key if none provided
resource "random_password" "secret_key" {
  length  = 64
  special = true
}

# ---------------------------------------------------------------
# Lambda Execution Role
# ---------------------------------------------------------------

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-${var.environment}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# CloudWatch Logs policy (required for Lambda)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB access policy
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "${var.project_name}-${var.environment}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}-*",
          "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}-*/index/*"
        ]
      }
    ]
  })
}

# S3 access policy (for resume PDFs)
resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "${var.project_name}-${var.environment}-lambda-s3-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-resumes-*",
          "arn:aws:s3:::${var.project_name}-${var.environment}-resumes-*/*"
        ]
      }
    ]
  })
}

# SSM Parameter Store access
resource "aws_iam_role_policy" "lambda_ssm_policy" {
  name = "${var.project_name}-${var.environment}-lambda-ssm-policy"
  role = aws_iam_role.lambda_execution_role.id

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
      }
    ]
  })
}

# Lambda invoke policy (for API Lambda to invoke worker Lambdas)
resource "aws_iam_role_policy" "lambda_invoke_policy" {
  name = "${var.project_name}-${var.environment}-lambda-invoke-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-*"
        ]
      }
    ]
  })
}

# ---------------------------------------------------------------
# SSM Parameters for secrets
# ---------------------------------------------------------------

resource "aws_ssm_parameter" "google_client_id" {
  name  = "/${var.project_name}/${var.environment}/google/client_id"
  type  = "SecureString"
  value = var.google_client_id
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "google_client_secret" {
  name  = "/${var.project_name}/${var.environment}/google/client_secret"
  type  = "SecureString"
  value = var.google_client_secret
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "github_client_id" {
  name  = "/${var.project_name}/${var.environment}/github/client_id"
  type  = "SecureString"
  value = var.github_client_id
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "github_client_secret" {
  name  = "/${var.project_name}/${var.environment}/github/client_secret"
  type  = "SecureString"
  value = var.github_client_secret
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "openrouter_api_key" {
  name  = "/${var.project_name}/${var.environment}/openrouter/api_key"
  type  = "SecureString"
  value = var.openrouter_api_key
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "/${var.project_name}/${var.environment}/app/secret_key"
  type  = "SecureString"
  value = var.secret_key != "" ? var.secret_key : random_password.secret_key.result
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "openrouter_llm_model" {
  name  = "/${var.project_name}/${var.environment}/app/openrouter_llm_model"
  type  = "String"
  value = var.openrouter_llm_model
  tags  = var.common_tags

  lifecycle {
    ignore_changes = [value]
  }
}
