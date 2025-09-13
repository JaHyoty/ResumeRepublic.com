# Secrets Module Outputs

# OAuth Credentials
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

# API Keys
output "openrouter_api_key_parameter_arn" {
  description = "OpenRouter API key SSM parameter ARN"
  value       = aws_ssm_parameter.openrouter_api_key.arn
}

# Application Secrets
output "secret_key_parameter_arn" {
  description = "Secret key SSM parameter ARN"
  value       = aws_ssm_parameter.secret_key.arn
}

# Non-sensitive configuration

output "openrouter_llm_model_parameter_arn" {
  description = "OpenRouter LLM model SSM parameter ARN"
  value       = aws_ssm_parameter.openrouter_llm_model.arn
}

# SSL/TLS Configuration
output "ssl_cipher_suites_parameter_arn" {
  description = "SSL cipher suites SSM parameter ARN"
  value       = aws_ssm_parameter.ssl_cipher_suites.arn
}

output "min_tls_version_parameter_arn" {
  description = "Minimum TLS version SSM parameter ARN"
  value       = aws_ssm_parameter.min_tls_version.arn
}

# Database connection details
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
