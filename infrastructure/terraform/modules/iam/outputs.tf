# IAM Module Outputs

output "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "ecs_execution_role_name" {
  description = "ECS execution role name"
  value       = aws_iam_role.ecs_execution_role.name
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_task_role_name" {
  description = "ECS task role name"
  value       = aws_iam_role.ecs_task_role.name
}

output "ec2_ssm_role_arn" {
  description = "EC2 SSM role ARN"
  value       = var.create_ec2_ssm_role ? aws_iam_role.ec2_ssm_role[0].arn : null
}

output "ec2_ssm_role_name" {
  description = "EC2 SSM role name"
  value       = var.create_ec2_ssm_role ? aws_iam_role.ec2_ssm_role[0].name : null
}

# SSM Parameter outputs
output "google_client_id_parameter_arn" {
  description = "Google client ID SSM parameter ARN"
  value       = aws_ssm_parameter.google_client_id.arn
}

output "google_client_secret_parameter_arn" {
  description = "Google client secret SSM parameter ARN"
  value       = aws_ssm_parameter.google_client_secret.arn
}

output "github_client_id_parameter_arn" {
  description = "GitHub client ID SSM parameter ARN"
  value       = aws_ssm_parameter.github_client_id.arn
}

output "github_client_secret_parameter_arn" {
  description = "GitHub client secret SSM parameter ARN"
  value       = aws_ssm_parameter.github_client_secret.arn
}

output "openrouter_api_key_parameter_arn" {
  description = "OpenRouter API key SSM parameter ARN"
  value       = aws_ssm_parameter.openrouter_api_key.arn
}

output "database_password_parameter_arn" {
  description = "Database password SSM parameter ARN"
  value       = var.manage_master_user_password ? null : aws_ssm_parameter.database_password[0].arn
}

output "secret_key_parameter_arn" {
  description = "Secret key SSM parameter ARN"
  value       = aws_ssm_parameter.secret_key.arn
}

# Additional application secrets outputs

output "openrouter_llm_model_parameter_arn" {
  description = "OpenRouter LLM model SSM parameter ARN"
  value       = aws_ssm_parameter.openrouter_llm_model.arn
}

# AWS credentials outputs
output "aws_access_key_id_parameter_arn" {
  description = "AWS access key ID SSM parameter ARN"
  value       = var.aws_access_key_id != "" ? aws_ssm_parameter.aws_access_key_id[0].arn : null
}

output "aws_secret_access_key_parameter_arn" {
  description = "AWS secret access key SSM parameter ARN"
  value       = var.aws_secret_access_key != "" ? aws_ssm_parameter.aws_secret_access_key[0].arn : null
}

output "aws_s3_bucket_parameter_arn" {
  description = "AWS S3 bucket SSM parameter ARN"
  value       = var.aws_s3_bucket != "" ? aws_ssm_parameter.aws_s3_bucket[0].arn : null
}

# SSL/TLS configuration outputs
output "ssl_cipher_suites_parameter_arn" {
  description = "SSL cipher suites SSM parameter ARN"
  value       = aws_ssm_parameter.ssl_cipher_suites.arn
}

output "min_tls_version_parameter_arn" {
  description = "Minimum TLS version SSM parameter ARN"
  value       = aws_ssm_parameter.min_tls_version.arn
}

# Database connection details outputs
output "database_host_parameter_arn" {
  description = "Database host SSM parameter ARN"
  value       = aws_ssm_parameter.database_host.arn
}

output "database_name_parameter_arn" {
  description = "Database name SSM parameter ARN"
  value       = aws_ssm_parameter.database_name.arn
}

output "database_user_parameter_arn" {
  description = "Database user SSM parameter ARN"
  value       = aws_ssm_parameter.database_user.arn
}
