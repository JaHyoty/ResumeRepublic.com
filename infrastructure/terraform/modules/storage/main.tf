# Storage Module
# Handles S3 buckets, CloudFront distributions, ECR repositories, and related resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Random string for unique bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 bucket for CloudFront access logs
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket = "${var.project_name}-${var.environment}-cloudfront-logs-${random_string.bucket_suffix.result}"

  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-${var.environment}-cloudfront-logs"
    Purpose     = "CloudFront access logs"
    Environment = var.environment
  })
}

# Enable ACLs on the CloudFront logs bucket (required for CloudFront logging)
resource "aws_s3_bucket_ownership_controls" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# S3 bucket versioning for CloudFront logs
resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption for CloudFront logs
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle configuration for CloudFront logs
resource "aws_s3_bucket_lifecycle_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    id     = "cloudfront_logs_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""  # Apply to all objects
    }

    expiration {
      days = 30  # Keep logs for 30 days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# S3 bucket ACL for CloudFront logs (required for CloudFront logging)
resource "aws_s3_bucket_acl" "cloudfront_logs" {
  depends_on = [aws_s3_bucket_ownership_controls.cloudfront_logs]
  bucket     = aws_s3_bucket.cloudfront_logs.id
  acl        = "private"
}

# S3 bucket public access block for CloudFront logs
resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  block_public_acls       = false  # Allow ACLs for CloudFront logging
  block_public_policy     = true
  ignore_public_acls      = false  # Allow ACLs for CloudFront logging
  restrict_public_buckets = false  # CloudFront needs access to write logs
}

# S3 Bucket for Frontend
resource "aws_s3_bucket" "frontend" {
  bucket        = "${var.project_name}-${var.environment}-frontend-${random_string.bucket_suffix.result}"
  force_destroy = true  # Allow bucket to be destroyed even if not empty

  tags = var.common_tags
}

# S3 Bucket for PDF Resumes
resource "aws_s3_bucket" "resumes" {
  bucket        = "${var.project_name}-${var.environment}-resumes-${random_string.bucket_suffix.result}"
  force_destroy = true  # Allow bucket to be destroyed even if not empty

  tags = var.common_tags
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true  # Safe with OAC - no public bucket policies needed
}

# S3 Bucket Policy for CloudFront OAC access
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.frontend]
}

# S3 bucket policy for resumes (allow CloudFront access via OAC)
resource "aws_s3_bucket_policy" "resumes" {
  bucket = aws_s3_bucket.resumes.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontOAC"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.resumes.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.resumes.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.resumes]
}

# S3 Bucket Public Access Block for Resumes
resource "aws_s3_bucket_public_access_block" "resumes" {
  bucket = aws_s3_bucket.resumes.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Server Side Encryption for Resumes
resource "aws_s3_bucket_server_side_encryption_configuration" "resumes" {
  bucket = aws_s3_bucket.resumes.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket Lifecycle Configuration for Resumes (cost optimization)
resource "aws_s3_bucket_lifecycle_configuration" "resumes" {
  bucket = aws_s3_bucket.resumes.id

  rule {
    id     = "resume_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""  # Apply to all objects
    }

    # Move old resumes to cheaper storage classes
    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Infrequent Access - 50% cheaper
    }

    transition {
      days          = 90
      storage_class = "GLACIER"  # Archive - 80% cheaper
    }

    # No expiration - keep files indefinitely to maintain database references

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CloudFront Origin Access Control for frontend
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-${var.environment}-frontend-oac"
  description                       = "OAC for ${var.project_name} frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Origin Access Control for resumes
resource "aws_cloudfront_origin_access_control" "resumes" {
  name                              = "${var.project_name}-${var.environment}-resumes-oac"
  description                       = "OAC for ${var.project_name} resumes"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Use AWS managed cache policies for better compatibility
# Managed policy IDs are stable and don't require custom creation


# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  # Frontend S3 bucket origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = var.cloudfront_aliases
  price_class         = "PriceClass_100"  # USA and Europe only - more cost effective

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # Use AWS managed policies for better compatibility
    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # Managed-CachingDisabled
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"  # Managed-CORS-S3Origin
  }

  # Resumes cache behavior removed - now using separate CloudFront distribution

  # SPA routing support
  dynamic "custom_error_response" {
    for_each = var.enable_spa_routing ? [1] : []
    content {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html"
    }
  }

  dynamic "custom_error_response" {
    for_each = var.enable_spa_routing ? [1] : []
    content {
      error_code         = 403
      response_code      = 200
      response_page_path = "/index.html"
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # CloudFront access logging for debugging routing issues
  logging_config {
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    include_cookies = false
    prefix          = "cloudfront-logs/"
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  comment = "CloudFront distribution for ${var.project_name} frontend only - resumes now use separate distribution"

  tags = var.common_tags
}

# CloudFront Key Group for Resume Access Control
resource "aws_cloudfront_key_group" "resumes" {
  name    = "${var.project_name}-${var.environment}-resumes-key-group"
  comment = "Key group for secure resume access via CloudFront signed URLs"

  items = [aws_cloudfront_public_key.resumes.id]
}

# CloudFront Public Key for Resume Access Control
resource "aws_cloudfront_public_key" "resumes" {
  name        = "${var.project_name}-${var.environment}-resumes-public-key"
  comment     = "Public key for CloudFront signed URLs - resumes"
  encoded_key = var.cloudfront_public_key
}

# Separate CloudFront Distribution for Resumes
resource "aws_cloudfront_distribution" "resumes" {
  # Resumes S3 bucket origin
  origin {
    domain_name              = aws_s3_bucket.resumes.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.resumes.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.resumes.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = var.resumes_cloudfront_aliases
  price_class         = "PriceClass_100"  # USA and Europe only - more cost effective

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.resumes.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # SECURITY: Require signed URLs for resume access
    trusted_signers = []
    trusted_key_groups = [aws_cloudfront_key_group.resumes.id]

    # Use AWS managed policies for better compatibility
    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # Managed-CachingDisabled
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"  # Managed-CORS-S3Origin
  }

  # CloudFront access logging for debugging
  logging_config {
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    include_cookies = false
    prefix          = "resumes-cloudfront-logs/"
  }

  # SSL Certificate (use same as frontend)
  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # Geographic restrictions (none - allow worldwide access)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  comment = "CloudFront distribution for ${var.project_name} resumes - Dedicated distribution for PDF access"

  tags = var.common_tags
}


# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.common_tags
}

# ECR lifecycle policy
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
