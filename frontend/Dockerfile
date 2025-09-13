# Simple build stage for React frontend
# This Dockerfile is only used for local development/testing
# In production, we use S3 + CloudFront directly

FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Simple HTTP server for local testing
FROM node:18-alpine

WORKDIR /app

# Install a simple HTTP server
RUN npm install -g serve

# Copy built files
COPY --from=builder /app/dist ./dist

# Expose port 3000
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start the server
CMD ["serve", "-s", "dist", "-l", "3000"]
