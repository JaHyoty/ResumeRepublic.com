# Secrets Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# External secrets configuration
variable "use_external_secrets" {
  description = "Whether to use external secrets from Secrets Manager"
  type        = bool
  default     = false
}

variable "external_secrets_name" {
  description = "Name of the external secrets in Secrets Manager"
  type        = string
  default     = ""
}

# OAuth Credentials
variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_client_id" {
  description = "GitHub OAuth Client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_client_secret" {
  description = "GitHub OAuth Client Secret"
  type        = string
  sensitive   = true
  default     = ""
}

# API Keys
variable "openrouter_api_key" {
  description = "OpenRouter API Key"
  type        = string
  sensitive   = true
  default     = ""
}

# Application Secrets
variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
  default     = ""
}

# Non-sensitive configuration

variable "openrouter_llm_model" {
  description = "OpenRouter LLM model"
  type        = string
  default     = "anthropic/claude-sonnet-4"
}

# SSL/TLS Configuration
variable "ssl_cipher_suites" {
  description = "SSL cipher suites"
  type        = string
  default     = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
}

variable "min_tls_version" {
  description = "Minimum TLS version"
  type        = string
  default     = "TLSv1.2"
}

# Database connection details
variable "database_host" {
  description = "Database host endpoint"
  type        = string
  default     = ""
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = ""
}

variable "database_user" {
  description = "Database username"
  type        = string
  default     = ""
}
