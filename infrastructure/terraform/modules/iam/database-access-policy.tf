# IAM policy for developers to access database via jump host
resource "aws_iam_policy" "database_access" {
  name        = "${var.project_name}-${var.environment}-database-access"
  description = "Policy for developers to access database via jump host using SSM Session Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:StartSession"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}::document/AWS-StartPortForwardingSessionToRemoteHost",
          "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/*"
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceTag/AccessRole" = "jump-host"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:StartSession"
        ]
        Resource = [
          "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/*"
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceTag/AccessRole" = "jump-host"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.database_credentials_secret_arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/database/*"
        ]
      }
    ]
  })

  tags = var.common_tags
}

# Data source for current AWS account ID (already defined in main.tf)
