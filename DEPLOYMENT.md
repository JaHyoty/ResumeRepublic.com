# CareerPathPro Deployment Guide

This guide explains how to deploy the CareerPathPro application using Docker.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd career-manager
```

### 2. Development Deployment

For development with hot reloading:

```bash
# Start only the database
docker-compose -f docker-compose.dev.yml up postgres

# Or start everything (database + backend)
docker-compose -f docker-compose.dev.yml up
```

### 3. Production Deployment

For production deployment:

```bash
# Create environment file
cp .env.example .env
# Edit .env with your production values

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
POSTGRES_DB=careerpathpro
POSTGRES_USER=careeruser
POSTGRES_PASSWORD=your-secure-password-here

# Backend Configuration
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=production

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```

## Services

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: careerpathpro
- **User**: careeruser
- **Password**: Set in environment variables

### Backend API
- **Port**: 8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

### Frontend
- **Port**: 3000
- **URL**: http://localhost:3000

## Deployment Options

### Option 1: Full Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Database Only (for local development)
```bash
docker-compose -f docker-compose.dev.yml up postgres
# Then run backend and frontend locally
```

### Option 3: Backend + Database (for frontend development)
```bash
docker-compose -f docker-compose.dev.yml up postgres backend
# Then run frontend locally
```

## Database Management

### Access Database
```bash
# Connect to database
docker exec -it careerpathpro_db_prod psql -U careeruser -d careerpathpro

# Run migrations
docker exec -it careerpathpro_backend_prod alembic upgrade head
```

### Backup Database
```bash
docker exec careerpathpro_db_prod pg_dump -U careeruser careerpathpro > backup.sql
```

### Restore Database
```bash
docker exec -i careerpathpro_db_prod psql -U careeruser -d careerpathpro < backup.sql
```

## Monitoring

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs backend
```

### Health Checks
- Database: `docker exec careerpathpro_db_prod pg_isready`
- Backend: `curl http://localhost:8000/health`
- Frontend: `curl http://localhost:3000`

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose files
2. **Permission issues**: Ensure Docker has proper permissions
3. **Database connection**: Check if database is healthy before starting backend

### Reset Everything
```bash
# Stop and remove all containers
docker-compose -f docker-compose.prod.yml down -v

# Remove all images
docker-compose -f docker-compose.prod.yml down --rmi all

# Start fresh
docker-compose -f docker-compose.prod.yml up -d
```

## Security Notes

- Change default passwords in production
- Use strong SECRET_KEY
- Consider using Docker secrets for sensitive data
- Enable SSL/TLS in production
- Use a reverse proxy (nginx) for production
