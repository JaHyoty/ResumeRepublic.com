# DNS Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "parent_domain_name" {
  description = "Parent domain name for DNS validation (e.g., resumerepublic.com for dev.resumerepublic.com)"
  type        = string
  default     = ""
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "create_route53_zone" {
  description = "Whether to create a new Route53 hosted zone"
  type        = bool
  default     = false
}

variable "create_dns_records" {
  description = "Whether to create DNS records"
  type        = bool
  default     = true
}

variable "create_cloudfront_records" {
  description = "Whether to create CloudFront-dependent DNS records (can cause circular dependency)"
  type        = bool
  default     = false
}

variable "create_www_record" {
  description = "Whether to create www subdomain record"
  type        = bool
  default     = true
}

variable "subject_alternative_names" {
  description = "Subject alternative names for the certificate"
  type        = list(string)
  default     = []
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
  default     = ""
}

variable "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  type        = string
  default     = ""
}

variable "alb_hosted_zone_id" {
  description = "Application Load Balancer hosted zone ID"
  type        = string
  default     = ""
}

variable "api_domain_name" {
  description = "API subdomain name (e.g., api.example.com)"
  type        = string
  default     = ""
}

