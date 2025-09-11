"""
TLS/SSL utilities for enforcing secure connections to external services
"""

import ssl
import logging
import requests
import httpx
from typing import Optional
from app.core.config import settings
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Use structlog for consistent logging
import structlog
logger = structlog.get_logger(__name__)


def create_secure_ssl_context() -> ssl.SSLContext:
    """
    Create a secure SSL context with TLS enforcement
    """
    context = ssl.create_default_context()
    
    # Configure certificate verification
    # Use development setting if in development environment
    verify_certs = settings.SSL_VERIFY_CERTIFICATES
    if settings.ENVIRONMENT == "development" and settings.SSL_VERIFY_CERTIFICATES_DEV is not None:
        verify_certs = settings.SSL_VERIFY_CERTIFICATES_DEV
        if not verify_certs:
            logger.warning("SSL certificate verification is disabled for development environment")
    
    # Configure certificate verification
    if verify_certs:
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        # For development mode without certificate verification
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    
    # Set minimum TLS version
    if settings.MIN_TLS_VERSION == "TLSv1.3":
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
    elif settings.MIN_TLS_VERSION == "TLSv1.2":
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
    
    # Disable insecure protocols
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    
    # Set cipher suites
    if hasattr(context, 'set_ciphers'):
        context.set_ciphers(settings.SSL_CIPHER_SUITES)
    
    logger.info(f"Created SSL context with TLS enforcement", 
                min_version=settings.MIN_TLS_VERSION,
                verify_certificates=verify_certs,
                check_hostname=context.check_hostname,
                verify_mode=context.verify_mode)
    return context


def create_requests_session() -> 'requests.Session':
    """
    Create a requests session with TLS enforcement
    """
    
    # Use development setting if in development environment
    verify_certs = settings.SSL_VERIFY_CERTIFICATES
    if settings.ENVIRONMENT == "development" and settings.SSL_VERIFY_CERTIFICATES_DEV is not None:
        verify_certs = settings.SSL_VERIFY_CERTIFICATES_DEV
        if not verify_certs:
            logger.warning("SSL certificate verification is disabled for development environment")
    
    session = requests.Session()
    session.verify = verify_certs
    session.timeout = 60
    
    if settings.ENFORCE_TLS:
        # For development with certificate verification disabled, use simple configuration
        if settings.ENVIRONMENT == "development" and not verify_certs:
            logger.info("Configured requests session with TLS enforcement (development mode)",
                       ssl_verify=verify_certs,
                       timeout=session.timeout,
                       note="Certificate verification disabled for development")
        else:
            # For production or when certificate verification is enabled
            class TLSEnforcingAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    context = create_urllib3_context()
                    context.set_ciphers(settings.SSL_CIPHER_SUITES)
                    context.options |= ssl.OP_NO_SSLv2
                    context.options |= ssl.OP_NO_SSLv3
                    context.options |= ssl.OP_NO_TLSv1
                    context.options |= ssl.OP_NO_TLSv1_1
                    if settings.MIN_TLS_VERSION == "TLSv1.3":
                        context.options |= ssl.OP_NO_TLSv1_2
                    kwargs['ssl_context'] = context
                    return super().init_poolmanager(*args, **kwargs)
            
            session.mount('https://', TLSEnforcingAdapter())
            logger.info("Configured requests session with TLS enforcement",
                       ssl_verify=verify_certs,
                       timeout=session.timeout,
                       cipher_suites=settings.SSL_CIPHER_SUITES[:50] + "...")
    else:
        logger.warning("TLS enforcement is disabled for requests session",
                      ssl_verify=verify_certs)
    
    return session


def create_httpx_client() -> 'httpx.AsyncClient':
    """
    Create an httpx client with TLS enforcement
    """
    # Use development setting if in development environment
    verify_certs = settings.SSL_VERIFY_CERTIFICATES
    if settings.ENVIRONMENT == "development" and settings.SSL_VERIFY_CERTIFICATES_DEV is not None:
        verify_certs = settings.SSL_VERIFY_CERTIFICATES_DEV
        if not verify_certs:
            logger.warning("SSL certificate verification is disabled for development environment")
    
    if settings.ENFORCE_TLS:
        # For development with certificate verification disabled, use simple configuration
        if settings.ENVIRONMENT == "development" and not verify_certs:
            client = httpx.AsyncClient(
                verify=False,
                timeout=60.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            logger.info("Configured httpx client with TLS enforcement (development mode)",
                       ssl_verify=verify_certs,
                       timeout=60.0,
                       note="Certificate verification disabled for development")
        else:
            # For production or when certificate verification is enabled
            ssl_context = create_secure_ssl_context()
            client = httpx.AsyncClient(
                verify=ssl_context,
                timeout=60.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            logger.info("Configured httpx client with TLS enforcement",
                       ssl_verify=verify_certs,
                       timeout=60.0,
                       cipher_suites=settings.SSL_CIPHER_SUITES[:50] + "...")
    else:
        client = httpx.AsyncClient(
            verify=False,
            timeout=60.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        logger.warning("TLS enforcement is disabled for httpx client",
                      ssl_verify=verify_certs)
    
    return client


def validate_tls_configuration() -> bool:
    """
    Validate that TLS configuration is properly set up
    """
    try:
        if not settings.ENFORCE_TLS:
            logger.warning("TLS enforcement is disabled")
            return False
        
        if not settings.SSL_VERIFY_CERTIFICATES:
            logger.warning("SSL certificate verification is disabled")
            return False
        
        # Test SSL context creation
        context = create_secure_ssl_context()
        if context.verify_mode == ssl.CERT_NONE:
            logger.error("SSL context created without certificate verification")
            return False
        
        logger.info("TLS configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"TLS configuration validation failed: {str(e)}")
        return False


def get_tls_info() -> dict:
    """
    Get information about the current TLS configuration
    """
    return {
        "enforce_tls": settings.ENFORCE_TLS,
        "verify_certificates": settings.SSL_VERIFY_CERTIFICATES,
        "min_tls_version": settings.MIN_TLS_VERSION,
        "cipher_suites": settings.SSL_CIPHER_SUITES,
        "ssl_version": ssl.OPENSSL_VERSION if hasattr(ssl, 'OPENSSL_VERSION') else "Unknown"
    }
