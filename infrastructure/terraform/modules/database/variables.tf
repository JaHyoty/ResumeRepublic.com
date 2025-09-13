# Database Module Variables

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

variable "private_subnet_ids" {
  description = "List of private subnet IDs for RDS subnet group (deprecated - use database_subnet_group_name)"
  type        = list(string)
  default     = []
}

variable "database_subnet_group_name" {
  description = "Database subnet group name (preferred over private_subnet_ids)"
  type        = string
  default     = null
}

variable "rds_security_group_id" {
  description = "Security group ID for RDS"
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL version for RDS"
  type        = string
  default     = "17.4"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "storage_type" {
  description = "Storage type for RDS"
  type        = string
  default     = "gp2"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "resumerepublic"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "resumerepublic_user"
}

variable "db_password" {
  description = "Database password (ignored if manage_master_user_password is true)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "manage_master_user_password" {
  description = "Use AWS managed master user password with automatic rotation"
  type        = bool
  default     = true
}

variable "iam_database_authentication_enabled" {
  description = "Whether to enable IAM database authentication"
  type        = bool
  default     = true
}

variable "password_rotation_days" {
  description = "Number of days after which to rotate the password (0 to disable rotation)"
  type        = number
  default     = 30
}

variable "kms_key_id" {
  description = "KMS key ID for encrypting the master user secret"
  type        = string
  default     = null
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying"
  type        = bool
  default     = false
}

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0 to disable)"
  type        = number
  default     = 0
}
