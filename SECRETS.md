# Secrets Management Guide

This guide explains how secrets are managed securely across different environments for the ResumeRepublic application.

## 🔐 Secrets Strategy Overview

We use a multi-layered approach to secrets management:

1. **Local Development**: `terraform.tfvars` (gitignored)
2. **AWS Production**: Systems Manager Parameter Store
3. **CI/CD**: GitHub Secrets
4. **Runtime**: Environment variables in ECS

## 📁 File Structure

```
infrastructure/terraform/
├── terraform.tfvars.example  # Template (committed)
├── terraform.tfvars          # Local secrets (gitignored)
└── main.tf                   # Infrastructure code
```

## 🚀 Quick Setup

### 1. Initial Secrets Setup

Run the setup script to configure all secrets:

```bash
./scripts/setup-secrets.sh
```

This script will:
- Generate secure passwords and keys
- Prompt for OAuth credentials
- Create `terraform.tfvars` (gitignored)
- Store secrets in AWS Systems Manager Parameter Store
- Show you what GitHub secrets to add

### 2. Manual Setup (Alternative)

If you prefer to set up secrets manually:

```bash
# Copy the template
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars

# Edit with your values
nano infrastructure/terraform/terraform.tfvars
```

## 🔧 Secrets Configuration

### Required Secrets

| Secret | Description | Generated | Example |
|--------|-------------|-----------|---------|
| `db_password` | PostgreSQL password | ✅ Auto | `Kj8mN2pQ9vR4sT7wX1yZ5` |
| `secret_key` | JWT signing key | ✅ Auto | `a1b2c3d4e5f6...` |
| `google_client_id` | Google OAuth ID | ❌ Manual | `123456789.apps.googleusercontent.com` |
| `google_client_secret` | Google OAuth secret | ❌ Manual | `GOCSPX-abc123...` |
| `github_client_id` | GitHub OAuth ID | ❌ Manual | `Iv1.abc123def456` |
| `github_client_secret` | GitHub OAuth secret | ❌ Manual | `abc123def456...` |
| `openrouter_api_key` | OpenRouter API key | ❌ Manual | `sk-or-v1-abc123...` |

### OAuth App Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `https://your-cloudfront-domain.com/auth/google/callback`

#### GitHub OAuth
1. Go to [GitHub Settings → Developer settings → OAuth Apps](https://github.com/settings/developers)
2. Create new OAuth App
3. Set Authorization callback URL: `https://your-cloudfront-domain.com/auth/github/callback`

## ☁️ AWS Systems Manager Parameter Store

Secrets are automatically stored in AWS Systems Manager Parameter Store:

```
/resumerepublic/database/password
/resumerepublic/app/secret_key
/resumerepublic/google/client_id
/resumerepublic/google/client_secret
/resumerepublic/github/client_id
/resumerepublic/github/client_secret
/resumerepublic/openrouter/api_key
```

### Accessing Secrets in AWS

```bash
# List all secrets
aws ssm get-parameters-by-path --path "/resumerepublic" --recursive

# Get specific secret
aws ssm get-parameter --name "/resumerepublic/database/password" --with-decryption
```

## 🔄 CI/CD with GitHub Actions

### Required GitHub Secrets

Add these to your repository: Settings → Secrets and variables → Actions

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `AWS_ACCESS_KEY_ID` | AWS access key | From AWS IAM |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | From AWS IAM |
| `DB_PASSWORD` | Database password | From terraform.tfvars |
| `SECRET_KEY` | App secret key | From terraform.tfvars |
| `GOOGLE_CLIENT_ID` | Google OAuth ID | From OAuth setup |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | From OAuth setup |
| `GITHUB_CLIENT_ID` | GitHub OAuth ID | From OAuth setup |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | From OAuth setup |
| `OPENROUTER_API_KEY` | OpenRouter API key | From OpenRouter |

### GitHub Actions Usage

The workflow automatically uses these secrets:

```yaml
env:
  TF_VAR_db_password: ${{ secrets.DB_PASSWORD }}
  TF_VAR_secret_key: ${{ secrets.SECRET_KEY }}
  # ... other secrets
```

## 🏗️ Runtime Environment Variables

In ECS, secrets are injected as environment variables:

```hcl
environment = [
  {
    name  = "DATABASE_URL"
    value = "postgresql://user:password@host:5432/db"
  }
]

secrets = [
  {
    name      = "GOOGLE_CLIENT_ID"
    valueFrom = aws_ssm_parameter.google_client_id.arn
  }
]
```

## 🔒 Security Best Practices

### ✅ Do's
- Use `terraform.tfvars` for local development (gitignored)
- Store production secrets in AWS Systems Manager Parameter Store
- Use GitHub Secrets for CI/CD
- Generate strong, random passwords
- Rotate secrets regularly
- Use least privilege IAM policies

### ❌ Don'ts
- Never commit `terraform.tfvars` to git
- Don't hardcode secrets in code
- Don't use weak passwords
- Don't share secrets via email/chat
- Don't store secrets in environment files

## 🔄 Secret Rotation

### Rotating Database Password

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# 2. Update terraform.tfvars
sed -i "s/db_password = \".*\"/db_password = \"$NEW_PASSWORD\"/" infrastructure/terraform/terraform.tfvars

# 3. Update AWS Parameter Store
aws ssm put-parameter --name "/resumerepublic/database/password" --value "$NEW_PASSWORD" --type "SecureString" --overwrite

# 4. Update GitHub secret
# Go to GitHub → Settings → Secrets → Update DB_PASSWORD

# 5. Redeploy
./scripts/deploy.sh
```

### Rotating Application Secret Key

```bash
# 1. Generate new key
NEW_SECRET_KEY=$(openssl rand -hex 32)

# 2. Update terraform.tfvars
sed -i "s/secret_key = \".*\"/secret_key = \"$NEW_SECRET_KEY\"/" infrastructure/terraform/terraform.tfvars

# 3. Update AWS Parameter Store
aws ssm put-parameter --name "/resumerepublic/app/secret_key" --value "$NEW_SECRET_KEY" --type "SecureString" --overwrite

# 4. Update GitHub secret
# Go to GitHub → Settings → Secrets → Update SECRET_KEY

# 5. Redeploy
./scripts/deploy.sh
```

## 🚨 Emergency Procedures

### If Secrets Are Compromised

1. **Immediately rotate all secrets**:
   ```bash
   ./scripts/setup-secrets.sh
   ```

2. **Update GitHub secrets** with new values

3. **Redeploy immediately**:
   ```bash
   ./scripts/deploy.sh
   ```

4. **Revoke OAuth app credentials** and create new ones

5. **Check logs** for any unauthorized access

### Recovery Procedures

If you lose access to secrets:

1. **Database**: Reset password via AWS RDS console
2. **OAuth**: Create new OAuth apps
3. **API Keys**: Generate new keys from respective services
4. **Application**: Generate new secret key

## 📊 Monitoring

### CloudWatch Alarms

Set up alarms for:
- Failed authentication attempts
- Unusual API usage patterns
- Database connection failures

### Log Monitoring

Monitor these logs:
- ECS application logs
- CloudFront access logs
- RDS slow query logs

## 🔍 Troubleshooting

### Common Issues

1. **"Parameter not found"**: Check if secrets are stored in Parameter Store
2. **"Access denied"**: Verify IAM permissions for ECS task role
3. **"Invalid credentials"**: Check OAuth app configuration
4. **"Database connection failed"**: Verify database password and network access

### Debug Commands

```bash
# Check if secrets exist
aws ssm get-parameters-by-path --path "/resumerepublic" --recursive

# Test database connection
aws rds describe-db-instances --db-instance-identifier resumerepublic-db

# Check ECS task logs
aws logs tail /ecs/resumerepublic-backend --follow
```

## 📚 Additional Resources

- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Terraform Sensitive Variables](https://www.terraform.io/docs/language/values/variables.html#sensitive)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
