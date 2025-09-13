# Compute Module Variables

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

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
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

variable "alb_target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "alb_listener_dependency" {
  description = "ALB listener dependency for ECS service"
  type        = any
  default     = null
}

variable "backend_port" {
  description = "Backend application port"
  type        = number
  default     = 8000
}

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

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "container_environment" {
  description = "Environment variables for container"
  type        = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "container_secrets" {
  description = "Secrets for container from SSM Parameter Store and Secrets Manager"
  type        = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

variable "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret in Secrets Manager"
  type        = string
  default     = ""
}
