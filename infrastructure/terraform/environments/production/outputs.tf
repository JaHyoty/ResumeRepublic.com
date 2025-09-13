# Production Environment Outputs

# Networking outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.networking.alb_dns_name
}

# Database outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "db_hostname" {
  description = "RDS hostname (without port)"
  value       = module.database.db_hostname
  sensitive   = true
}

output "db_name" {
  description = "Database name"
  value       = module.database.db_name
}

output "db_username" {
  description = "Database username"
  value       = module.database.db_username
}

# Compute outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.compute.ecs_cluster_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.compute.ecs_cluster_arn
}

# Storage outputs
output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.storage.s3_bucket_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = module.storage.cloudfront_domain_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.storage.ecr_repository_url
}

# DNS outputs
output "custom_domain" {
  description = "Custom domain name"
  value       = var.domain_name
}

output "www_domain" {
  description = "WWW domain name"
  value       = "www.${var.domain_name}"
}

output "api_domain_name" {
  description = "API domain name"
  value       = var.api_domain_name != "" ? var.api_domain_name : null
}


output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = module.dns.acm_certificate_arn
}

# IAM outputs
output "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  value       = module.iam.ecs_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = module.iam.ecs_task_role_arn
}
