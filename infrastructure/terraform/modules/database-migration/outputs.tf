# Database Migration Module Outputs

output "migration_task_definition_arn" {
  description = "Migration task definition ARN"
  value       = aws_ecs_task_definition.migration.arn
}

output "migration_log_group_name" {
  description = "Migration log group name"
  value       = aws_cloudwatch_log_group.migration.name
}

output "migration_log_group_arn" {
  description = "Migration log group ARN"
  value       = aws_cloudwatch_log_group.migration.arn
}
