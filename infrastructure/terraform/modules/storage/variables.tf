# Storage Module Variables

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

variable "cloudfront_aliases" {
  description = "CloudFront distribution aliases"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront"
  type        = string
  default     = null
}

variable "enable_spa_routing" {
  description = "Enable SPA routing support (404/403 -> index.html)"
  type        = bool
  default     = true
}
