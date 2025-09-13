# DNS Module Outputs

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
}

output "route53_zone_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].name_servers : data.aws_route53_zone.main[0].name_servers
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.main.arn
}

output "acm_certificate_domain_name" {
  description = "ACM certificate domain name"
  value       = aws_acm_certificate.main.domain_name
}

output "acm_certificate_validation_arn" {
  description = "ACM certificate validation ARN"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

output "main_domain_record_name" {
  description = "Main domain record name"
  value       = var.create_dns_records ? aws_route53_record.main[0].name : null
}

output "www_domain_record_name" {
  description = "WWW domain record name"
  value       = var.create_dns_records && var.create_www_record ? aws_route53_record.www[0].name : null
}

output "api_domain_record_name" {
  description = "API domain record name"
  value       = var.create_dns_records && var.api_domain_name != "" ? aws_route53_record.api[0].name : null
}

