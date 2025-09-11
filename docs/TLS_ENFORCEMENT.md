# TLS Enforcement for External LLM Service Calls

This document describes the TLS (Transport Layer Security) enforcement implemented in the CareerPathPro backend to ensure secure communication with external LLM services.

## 🔐 Overview

The backend enforces TLS for all external API calls, particularly to LLM services like OpenRouter, OpenAI, and Anthropic. This ensures that:

- All data transmitted to/from LLM services is encrypted
- Certificate validation prevents man-in-the-middle attacks
- Only secure cipher suites are used
- Insecure protocols (SSLv2, SSLv3, TLSv1.0, TLSv1.1) are disabled

## ⚙️ Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# SSL/TLS Configuration for External API Calls
ENFORCE_TLS=true
SSL_VERIFY_CERTIFICATES=true
SSL_CIPHER_SUITES=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS
MIN_TLS_VERSION=TLSv1.2
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `ENFORCE_TLS` | `true` | Enable/disable TLS enforcement |
| `SSL_VERIFY_CERTIFICATES` | `true` | Enable/disable certificate verification |
| `SSL_CIPHER_SUITES` | `ECDHE+AESGCM:...` | Allowed cipher suites |
| `MIN_TLS_VERSION` | `TLSv1.2` | Minimum TLS version (TLSv1.2 or TLSv1.3) |

## 🛠️ Implementation Details

### Backend LLM Service

The `LLMService` class in `backend/app/services/llm_service.py` uses:

1. **Secure SSL Context**: Created with `ssl.create_default_context()`
2. **Requests Session**: Configured with TLS enforcement
3. **Custom SSL Adapter**: Enforces cipher suites and protocol versions
4. **Certificate Verification**: Validates server certificates

### TLS Utility Module

The `backend/app/utils/tls_utils.py` provides:

- `create_secure_ssl_context()`: Creates SSL context with security settings
- `create_requests_session()`: Creates requests session with TLS enforcement
- `create_httpx_client()`: Creates httpx client with TLS enforcement
- `validate_tls_configuration()`: Validates TLS configuration
- `get_tls_info()`: Returns current TLS configuration info

## 🔒 Security Features

### Cipher Suite Enforcement

Only secure cipher suites are allowed:
- `ECDHE+AESGCM`: Elliptic Curve Diffie-Hellman with AES-GCM
- `ECDHE+CHACHA20`: Elliptic Curve Diffie-Hellman with ChaCha20
- `DHE+AESGCM`: Diffie-Hellman with AES-GCM
- `DHE+CHACHA20`: Diffie-Hellman with ChaCha20

Insecure ciphers are explicitly disabled:
- `!aNULL`: No anonymous key exchange
- `!MD5`: No MD5-based ciphers
- `!DSS`: No DSS-based ciphers

### Protocol Version Enforcement

- **Disabled**: SSLv2, SSLv3, TLSv1.0, TLSv1.1
- **Enabled**: TLSv1.2, TLSv1.3 (configurable minimum)

### Certificate Validation

- **Hostname Verification**: Ensures certificate matches the hostname
- **Certificate Chain Validation**: Verifies the entire certificate chain
- **Revocation Checking**: Uses system certificate store for revocation

## 🧪 Testing

### Run TLS Enforcement Tests

```bash
# Test TLS configuration and enforcement
python scripts/test-tls-enforcement.py
```

The test script verifies:
- SSL context creation
- Requests session configuration
- TLS configuration validation
- Cipher suite configuration
- OpenRouter API connection

### Manual Testing

```python
from backend.app.services.llm_service import LLMService

# Create LLM service instance
llm_service = LLMService()

# Check TLS configuration
print(f"TLS enforcement: {llm_service.session.verify}")
print(f"Session timeout: {llm_service.session.timeout}")
```

## 🚨 Error Handling

### SSL/TLS Errors

The system handles various SSL/TLS errors:

```python
except requests.exceptions.SSLError as e:
    logger.error(f"SSL/TLS error: {str(e)}")
    raise Exception(f"SSL/TLS connection failed: {str(e)}")

except requests.exceptions.ConnectionError as e:
    if "SSL" in str(e) or "TLS" in str(e):
        logger.error(f"TLS connection error: {str(e)}")
        raise Exception(f"TLS connection failed: {str(e)}")
```

### Common Error Scenarios

1. **Certificate Verification Failed**
   - **Cause**: Invalid or self-signed certificate
   - **Solution**: Check certificate validity or disable verification (not recommended)

2. **Cipher Suite Mismatch**
   - **Cause**: Server doesn't support configured cipher suites
   - **Solution**: Update `SSL_CIPHER_SUITES` configuration

3. **TLS Version Mismatch**
   - **Cause**: Server doesn't support minimum TLS version
   - **Solution**: Lower `MIN_TLS_VERSION` or update server

## 🔧 Troubleshooting

### Disable TLS Enforcement (Not Recommended)

```bash
# In .env file
ENFORCE_TLS=false
SSL_VERIFY_CERTIFICATES=false
```

**Warning**: This disables all TLS security and should only be used for debugging.

### Debug TLS Issues

```python
import logging
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
```

### Check TLS Configuration

```python
from backend.app.utils.tls_utils import get_tls_info
print(get_tls_info())
```

## 📚 Best Practices

1. **Always Use HTTPS**: Never make LLM API calls over HTTP
2. **Verify Certificates**: Keep `SSL_VERIFY_CERTIFICATES=true`
3. **Use Strong Ciphers**: Use the provided cipher suite configuration
4. **Monitor Logs**: Watch for SSL/TLS errors in application logs
5. **Regular Updates**: Keep SSL/TLS libraries updated
6. **Test Configuration**: Run TLS tests after configuration changes

## 🔍 Monitoring

### Log Messages

The system logs TLS-related information:

```
INFO: TLS enforcement enabled for LLM API calls (min version: TLSv1.2)
INFO: Configured requests session with TLS enforcement
WARNING: TLS enforcement is disabled for LLM API calls
ERROR: SSL/TLS error when connecting to OpenRouter API: [error details]
```

### Health Check

Add TLS status to health checks:

```python
@app.get("/health")
async def health_check():
    tls_info = get_tls_info()
    return {
        "status": "healthy",
        "tls_enforcement": tls_info["enforce_tls"],
        "ssl_verification": tls_info["verify_certificates"]
    }
```

## 🚀 Production Deployment

### Environment Variables

```bash
# Production TLS configuration
ENFORCE_TLS=true
SSL_VERIFY_CERTIFICATES=true
SSL_CIPHER_SUITES=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS
MIN_TLS_VERSION=TLSv1.3
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - ENFORCE_TLS=true
      - SSL_VERIFY_CERTIFICATES=true
      - MIN_TLS_VERSION=TLSv1.3
```

### Kubernetes Configuration

```yaml
# deployment.yaml
env:
- name: ENFORCE_TLS
  value: "true"
- name: SSL_VERIFY_CERTIFICATES
  value: "true"
- name: MIN_TLS_VERSION
  value: "TLSv1.3"
```

## 📖 References

- [Python SSL Documentation](https://docs.python.org/3/library/ssl.html)
- [Requests SSL Documentation](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [TLS Cipher Suites](https://ciphersuite.info/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
