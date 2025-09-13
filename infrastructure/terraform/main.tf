# Main Terraform Configuration
# This file serves as the entry point and can be used for workspace management
# For environment-specific deployments, use the files in the environments/ directory

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# This file is kept for backward compatibility
# For new deployments, use the environment-specific configurations:
# - environments/production/ for production
# - environments/development/ for development

# To deploy:
# 1. Copy the appropriate environment directory
# 2. Update the variables in terraform.tfvars
# 3. Run terraform init, plan, and apply

output "message" {
  value = "This is the legacy main.tf file. Please use environment-specific configurations in the environments/ directory."
}