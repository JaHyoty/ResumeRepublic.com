# Development Environment Configuration
# This file orchestrates all modules for the development environment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Local values
locals {
  environment = "production"
  common_tags = {
    Project     = var.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
  }
  
  # ACM certificate ARN for networking module
  acm_certificate_arn = var.domain_name != "" ? module.dns[0].acm_certificate_arn : null
}

# Data sources
data "aws_caller_identity" "current" {}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name = var.project_name
  environment  = local.environment
  common_tags  = local.common_tags

  vpc_cidr                = var.vpc_cidr
  availability_zone_count = var.availability_zone_count
  # private_subnets         = var.private_subnets  # Removed - no longer needed
  database_subnets        = var.database_subnets
  public_subnets          = var.public_subnets
  backend_port            = var.backend_port
  acm_certificate_arn     = local.acm_certificate_arn
}

# Database Module
module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = local.environment
  common_tags  = local.common_tags

  # private_subnet_ids      = module.networking.private_subnets  # Removed - using database_subnet_group_name instead
  database_subnet_group_name = module.networking.database_subnet_group_name
  rds_security_group_id   = module.networking.rds_security_group_id
  postgres_version        = var.postgres_version
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  max_allocated_storage   = var.db_max_allocated_storage
  storage_type            = var.db_storage_type
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  manage_master_user_password = var.db_manage_master_user_password
  password_rotation_days  = var.db_password_rotation_days
  kms_key_id              = var.db_kms_key_id
  iam_database_authentication_enabled = var.db_iam_database_authentication_enabled
  backup_retention_period = var.db_backup_retention_period
  backup_window           = var.db_backup_window
  maintenance_window      = var.db_maintenance_window
  skip_final_snapshot     = var.db_skip_final_snapshot
  performance_insights_enabled = var.db_performance_insights_enabled
  performance_insights_retention_period = var.db_performance_insights_retention_period
  monitoring_interval     = var.db_monitoring_interval
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = local.environment
  aws_region   = var.aws_region
  common_tags  = local.common_tags

  create_ec2_ssm_role = var.create_ec2_ssm_role
  google_client_id    = var.google_client_id
  google_client_secret = var.google_client_secret
  github_client_id    = var.github_client_id
  github_client_secret = var.github_client_secret
  openrouter_api_key  = var.openrouter_api_key
  database_password   = var.db_password
  manage_master_user_password = var.db_manage_master_user_password
  iam_database_authentication_enabled = var.db_iam_database_authentication_enabled
  database_credentials_secret_arn     = module.database.db_master_user_secret_arn
  secret_key          = var.secret_key
  openrouter_llm_model = var.openrouter_llm_model
  aws_access_key_id   = var.aws_access_key_id
  aws_secret_access_key = var.aws_secret_access_key
  aws_s3_bucket       = var.aws_s3_bucket
  ssl_cipher_suites   = var.ssl_cipher_suites
  min_tls_version     = var.min_tls_version
  database_host       = module.database.db_hostname
  database_name       = module.database.db_name
  database_user       = module.database.db_username
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_name = var.project_name
  environment  = local.environment
  common_tags  = local.common_tags

  cloudfront_aliases         = var.domain_name != "" ? [var.domain_name] : []
  resumes_cloudfront_aliases = []  # No aliases for now - use default CloudFront domain
  acm_certificate_arn        = var.domain_name != "" ? module.dns[0].acm_certificate_validation_arn : null
  enable_spa_routing         = true
  cloudfront_public_key      = module.iam.cloudfront_public_key
}

# DNS Module (only if domain is provided)
module "dns" {
  count  = var.domain_name != "" ? 1 : 0
  source = "../../modules/dns"

  project_name = var.project_name
  environment  = local.environment
  domain_name  = var.domain_name
  parent_domain_name = var.parent_domain_name
  common_tags  = local.common_tags

  create_route53_zone        = var.create_route53_zone
  create_dns_records         = true
  create_www_record          = var.create_www_record
  create_cloudfront_records  = var.create_cloudfront_records
  subject_alternative_names  = concat(
    var.create_www_record ? ["www.${var.domain_name}"] : [],
    var.api_domain_name != "" ? [var.api_domain_name] : []
  )
  # CloudFront variables not passed to avoid circular dependency
  # DNS records will be created manually in the main configuration
  alb_dns_name               = module.networking.alb_dns_name
  alb_hosted_zone_id         = module.networking.alb_hosted_zone_id
  api_domain_name            = var.api_domain_name
}

# Compute Module
module "compute" {
  source = "../../modules/compute"

  project_name = var.project_name
  environment  = local.environment
  aws_region   = var.aws_region
  common_tags  = local.common_tags

  public_subnet_ids      = module.networking.public_subnets
  ecs_security_group_id   = module.networking.ecs_security_group_id
  ecs_execution_role_arn  = module.iam.ecs_execution_role_arn
  ecs_task_role_arn       = module.iam.ecs_task_role_arn
  alb_target_group_arn    = module.networking.alb_target_group_arn
  alb_listener_dependency = module.networking.alb_listener_dependency
  backend_port            = var.backend_port
  task_cpu                = var.task_cpu
  task_memory             = var.task_memory
  desired_count           = var.backend_desired_count
  log_retention_days      = var.log_retention_days
  db_credentials_secret_arn = module.database.db_master_user_secret_arn

  container_environment = [
    {
      name  = "ENVIRONMENT"
      value = local.environment
    },
    {
      name  = "DEBUG"
      value = "false"
    },
    {
      name  = "ALLOWED_ORIGINS"
      value = var.domain_name != "" ? "https://${var.domain_name}" : "*"
    },
    {
      name  = "ALLOWED_HOSTS"
      value = "${module.networking.alb_dns_name}${var.domain_name != "" ? ",${module.storage.cloudfront_domain_name}" : ""}"
    },
    {
      name  = "USE_IAM_DATABASE_AUTH"
      value = var.db_iam_database_authentication_enabled ? "true" : "false"
    },
    {
      name  = "DATABASE_PORT"
      value = "5432"
    },
    {
      name  = "DATABASE_CREDENTIALS_SECRET_ARN"
      value = module.database.db_master_user_secret_arn
    },
    {
      name  = "DATABASE_CREDENTIALS_CACHE_TTL"
      value = "300"
    },
    {
      name  = "ENFORCE_TLS"
      value = "true"
    },
    {
      name  = "SSL_VERIFY_CERTIFICATES"
      value = "true"
    },
    {
      name  = "SSL_VERIFY_CERTIFICATES_DEV"
      value = "true"
    },
    {
      name  = "RESUMES_S3_BUCKET"
      value = module.storage.resumes_s3_bucket_name
    },
        {
          name  = "RESUMES_CLOUDFRONT_DOMAIN"
          value = module.storage.resumes_cloudfront_domain_name
        },
        {
          name  = "CLOUDFRONT_KEY_PAIR_ID"
          value = module.storage.cloudfront_public_key_id
        },
        {
          name  = "CLOUDFRONT_PRIVATE_KEY_PATH"
          value = "/app/cloudfront_private_key.pem"
        }
  ]

  container_secrets = concat([
    {
      name      = "GOOGLE_CLIENT_ID"
      valueFrom = module.iam.google_client_id_parameter_arn
    },
    {
      name      = "GOOGLE_CLIENT_SECRET"
      valueFrom = module.iam.google_client_secret_parameter_arn
    },
    {
      name      = "GITHUB_CLIENT_ID"
      valueFrom = module.iam.github_client_id_parameter_arn
    },
    {
      name      = "GITHUB_CLIENT_SECRET"
      valueFrom = module.iam.github_client_secret_parameter_arn
    },
    {
      name      = "OPENROUTER_API_KEY"
      valueFrom = module.iam.openrouter_api_key_parameter_arn
    },
    {
      name      = "DATABASE_HOST"
      valueFrom = module.iam.database_host_parameter_arn
    },
    {
      name      = "DATABASE_NAME"
      valueFrom = module.iam.database_name_parameter_arn
    },
    {
      name      = "DATABASE_USER"
      valueFrom = module.iam.database_user_parameter_arn
    },
    {
      name      = "SECRET_KEY"
      valueFrom = module.iam.secret_key_parameter_arn
    },
    {
      name      = "CLOUDFRONT_PRIVATE_KEY"
      valueFrom = module.iam.cloudfront_private_key_parameter_arn
    },
    {
      name      = "OPENROUTER_LLM_MODEL"
      valueFrom = module.iam.openrouter_llm_model_parameter_arn
    },
    {
      name      = "SSL_CIPHER_SUITES"
      valueFrom = module.iam.ssl_cipher_suites_parameter_arn
    },
    {
      name      = "MIN_TLS_VERSION"
      valueFrom = module.iam.min_tls_version_parameter_arn
    }
  ],
  # Conditionally add database credentials secret only if not using IAM auth
  var.db_iam_database_authentication_enabled ? [] : [
    {
      name      = "DATABASE_CREDENTIALS"
      valueFrom = module.database.db_master_user_secret_arn
    }
  ])
}

# DNS Records for CloudFront (created after both DNS and Storage modules to avoid circular dependency)
resource "aws_route53_record" "main_domain" {
  count   = var.domain_name != "" && var.create_cloudfront_records && length(module.dns) > 0 ? 1 : 0
  zone_id = module.dns[0].route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.storage.cloudfront_domain_name
    zone_id                = module.storage.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "www_domain" {
  count   = var.domain_name != "" && var.create_cloudfront_records && var.create_www_record && length(module.dns) > 0 ? 1 : 0
  zone_id = module.dns[0].route53_zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.storage.cloudfront_domain_name
    zone_id                = module.storage.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# Jump host for database access
module "jump_host" {
  source = "../../modules/jump-host"

  project_name              = var.project_name
  environment              = local.environment
  vpc_id                   = module.networking.vpc_id
  database_subnet_id        = module.networking.database_subnets[0]
  database_host            = module.database.db_endpoint
  database_port            = module.database.db_port
  database_security_group_id = module.database.db_security_group_id
  instance_type            = "t3.micro"

  common_tags = local.common_tags
}