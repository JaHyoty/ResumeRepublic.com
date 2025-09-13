# Security Best Practices

This document outlines the security measures implemented in the ResumeRepublic Terraform infrastructure and provides guidance for maintaining security best practices.

## 🔐 Password Management

### Database Passwords

**AWS Managed Master User Password**:
- RDS master user password is managed by AWS
- Automatic rotation every 30 days (configurable)
- No manual password management required
- Passwords are never stored in Terraform state or configuration files

**Secrets Manager Integration**:
- Database credentials stored in AWS Secrets Manager
- Encrypted using AWS KMS
- ECS tasks retrieve credentials at runtime
- Audit trail for all secret access

### Application Secrets

**SSM Parameter Store**:
- OAuth credentials and API keys stored in SSM Parameter Store
- All parameters encrypted using AWS managed keys
- Fine-grained IAM access control
- No secrets in Terraform state or configuration files

## 🛡️ Network Security

### VPC Configuration
- **Private Subnets**: Backend services (ECS tasks)
- **Database Subnets**: Database tier (RDS) - isolated from backend
- **Public Subnets**: Load balancer and NAT Gateway
- **Network Isolation**: Database and backend services in separate subnets
- **NAT Gateway**: Outbound internet access for private resources
- **No Direct Internet Access**: Private resources cannot be reached from internet

### Security Groups
- **RDS Security Group**: 
  - Only allows PostgreSQL access from backend subnets (10.0.1.0/24, 10.0.2.0/24)
  - Only allows PostgreSQL access from database subnets (10.0.10.0/24, 10.0.20.0/24)
  - No direct internet access
- **ECS Security Group**: Allows inbound traffic on application port from ALB
- **ALB Security Group**: Allows HTTP/HTTPS traffic from internet
- **Principle of Least Privilege**: Each security group has minimal required permissions

### Load Balancer
- Application Load Balancer in public subnets
- HTTPS termination with ACM certificates
- Health checks configured for application availability

## 🔒 Data Encryption

### Encryption at Rest
- **RDS**: Storage encryption enabled using AWS managed keys
- **S3**: Server-side encryption for frontend assets
- **Secrets Manager**: All secrets encrypted with AWS KMS
- **SSM Parameters**: All parameters encrypted with AWS managed keys

### Encryption in Transit
- **HTTPS**: All web traffic encrypted with TLS 1.2+
- **Database**: SSL/TLS encryption for database connections
- **API**: All API communications encrypted

## 🔑 Access Control

### IAM Roles and Policies
- **ECS Execution Role**: Minimal permissions for container execution
- **ECS Task Role**: Application-specific permissions
- **EC2 SSM Role**: Systems Manager access for dev machines
- **Principle of Least Privilege**: Each role has only required permissions

### Resource Tagging
- Consistent tagging strategy for all resources
- Environment-based resource separation
- Cost allocation and security compliance

## 🔍 Monitoring and Logging

### CloudWatch Logs
- Application logs stored in CloudWatch
- Log retention policies configured per environment
- Centralized logging for troubleshooting

### CloudTrail (Recommended)
- Enable AWS CloudTrail for API call logging
- Monitor secret access and configuration changes
- Set up alerts for suspicious activities

### VPC Flow Logs (Recommended)
- Enable VPC Flow Logs for network monitoring
- Monitor network traffic patterns
- Detect unusual network activity

## 🚨 Security Recommendations

### Immediate Actions
1. **Enable CloudTrail**: Set up AWS CloudTrail for audit logging
2. **VPC Flow Logs**: Enable VPC Flow Logs for network monitoring
3. **WAF**: Consider AWS WAF for additional web application protection
4. **GuardDuty**: Enable AWS GuardDuty for threat detection

### Regular Maintenance
1. **Password Rotation**: Verify automatic password rotation is working
2. **Security Updates**: Keep all dependencies and base images updated
3. **Access Reviews**: Regularly review IAM permissions and access patterns
4. **Backup Testing**: Test backup and recovery procedures

### Monitoring
1. **Secret Access**: Monitor access to secrets and parameters
2. **Network Traffic**: Review VPC Flow Logs for anomalies
3. **Resource Changes**: Monitor for unexpected infrastructure changes
4. **Cost Monitoring**: Set up billing alerts for unexpected costs

## 🔧 Security Configuration

### Environment-Specific Security

**Development Environment**:
- Shorter log retention (3 days)
- Skip final snapshot for easier cleanup
- EC2 SSM role enabled for dev access
- Debug mode enabled

**Production Environment**:
- Longer log retention (7 days)
- Final snapshot required
- No EC2 SSM role
- Debug mode disabled
- Performance monitoring available

### Secret Rotation

**Database Passwords**:
- Automatic rotation every 30 days
- No application downtime during rotation
- Credentials updated in Secrets Manager automatically

**Application Secrets**:
- All secrets managed through SSM Parameter Store
- Comprehensive coverage of all configuration values
- Manual rotation for OAuth credentials and API keys
- Update SSM parameters when secrets change
- Restart ECS services to pick up new secrets

**Secrets Managed in Parameter Store**:
- OAuth credentials (Google, GitHub)
- API keys (OpenRouter)
- Application configuration (Redis, service URLs)
- SSL/TLS configuration
- AWS credentials (optional)
- Database connection details (host, name, user)
- Application secret key
- Database credentials (via Secrets Manager)

## 🔍 Secrets Validation

### Validation Script
Use the provided script to validate all secrets are properly configured:

```bash
./scripts/validate-secrets.sh
```

This script checks:
- All required SSM parameters exist
- Secrets Manager secrets are accessible
- IAM permissions are correctly configured
- Provides guidance for missing secrets

### Manual Validation
You can also manually check secrets:

```bash
# List all secrets
aws ssm get-parameters-by-path --path "/resumerepublic" --recursive

# Check specific secret
aws ssm get-parameter --name "/resumerepublic/database/password" --with-decryption
```

## 📋 Security Checklist

### Pre-Deployment
- [ ] Review all IAM permissions
- [ ] Verify security group rules
- [ ] Check encryption settings
- [ ] Validate secret management configuration
- [ ] Run secrets validation script

### Post-Deployment
- [ ] Test secret access from applications
- [ ] Verify password rotation is working
- [ ] Check CloudWatch logs
- [ ] Test backup and recovery procedures

### Ongoing
- [ ] Monitor secret access patterns
- [ ] Review and update IAM policies
- [ ] Check for security updates
- [ ] Audit resource access logs

## 🆘 Incident Response

### Security Incident Response Plan
1. **Detection**: Monitor CloudTrail, VPC Flow Logs, and application logs
2. **Assessment**: Determine scope and impact of the incident
3. **Containment**: Isolate affected resources
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve security measures

### Emergency Procedures
- **Secret Compromise**: Rotate all affected secrets immediately
- **Network Breach**: Review and update security groups
- **Resource Compromise**: Terminate and recreate affected resources
- **Data Breach**: Follow data breach notification procedures

## 📚 Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [AWS Well-Architected Security Pillar](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Security Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## 🤝 Security Contact

For security-related questions or to report security issues:
- Review this documentation first
- Check AWS Security Center
- Contact your security team
- Follow your organization's security procedures
