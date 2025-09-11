#!/bin/bash

# Setup development SSL configuration
# This script helps configure SSL for development environments

echo "🔧 Setting up development SSL configuration..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
fi

# Set development SSL settings
echo "🔒 Configuring SSL for development environment..."

# Update .env file with development SSL settings
if grep -q "SSL_VERIFY_CERTIFICATES_DEV" .env; then
    # Update existing setting
    sed -i 's/SSL_VERIFY_CERTIFICATES_DEV=.*/SSL_VERIFY_CERTIFICATES_DEV=false/' .env
else
    # Add new setting
    echo "" >> .env
    echo "# Development SSL Configuration" >> .env
    echo "SSL_VERIFY_CERTIFICATES_DEV=false" >> .env
fi

# Ensure environment is set to development
if grep -q "ENVIRONMENT=" .env; then
    sed -i 's/ENVIRONMENT=.*/ENVIRONMENT=development/' .env
else
    echo "ENVIRONMENT=development" >> .env
fi

echo "✅ Development SSL configuration updated!"
echo ""
echo "📋 Current SSL settings:"
echo "   - ENFORCE_TLS: true (TLS encryption enabled)"
echo "   - SSL_VERIFY_CERTIFICATES: true (for production)"
echo "   - SSL_VERIFY_CERTIFICATES_DEV: false (for development)"
echo "   - ENVIRONMENT: development"
echo ""
echo "⚠️  WARNING: Certificate verification is disabled for development only!"
echo "   This should NEVER be used in production."
echo ""
echo "🚀 You can now start your backend with:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "🧪 Test the configuration with:"
echo "   python scripts/test-tls-enforcement.py"
