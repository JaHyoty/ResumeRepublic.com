-- Database initialization script for Docker
-- This script runs when the PostgreSQL container starts

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE careerpathpro'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'careerpathpro')\gexec

-- Connect to the careerpathpro database
\c careerpathpro;

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE careerpathpro TO user;
GRANT ALL PRIVILEGES ON SCHEMA public TO user;
