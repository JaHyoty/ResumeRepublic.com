# Secrets Management Module
# Handles secure secret retrieval and Parameter Store creation

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data source for existing secrets (if using external secret management)
data "aws_secretsmanager_secret" "app_secrets" {
  count = var.use_external_secrets ? 1 : 0
  name  = var.external_secrets_name
}

data "aws_secretsmanager_secret_version" "app_secrets" {
  count     = var.use_external_secrets ? 1 : 0
  secret_id = data.aws_secretsmanager_secret.app_secrets[0].id
}

# Local values for secret resolution
locals {
  # Use external secrets if available, otherwise use variables
  secrets = var.use_external_secrets ? jsondecode(data.aws_secretsmanager_secret_version.app_secrets[0].secret_string) : {
    google_client_id     = var.google_client_id
    google_client_secret = var.google_client_secret
    github_client_id     = var.github_client_id
    github_client_secret = var.github_client_secret
    openrouter_api_key   = var.openrouter_api_key
    secret_key           = var.secret_key
  }
}

# OAuth Credentials
resource "aws_ssm_parameter" "google_client_id" {
  name  = "/${var.project_name}/google/client_id"
  type  = "SecureString"
  value = local.secrets.google_client_id

  tags = var.common_tags
}

resource "aws_ssm_parameter" "google_client_secret" {
  name  = "/${var.project_name}/google/client_secret"
  type  = "SecureString"
  value = local.secrets.google_client_secret

  tags = var.common_tags
}

resource "aws_ssm_parameter" "github_client_id" {
  name  = "/${var.project_name}/github/client_id"
  type  = "SecureString"
  value = local.secrets.github_client_id

  tags = var.common_tags
}

resource "aws_ssm_parameter" "github_client_secret" {
  name  = "/${var.project_name}/github/client_secret"
  type  = "SecureString"
  value = local.secrets.github_client_secret

  tags = var.common_tags
}

# API Keys
resource "aws_ssm_parameter" "openrouter_api_key" {
  name  = "/${var.project_name}/openrouter/api_key"
  type  = "SecureString"
  value = local.secrets.openrouter_api_key

  tags = var.common_tags
}

# Application Secrets
resource "aws_ssm_parameter" "secret_key" {
  name  = "/${var.project_name}/app/secret_key"
  type  = "SecureString"
  value = local.secrets.secret_key

  tags = var.common_tags
}

# Non-sensitive configuration

resource "aws_ssm_parameter" "openrouter_llm_model" {
  name  = "/${var.project_name}/app/openrouter_llm_model"
  type  = "String"
  value = var.openrouter_llm_model

  tags = var.common_tags
}

# SSL/TLS Configuration
resource "aws_ssm_parameter" "ssl_cipher_suites" {
  name  = "/${var.project_name}/app/ssl_cipher_suites"
  type  = "String"
  value = var.ssl_cipher_suites

  tags = var.common_tags
}

resource "aws_ssm_parameter" "min_tls_version" {
  name  = "/${var.project_name}/app/min_tls_version"
  type  = "String"
  value = var.min_tls_version

  tags = var.common_tags
}

# Database connection details (populated after database creation)
resource "aws_ssm_parameter" "database_host" {
  name  = "/${var.project_name}/database/host"
  type  = "String"
  value = var.database_host

  tags = var.common_tags
}

resource "aws_ssm_parameter" "database_name" {
  name  = "/${var.project_name}/database/name"
  type  = "String"
  value = var.database_name

  tags = var.common_tags
}

resource "aws_ssm_parameter" "database_user" {
  name  = "/${var.project_name}/database/user"
  type  = "String"
  value = var.database_user

  tags = var.common_tags
}
