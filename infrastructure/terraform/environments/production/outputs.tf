# Production Environment Outputs

# Storage outputs
output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.storage.s3_bucket_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = module.storage.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.storage.cloudfront_distribution_id
}

output "resumes_s3_bucket_name" {
  description = "S3 bucket name for resumes"
  value       = module.storage.resumes_s3_bucket_name
}

output "resumes_cloudfront_domain_name" {
  description = "CloudFront domain name for resumes"
  value       = module.storage.resumes_cloudfront_domain_name
}

output "resumes_cloudfront_distribution_id" {
  description = "CloudFront distribution ID for resumes"
  value       = module.storage.resumes_cloudfront_distribution_id
}

output "cloudfront_public_key_id" {
  description = "CloudFront public key ID for signed URLs"
  value       = module.storage.cloudfront_public_key_id
}

# ECR outputs
output "ecr_repository_url" {
  description = "ECR repository URL for backend API"
  value       = aws_ecr_repository.backend.repository_url
}

output "pdf_ecr_repository_url" {
  description = "ECR repository URL for PDF generator"
  value       = aws_ecr_repository.pdf.repository_url
}

output "scraper_ecr_repository_url" {
  description = "ECR repository URL for job scraper"
  value       = aws_ecr_repository.scraper.repository_url
}

# Serverless outputs
output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.serverless.dynamodb_table_name
}

output "lambda_function_name" {
  description = "Backend API Lambda function name"
  value       = module.serverless.lambda_function_name
}

output "pdf_lambda_function_name" {
  description = "PDF Lambda function name"
  value       = "${var.project_name}-pdf"
}

output "scraper_lambda_function_name" {
  description = "Scraper Lambda function name"
  value       = "${var.project_name}-scraper"
}

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.serverless.api_gateway_endpoint
}


# IAM outputs
output "lambda_execution_role_arn" {
  description = "Lambda execution role ARN"
  value       = module.iam.lambda_execution_role_arn
}

# DNS outputs
output "custom_domain" {
  description = "Custom domain name"
  value       = var.domain_name
}

output "api_domain_name" {
  description = "API domain name"
  value       = var.api_domain_name != "" ? var.api_domain_name : null
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = length(module.dns) > 0 ? module.dns[0].acm_certificate_arn : null
}
