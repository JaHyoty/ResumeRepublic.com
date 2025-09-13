# IAM Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "create_ec2_ssm_role" {
  description = "Whether to create EC2 SSM role for dev machines"
  type        = bool
  default     = false
}

# Secret variables
variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_client_id" {
  description = "GitHub OAuth client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_client_secret" {
  description = "GitHub OAuth client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "manage_master_user_password" {
  description = "Whether to use AWS managed master user password"
  type        = bool
  default     = false
}

variable "iam_database_authentication_enabled" {
  description = "Whether IAM database authentication is enabled"
  type        = bool
  default     = false
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
  default     = ""
}

# Additional application secrets

variable "openrouter_llm_model" {
  description = "OpenRouter LLM model"
  type        = string
  default     = "anthropic/claude-3.5-sonnet"
}

# AWS credentials (optional)
variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_s3_bucket" {
  description = "AWS S3 bucket name"
  type        = string
  default     = ""
}

# SSL/TLS Configuration
variable "ssl_cipher_suites" {
  description = "SSL cipher suites"
  type        = string
  default     = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
}

variable "min_tls_version" {
  description = "Minimum TLS version"
  type        = string
  default     = "TLSv1.2"
}

# Database connection details
variable "database_host" {
  description = "Database host endpoint"
  type        = string
  default     = ""
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = ""
}

variable "database_user" {
  description = "Database username"
  type        = string
  default     = ""
}
