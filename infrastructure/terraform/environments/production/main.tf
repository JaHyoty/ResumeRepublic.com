###############################################################################
# Production Environment — Serverless Architecture
# API Gateway + Lambda + DynamoDB
###############################################################################

terraform {
  required_version = ">= 1.5.0"

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

  backend "s3" {
    bucket         = "resumerepublic-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  environment = "production"
  common_tags = {
    Project     = var.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------
# IAM Module (Lambda execution role + SSM parameters)
# ---------------------------------------------------------------
module "iam" {
  source = "../../modules/iam"

  project_name         = var.project_name
  environment          = local.environment
  aws_region           = var.aws_region
  common_tags          = local.common_tags
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  github_client_id     = var.github_client_id
  github_client_secret = var.github_client_secret
  openrouter_api_key   = var.openrouter_api_key
  openrouter_llm_model = var.openrouter_llm_model
  secret_key           = var.secret_key
}

# ---------------------------------------------------------------
# Storage Module (S3 + CloudFront for frontend + resume PDFs)
# ---------------------------------------------------------------
module "storage" {
  source = "../../modules/storage"

  project_name = var.project_name
  environment  = local.environment
  common_tags  = local.common_tags

  cloudfront_public_key      = data.aws_ssm_parameter.cloudfront_public_key.value
  cloudfront_aliases         = var.domain_name != "" ? (var.create_www_record ? [var.domain_name, "www.${var.domain_name}"] : [var.domain_name]) : []
  resumes_cloudfront_aliases = []
  acm_certificate_arn        = var.domain_name != "" ? module.dns[0].acm_certificate_validation_arn : null
  enable_spa_routing         = true
}

data "aws_ssm_parameter" "cloudfront_public_key" {
  name = "/${var.project_name}/${local.environment}/cloudfront/public_key"
}

data "aws_ssm_parameter" "secret_key" {
  name            = "/${var.project_name}/${local.environment}/app/secret_key"
  with_decryption = true
}

data "aws_ssm_parameter" "google_client_id" {
  name            = "/${var.project_name}/${local.environment}/google/client_id"
  with_decryption = true
}

data "aws_ssm_parameter" "google_client_secret" {
  name            = "/${var.project_name}/${local.environment}/google/client_secret"
  with_decryption = true
}

data "aws_ssm_parameter" "github_client_id" {
  name            = "/${var.project_name}/${local.environment}/github/client_id"
  with_decryption = true
}

data "aws_ssm_parameter" "github_client_secret" {
  name            = "/${var.project_name}/${local.environment}/github/client_secret"
  with_decryption = true
}

data "aws_ssm_parameter" "openrouter_api_key" {
  name            = "/${var.project_name}/${local.environment}/openrouter/api_key"
  with_decryption = true
}

data "aws_ssm_parameter" "openrouter_llm_model" {
  name = "/${var.project_name}/${local.environment}/app/openrouter_llm_model"
}

# ---------------------------------------------------------------
# Serverless Module (API Gateway + Lambda + DynamoDB)
# ---------------------------------------------------------------
module "serverless" {
  source = "../../modules/serverless"

  project_name        = var.project_name
  environment         = local.environment
  aws_region          = var.aws_region
  dynamodb_table_name = "${var.project_name}-${local.environment}"
  lambda_role_arn     = module.iam.lambda_execution_role_arn
  lambda_image_uri    = "${aws_ecr_repository.backend.repository_url}:latest"

  resumes_s3_bucket         = module.storage.resumes_s3_bucket_name
  resumes_cloudfront_domain = module.storage.resumes_cloudfront_domain_name
  secret_key                = data.aws_ssm_parameter.secret_key.value
  google_client_id          = data.aws_ssm_parameter.google_client_id.value
  google_client_secret      = data.aws_ssm_parameter.google_client_secret.value
  github_client_id          = data.aws_ssm_parameter.github_client_id.value
  github_client_secret      = data.aws_ssm_parameter.github_client_secret.value
  openrouter_api_key        = data.aws_ssm_parameter.openrouter_api_key.value
  openrouter_llm_model      = data.aws_ssm_parameter.openrouter_llm_model.value
  cookie_domain             = var.domain_name != "" ? ".${var.domain_name}" : ""

  allowed_origins = concat(
    var.domain_name != "" ? [
      "https://${var.domain_name}",
      "https://www.${var.domain_name}",
    ] : [
      "https://resumerepublic.com",
      "https://www.resumerepublic.com",
      "https://dev.resumerepublic.com",
    ],
    [
      "https://${module.storage.cloudfront_domain_name}",
    ]
  )

  custom_domain       = var.api_domain_name
  acm_certificate_arn = var.domain_name != "" ? module.dns[0].acm_certificate_validation_arn : ""

  tags = local.common_tags

  pdf_lambda_image_uri     = "${aws_ecr_repository.pdf.repository_url}:latest"
  scraper_lambda_image_uri = "${aws_ecr_repository.scraper.repository_url}:latest"
}

# ---------------------------------------------------------------
# ECR Repository (for Lambda container images)
# ---------------------------------------------------------------
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_repository" "pdf" {
  name                 = "${var.project_name}-pdf"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_repository" "scraper" {
  name                 = "${var.project_name}-scraper"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------
# DNS Module (Route53 + ACM)
# ---------------------------------------------------------------
module "dns" {
  count  = var.domain_name != "" ? 1 : 0
  source = "../../modules/dns"

  project_name       = var.project_name
  environment        = local.environment
  domain_name        = var.domain_name
  parent_domain_name = var.parent_domain_name
  common_tags        = local.common_tags

  create_route53_zone       = var.create_route53_zone
  create_dns_records        = true
  create_www_record         = var.create_www_record
  create_cloudfront_records = var.create_cloudfront_records
  subject_alternative_names = concat(
    var.create_www_record ? ["www.${var.domain_name}"] : [],
    var.api_domain_name != "" ? [var.api_domain_name] : []
  )

  # API Gateway domain for api.* record
  alb_dns_name       = module.serverless.custom_domain_target
  alb_hosted_zone_id = module.serverless.custom_domain_hosted_zone_id
  api_domain_name    = var.api_domain_name
}

# ---------------------------------------------------------------
# CloudFront DNS records
# ---------------------------------------------------------------
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
