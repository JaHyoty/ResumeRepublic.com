variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "resumerepublic"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "resumerepublic-production"
}

variable "lambda_role_arn" {
  description = "IAM role ARN for the Lambda function"
  type        = string
}

variable "lambda_image_uri" {
  description = "ECR image URI for the Lambda container"
  type        = string
}

variable "resumes_s3_bucket" {
  description = "S3 bucket for resume storage"
  type        = string
  default     = ""
}

variable "resumes_cloudfront_domain" {
  description = "CloudFront domain for resume access"
  type        = string
  default     = ""
}

variable "secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
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

variable "openrouter_llm_model" {
  description = "OpenRouter LLM model name"
  type        = string
  default     = ""
}

variable "cookie_domain" {
  description = "Cookie domain"
  type        = string
  default     = ""
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["https://resumerepublic.com"]
}

variable "custom_domain" {
  description = "Custom domain for API Gateway"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

variable "pdf_lambda_image_uri" {
  description = "ECR image URI for the PDF Lambda"
  type        = string
  default     = ""
}

variable "scraper_lambda_image_uri" {
  description = "ECR image URI for the Scraper Lambda"
  type        = string
  default     = ""
}
