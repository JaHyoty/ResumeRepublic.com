# Database Migration Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
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

# ECS Configuration
variable "ecs_cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "ecs_task_role_name" {
  description = "ECS task role name"
  type        = string
}

# Network Configuration
variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "migration_security_group_id" {
  description = "Security group ID for migration tasks"
  type        = string
}

# Database Configuration
variable "database_host_parameter_arn" {
  description = "Database host parameter ARN"
  type        = string
}

variable "database_name_parameter_arn" {
  description = "Database name parameter ARN"
  type        = string
}

variable "database_user_parameter_arn" {
  description = "Database user parameter ARN"
  type        = string
}

variable "database_credentials_secret_arn" {
  description = "Database credentials secret ARN"
  type        = string
}

variable "secret_key_parameter_arn" {
  description = "Secret key parameter ARN"
  type        = string
}

# Migration Configuration
variable "migration_image" {
  description = "Docker image for database migrations (should be your backend image)"
  type        = string
  default     = ""
}

variable "migration_cpu" {
  description = "CPU units for migration task"
  type        = number
  default     = 512
}

variable "migration_memory" {
  description = "Memory for migration task"
  type        = number
  default     = 1024
}

# Logging Configuration
variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 7
}

variable "debug" {
  description = "Enable debug mode"
  type        = bool
  default     = false
}
