# DNS Module
# Handles Route53, ACM certificates, and DNS records

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Route 53 zone (assuming you already have the hosted zone)
data "aws_route53_zone" "main" {
  count        = var.create_route53_zone ? 0 : 1
  name         = var.parent_domain_name != "" ? var.parent_domain_name : var.domain_name
  private_zone = false
}

# Create Route53 zone if requested
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = var.domain_name

  tags = var.common_tags
}

# ACM Certificate for custom domain
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = var.subject_alternative_names

  lifecycle {
    create_before_destroy = true
  }

  tags = var.common_tags
}

# ACM Certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Route 53 A record for main domain (CloudFront)
resource "aws_route53_record" "main" {
  count   = var.create_dns_records && var.create_cloudfront_records && var.cloudfront_domain_name != "" && var.cloudfront_hosted_zone_id != "" ? 1 : 0
  zone_id = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# Route 53 A record for www subdomain (CloudFront)
resource "aws_route53_record" "www" {
  count   = var.create_dns_records && var.create_www_record && var.create_cloudfront_records && var.cloudfront_domain_name != "" && var.cloudfront_hosted_zone_id != "" ? 1 : 0
  zone_id = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# Route 53 A record for API subdomain (if provided)
resource "aws_route53_record" "api" {
  count   = var.create_dns_records && var.api_domain_name != "" ? 1 : 0
  zone_id = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_hosted_zone_id
    evaluate_target_health = true
  }
}

