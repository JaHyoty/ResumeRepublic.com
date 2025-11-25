# Storage Module Outputs

output "s3_bucket_id" {
  description = "S3 bucket ID for frontend"
  value       = aws_s3_bucket.frontend.id
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for frontend"
  value       = aws_s3_bucket.frontend.arn
}

output "s3_bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.frontend.bucket_domain_name
}

output "s3_bucket_regional_domain_name" {
  description = "S3 bucket regional domain name"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.frontend.arn
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_arn" {
  description = "ECR repository ARN for backend"
  value       = aws_ecr_repository.backend.arn
}

output "ecr_repository_name" {
  description = "ECR repository name for backend"
  value       = aws_ecr_repository.backend.name
}

# Resumes S3 Bucket Outputs
output "resumes_s3_bucket_id" {
  description = "S3 bucket ID for resumes"
  value       = aws_s3_bucket.resumes.id
}

output "resumes_s3_bucket_name" {
  description = "S3 bucket name for resumes"
  value       = aws_s3_bucket.resumes.bucket
}

output "resumes_s3_bucket_arn" {
  description = "S3 bucket ARN for resumes"
  value       = aws_s3_bucket.resumes.arn
}

output "resumes_s3_bucket_domain_name" {
  description = "S3 bucket domain name for resumes"
  value       = aws_s3_bucket.resumes.bucket_domain_name
}

output "resumes_s3_bucket_regional_domain_name" {
  description = "S3 bucket regional domain name for resumes"
  value       = aws_s3_bucket.resumes.bucket_regional_domain_name
}

# Resumes CloudFront Distribution Outputs
output "resumes_cloudfront_distribution_id" {
  description = "CloudFront distribution ID for resumes"
  value       = aws_cloudfront_distribution.resumes.id
}

output "resumes_cloudfront_domain_name" {
  description = "CloudFront domain name for resumes"
  value       = aws_cloudfront_distribution.resumes.domain_name
}

output "resumes_cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID for resumes"
  value       = aws_cloudfront_distribution.resumes.hosted_zone_id
}

output "cloudfront_public_key_id" {
  description = "CloudFront public key ID for signed URLs"
  value       = aws_cloudfront_public_key.resumes.id
}

