output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.main.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.main.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "api_gateway_execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_apigatewayv2_api.main.execution_arn
}

output "custom_domain_target" {
  description = "Target domain name for Route53 alias record"
  value       = var.custom_domain != "" ? aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name : ""
}

output "custom_domain_hosted_zone_id" {
  description = "Hosted zone ID for the API Gateway domain"
  value       = var.custom_domain != "" ? aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id : ""
}
