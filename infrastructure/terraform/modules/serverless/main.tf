###############################################################################
# Serverless Module — API Gateway + Lambda + DynamoDB
# Replaces: networking, compute, database, and jump-host modules
###############################################################################

# ---------------------------------------------------------------
# DynamoDB Table (single-table design, pay-per-request)
# ---------------------------------------------------------------

resource "aws_dynamodb_table" "main" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  deletion_protection_enabled = true

  tags = merge(var.tags, {
    Name = var.dynamodb_table_name
  })
}

# ---------------------------------------------------------------
# Lambda Function (container image)
# ---------------------------------------------------------------

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = var.lambda_role_arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  timeout       = 30   # API requests only — no heavy processing
  memory_size   = 256  # Lightweight — no LaTeX or Playwright

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      DYNAMODB_TABLE_NAME      = aws_dynamodb_table.main.name
      AWS_REGION_OVERRIDE      = var.aws_region
      RESUMES_S3_BUCKET        = var.resumes_s3_bucket
      RESUMES_CLOUDFRONT_DOMAIN = var.resumes_cloudfront_domain
      SECRET_KEY               = var.secret_key
      GOOGLE_CLIENT_ID         = var.google_client_id
      GOOGLE_CLIENT_SECRET     = var.google_client_secret
      GITHUB_CLIENT_ID         = var.github_client_id
      GITHUB_CLIENT_SECRET     = var.github_client_secret
      OPENROUTER_API_KEY       = var.openrouter_api_key
      OPENROUTER_LLM_MODEL     = var.openrouter_llm_model
      COOKIE_DOMAIN            = var.cookie_domain
      COOKIE_SECURE            = "true"
      COOKIE_SAMESITE          = var.cookie_domain != "" ? "lax" : "none"
      ALLOWED_ORIGINS          = join(",", var.allowed_origins)
      PDF_LAMBDA_NAME          = "${var.project_name}-pdf"
      SCRAPER_LAMBDA_NAME      = "${var.project_name}-scraper"
      ALLOWED_HOSTS            = "*"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-api"
  })
}

# CloudWatch Log Group for API Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14

  tags = var.tags
}

# ---------------------------------------------------------------
# PDF Worker Lambda (LaTeX resume generation)
# ---------------------------------------------------------------

resource "aws_lambda_function" "pdf" {
  function_name = "${var.project_name}-pdf"
  role          = var.lambda_role_arn
  package_type  = "Image"
  image_uri     = var.pdf_lambda_image_uri
  timeout       = 300   # 5 minutes for LaTeX compilation
  memory_size   = 2048  # LaTeX needs memory

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      DYNAMODB_TABLE_NAME      = aws_dynamodb_table.main.name
      AWS_REGION_OVERRIDE      = var.aws_region
      RESUMES_S3_BUCKET        = var.resumes_s3_bucket
      RESUMES_CLOUDFRONT_DOMAIN = var.resumes_cloudfront_domain
      OPENROUTER_API_KEY       = var.openrouter_api_key
      OPENROUTER_LLM_MODEL     = var.openrouter_llm_model
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-pdf"
  })
}

resource "aws_cloudwatch_log_group" "pdf_lambda" {
  name              = "/aws/lambda/${var.project_name}-pdf"
  retention_in_days = 14
  tags              = var.tags
}

# ---------------------------------------------------------------
# Scraper Worker Lambda (Playwright web scraping)
# ---------------------------------------------------------------

resource "aws_lambda_function" "scraper" {
  function_name = "${var.project_name}-scraper"
  role          = var.lambda_role_arn
  package_type  = "Image"
  image_uri     = var.scraper_lambda_image_uri
  timeout       = 120   # 2 minutes for web scraping
  memory_size   = 1024  # Chromium needs memory

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main.name
      AWS_REGION_OVERRIDE = var.aws_region
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-scraper"
  })
}

resource "aws_cloudwatch_log_group" "scraper_lambda" {
  name              = "/aws/lambda/${var.project_name}-scraper"
  retention_in_days = 14
  tags              = var.tags
}

# ---------------------------------------------------------------
# API Gateway HTTP API
# ---------------------------------------------------------------

resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins     = var.allowed_origins
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["Content-Type", "Authorization", "Cookie"]
    allow_credentials = contains(var.allowed_origins, "*") ? false : true
    max_age           = 3600
  }

  tags = var.tags
}

# Lambda integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

# Default route — catch all requests
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Auto-deploy stage
resource "aws_apigatewayv2_stage" "production" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  tags = var.tags
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 14

  tags = var.tags
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# ---------------------------------------------------------------
# Custom Domain (api.resumerepublic.com)
# ---------------------------------------------------------------

resource "aws_apigatewayv2_domain_name" "api" {
  count       = var.custom_domain != "" ? 1 : 0
  domain_name = var.custom_domain

  domain_name_configuration {
    certificate_arn = var.acm_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = var.tags
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count       = var.custom_domain != "" ? 1 : 0
  api_id      = aws_apigatewayv2_api.main.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.production.id
}
