# Database Module Outputs

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "db_hostname" {
  description = "RDS hostname (without port)"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Database username"
  value       = aws_db_instance.main.username
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

output "db_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "db_subnet_group_name" {
  description = "DB subnet group name"
  value       = local.db_subnet_group_name
}

output "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret in Secrets Manager"
  value       = var.manage_master_user_password ? null : aws_secretsmanager_secret.db_credentials[0].arn
}

output "db_credentials_secret_name" {
  description = "Name of the database credentials secret in Secrets Manager"
  value       = var.manage_master_user_password ? null : aws_secretsmanager_secret.db_credentials[0].name
}

output "db_master_user_secret_arn" {
  description = "ARN of the RDS master user secret (if managed by AWS)"
  value       = var.manage_master_user_password ? aws_db_instance.main.master_user_secret[0].secret_arn : null
}

output "db_iam_auth_role_arn" {
  description = "ARN of the IAM role for RDS IAM database authentication"
  value       = var.iam_database_authentication_enabled ? aws_iam_role.rds_iam_auth_role[0].arn : null
}

output "db_iam_auth_role_name" {
  description = "Name of the IAM role for RDS IAM database authentication"
  value       = var.iam_database_authentication_enabled ? aws_iam_role.rds_iam_auth_role[0].name : null
}

output "db_security_group_id" {
  description = "Security group ID of the database"
  value       = var.rds_security_group_id
}

