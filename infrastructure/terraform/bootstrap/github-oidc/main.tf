###############################################################################
# One-time bootstrap: IAM role that GitHub Actions assumes via OIDC to deploy
# production. Run manually once (needs admin credentials):
#
#   terraform init && terraform apply
#
# Then set the `role_arn` output as the AWS_ROLE_ARN variable of the GitHub
# "production" environment. Uses the GitHub OIDC provider already in the account.
###############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "resumerepublic-terraform-state"
    key            = "bootstrap/github-oidc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "github_repo" {
  type    = string
  default = "JaHyoty/ResumeRepublic.com"
}

variable "github_environment" {
  description = "GitHub environment allowed to assume the role"
  type        = string
  default     = "production"
}

variable "project_name" {
  type    = string
  default = "resumerepublic"
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_deploy" {
  name = "${var.project_name}-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:environment:${var.github_environment}"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "deploy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ManagedServices"
        Effect = "Allow"
        Action = [
          "lambda:*",
          "apigateway:*",
          "dynamodb:*",
          "s3:*",
          "cloudfront:*",
          "route53:*",
          "acm:*",
          "ssm:*",
          "logs:*",
          "ecr:*",
          "kms:Describe*",
          "kms:List*",
          "kms:Decrypt",
          "sts:GetCallerIdentity",
        ]
        Resource = "*"
      },
      {
        # Terraform manages the Lambda execution role; limit IAM to project-named resources
        Sid    = "ProjectIam"
        Effect = "Allow"
        Action = "iam:*"
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-*",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.project_name}-*",
        ]
      },
      {
        Sid      = "IamReadOnly"
        Effect   = "Allow"
        Action   = ["iam:Get*", "iam:List*"]
        Resource = "*"
      },
    ]
  })
}

output "role_arn" {
  description = "Set as the AWS_ROLE_ARN variable in the GitHub production environment"
  value       = aws_iam_role.github_deploy.arn
}
