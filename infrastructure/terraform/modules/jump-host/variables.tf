variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the jump host will be deployed"
  type        = string
}

variable "database_subnet_id" {
  description = "Database subnet ID where the jump host will be deployed"
  type        = string
}

variable "database_host" {
  description = "Database host endpoint"
  type        = string
}

variable "database_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "database_security_group_id" {
  description = "Security group ID of the database"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for jump host"
  type        = string
  default     = "t3.micro"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
