# Production Environment Variables

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "resumerepublic"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "resumerepublic.com"
}

variable "api_domain_name" {
  description = "API subdomain name (e.g., api.resumerepublic.com)"
  type        = string
  default     = ""
}

variable "parent_domain_name" {
  description = "Parent domain name for DNS validation (e.g., resumerepublic.com for resumerepublic.com)"
  type        = string
  default     = ""
}


# Networking variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

# variable "private_subnets" {
#   description = "List of private subnet CIDR blocks for backend services"
#   type        = list(string)
#   default     = ["10.0.1.0/24", "10.0.2.0/24"]
# }

variable "database_subnets" {
  description = "List of database subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "backend_port" {
  description = "Backend application port"
  type        = number
  default     = 8000
}

# Database variables
variable "postgres_version" {
  description = "PostgreSQL version for RDS"
  type        = string
  default     = "17.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 10
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_storage_type" {
  description = "Storage type for RDS"
  type        = string
  default     = "gp2"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "resumerepublic_prod"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "resumerepublic_user"
}

variable "db_password" {
  description = "Database password (ignored if db_manage_master_user_password is true)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_manage_master_user_password" {
  description = "Use AWS managed master user password with automatic rotation"
  type        = bool
  default     = true
}

variable "db_iam_database_authentication_enabled" {
  description = "Whether to enable IAM database authentication"
  type        = bool
  default     = false
}

variable "db_password_rotation_days" {
  description = "Number of days after which to rotate the password (0 to disable rotation)"
  type        = number
  default     = 30
}

variable "db_kms_key_id" {
  description = "KMS key ID for encrypting the master user secret"
  type        = string
  default     = null
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "db_skip_final_snapshot" {
  description = "Skip final snapshot when destroying"
  type        = bool
  default     = false
}

variable "db_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false
}

variable "db_performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

variable "db_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0 to disable)"
  type        = number
  default     = 0
}

# Compute variables
variable "task_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory for ECS task"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# DNS variables
variable "create_route53_zone" {
  description = "Whether to create a new Route53 hosted zone"
  type        = bool
  default     = false
}

variable "create_www_record" {
  description = "Whether to create a www subdomain record"
  type        = bool
  default     = true
}

variable "create_cloudfront_records" {
  description = "Whether to create CloudFront-dependent DNS records (can cause circular dependency)"
  type        = bool
  default     = false
}

# IAM variables
variable "create_ec2_ssm_role" {
  description = "Whether to create EC2 SSM role for dev machines"
  type        = bool
  default     = false
}

# Secret variables
variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

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

# Additional application secrets

variable "openrouter_llm_model" {
  description = "OpenRouter LLM model"
  type        = string
  default     = "anthropic/claude-sonnet-4"
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

# Database connection details (will be populated from database module outputs)
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

# CloudFront Configuration
# CloudFront public key ID is now generated dynamically by Terraform
# No variables needed for CloudFront key management
