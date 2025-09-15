# Networking Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

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

variable "private_subnets" {
  description = "List of private subnet CIDR blocks for backend services"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

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

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener"
  type        = string
  default     = null
}
