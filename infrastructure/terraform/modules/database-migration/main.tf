# Database Migration Module
# Creates ECS task definition and service for running database migrations

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECS Task Definition for Database Migrations
resource "aws_ecs_task_definition" "migration" {
  family                   = "${var.project_name}-db-migration"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.migration_cpu
  memory                   = var.migration_memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn           = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "migration"
      image = var.migration_image
      
      # Environment variables
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "DEBUG"
          value = var.debug ? "true" : "false"
        },
        {
          name  = "PYTHONPATH"
          value = "/app"
        },
        {
          name  = "MIGRATION_MODE"
          value = "upgrade"
        }
      ]

      # Secrets from Parameter Store and Secrets Manager
      secrets = [
        {
          name      = "DATABASE_HOST"
          valueFrom = var.database_host_parameter_arn
        },
        {
          name      = "DATABASE_NAME"
          valueFrom = var.database_name_parameter_arn
        },
        {
          name      = "DATABASE_USER"
          valueFrom = var.database_user_parameter_arn
        },
        {
          name      = "DATABASE_CREDENTIALS"
          valueFrom = var.database_credentials_secret_arn
        },
        {
          name      = "SECRET_KEY"
          valueFrom = var.secret_key_parameter_arn
        }
      ]

      # Logging
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }

      # Essential container
      essential = true
      
      # Command to run Alembic migrations within the ECS task
      command = [
        "/bin/bash", "-c",
        <<-EOT
          set -e
          echo "🗄️  Starting database migration process..."
          
          # Set working directory to app
          cd /app
          
          # Test database connection
          echo "🔗 Testing database connection..."
          python -c "
          import os
          from sqlalchemy import create_engine
          from sqlalchemy.exc import OperationalError
          
          db_url = f'postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_CREDENTIALS']}@{os.environ['DATABASE_HOST']}/{os.environ['DATABASE_NAME']}'
          try:
              engine = create_engine(db_url)
              with engine.connect() as conn:
                  conn.execute('SELECT 1')
              print('✅ Database connection successful')
          except Exception as e:
              print(f'❌ Database connection failed: {e}')
              exit(1)
          "
          
          # Check current migration status
          echo "📊 Checking current migration status..."
          alembic current
          
          # Show available migrations
          echo "📋 Available migrations:"
          alembic history
          
          # Run Alembic upgrade
          echo "🏗️  Running Alembic upgrade to head..."
          alembic upgrade head
          
          # Verify migration completed
          echo "✅ Verifying migration completion..."
          alembic current
          
          echo "✅ Database migration completed successfully!"
        EOT
      ]
    }
  ])

  tags = var.common_tags
}

# CloudWatch Log Group for Migration Logs
resource "aws_cloudwatch_log_group" "migration" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = var.common_tags
}

# IAM Policy for Migration Task
resource "aws_iam_policy" "migration_task_policy" {
  name        = "${var.project_name}-${var.environment}-migration-task-policy"
  description = "Policy for database migration tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          var.database_credentials_secret_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.migration.arn}:*"
      }
    ]
  })

  tags = var.common_tags
}

# Attach policy to task role
resource "aws_iam_role_policy_attachment" "migration_task_policy" {
  role       = var.ecs_task_role_name
  policy_arn = aws_iam_policy.migration_task_policy.arn
}
