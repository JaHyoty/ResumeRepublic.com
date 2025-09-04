# Environment Variables Setup Guide

## 🔐 Security Best Practices

**NEVER commit secrets to version control!** All sensitive configuration should be provided via environment variables.

## 📋 Required Environment Variables

### Backend Service

```bash
# Environment
ENVIRONMENT=production  # or development
DEBUG=false  # Set to false in production

# Database (REQUIRED)
DATABASE_URL=postgresql://username:password@host:port/database
DATABASE_URL_ASYNC=postgresql+asyncpg://username:password@host:port/database

# Security (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-here  # Generate with: openssl rand -hex 32

# OAuth Providers (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret

# External Services
PARSING_SERVICE_URL=http://parsing-service:8001
REDIS_URL=redis://redis:6379

# AWS (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1

# CORS (Configure for your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Parsing Service

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# External Services
BACKEND_URL=http://backend:8000

# LLM Configuration (At least one required)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_LLM_PROVIDER=openai

# AWS (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000
```

## 🚀 Quick Setup

### 1. Copy Environment Template

```bash
cp env.example .env
```

### 2. Generate Secure Secret Key

```bash
# Generate a secure secret key
openssl rand -hex 32
```

### 3. Configure Database

```bash
# For local development
DATABASE_URL=postgresql://user:password@localhost:5432/careerpathpro

# For production (example)
DATABASE_URL=postgresql://prod_user:secure_password@db.example.com:5432/careerpathpro_prod
```

### 4. Set Up OAuth Providers

1. **Google OAuth**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs

2. **GitHub OAuth**:
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - Create new OAuth App
   - Set callback URL

3. **Apple OAuth**:
   - Go to [Apple Developer Console](https://developer.apple.com/)
   - Create Sign in with Apple service

## 🔒 Production Security Checklist

- [ ] All secrets are in environment variables
- [ ] No hardcoded credentials in code
- [ ] Database uses strong passwords
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Secret keys are cryptographically secure
- [ ] Environment variables are not logged
- [ ] `.env` files are in `.gitignore`

## 🐳 Docker Environment Variables

### Using Docker Compose

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/careerpathpro
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    env_file:
      - .env
```

### Using Docker Secrets (Production)

```yaml
# docker-compose.prod.yml
services:
  backend:
    secrets:
      - db_password
      - secret_key
    environment:
      - DATABASE_URL=postgresql://user:${DB_PASSWORD}@postgres:5432/careerpathpro

secrets:
  db_password:
    external: true
  secret_key:
    external: true
```

## 🔍 Environment Validation

The application automatically validates required settings:

- **Development**: Uses defaults, warns about missing optional settings
- **Production**: Fails to start if required settings are missing or using default values

## 📝 Example .env File

```bash
# Development Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/careerpathpro
DATABASE_URL_ASYNC=postgresql+asyncpg://user:password@localhost:5432/careerpathpro

# Security
SECRET_KEY=your-generated-secret-key-here

# OAuth (Optional for development)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# External Services
PARSING_SERVICE_URL=http://localhost:8001
REDIS_URL=redis://localhost:6379

# LLM (Required for parsing service)
OPENAI_API_KEY=your-openai-api-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
ALLOWED_HOSTS=localhost,127.0.0.1
```

## ⚠️ Security Warnings

1. **Never commit `.env` files** to version control
2. **Rotate secrets regularly** in production
3. **Use different secrets** for different environments
4. **Monitor access logs** for suspicious activity
5. **Use least privilege** for AWS credentials
6. **Enable MFA** on all service accounts
