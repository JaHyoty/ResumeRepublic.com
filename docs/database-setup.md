# Database Setup Guide

This guide explains how to set up the PostgreSQL database for CareerPathPro.

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose installed
- Docker daemon running

### 1. Start Database Services

```bash
# Navigate to the docker directory
cd infrastructure/docker

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Check if services are running
docker-compose ps
```

### 2. Verify Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U user -d careerpathpro

# Test connection
\dt
\q
```

## 🛠️ Manual Setup (Local PostgreSQL)

### Prerequisites
- PostgreSQL 12+ installed
- `psql` command line tool available

### 1. Create Database

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE careerpathpro;
CREATE USER careerpathpro_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE careerpathpro TO careerpathpro_user;
\q
```

### 2. Run Schema Script

```bash
# Run the schema script
psql -h localhost -U careerpathpro_user -d careerpathpro -f database_schema.sql
```

## 🔧 Development Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://careerpathpro_user:your_secure_password@localhost:5432/careerpathpro
DATABASE_URL_ASYNC=postgresql+asyncpg://careerpathpro_user:your_secure_password@localhost:5432/careerpathpro

# For Docker setup
DATABASE_URL=postgresql://user:password@localhost:5432/careerpathpro
DATABASE_URL_ASYNC=postgresql+asyncpg://user:password@localhost:5432/careerpathpro
```

### 2. Run Migrations (if using Alembic)

```bash
cd backend
alembic upgrade head
```

### 3. Verify Setup

```bash
# Test database connection
python scripts/init_db.py

# Check tables
psql -h localhost -U careerpathpro_user -d careerpathpro -c "\dt"
```

## 📊 Database Schema Overview

### Core Tables

1. **users** - User accounts and profiles
2. **experiences** - Work experience records
3. **experience_titles** - Job titles for each experience
4. **achievements** - Accomplishments linked to experiences
5. **tools** - Technology tools and frameworks
6. **experience_tools** - Many-to-many relationship between experiences and tools
7. **skills** - User skills with proficiency levels
8. **publications** - Research papers, articles, blog posts
9. **certifications** - Professional certifications
10. **job_descriptions** - Job postings and requirements
11. **resume_versions** - Generated resume versions

### Key Features

- **Cascading Deletes**: When a user is deleted, all related data is automatically removed
- **Indexes**: Optimized for common queries (user lookups, date ranges, text search)
- **JSONB Support**: For flexible metadata storage
- **Triggers**: Automatic `updated_at` timestamp updates
- **Extensions**: UUID and trigram support for advanced features

## 🔍 Sample Data

The schema includes sample data for development:

- 2 sample users
- 10 common technology tools
- Sample work experiences with achievements
- Sample skills and certifications
- Sample job description and resume version

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # Start PostgreSQL
   sudo systemctl start postgresql
   ```

2. **Permission Denied**
   ```bash
   # Check PostgreSQL configuration
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

3. **Database Not Found**
   ```bash
   # Create database manually
   createdb careerpathpro
   ```

4. **Docker Issues**
   ```bash
   # Check Docker daemon
   sudo systemctl status docker
   
   # Start Docker daemon
   sudo systemctl start docker
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

### Reset Database

```bash
# Drop and recreate database
dropdb careerpathpro
createdb careerpathpro
psql -d careerpathpro -f database_schema.sql
```

## 📈 Performance Optimization

### Indexes

The schema includes optimized indexes for:
- User lookups by email
- Experience queries by user and date ranges
- Full-text search on job descriptions
- JSONB queries on extracted keywords

### Connection Pooling

For production, consider using connection pooling:

```python
# In your application
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## 🔒 Security Considerations

1. **Use strong passwords** for database users
2. **Limit database access** to application servers only
3. **Enable SSL** for production connections
4. **Regular backups** of the database
5. **Monitor access logs** for suspicious activity

## 📝 Next Steps

After setting up the database:

1. **Start the backend service**: `cd backend && uvicorn app.main:app --reload`
2. **Test API endpoints**: Visit `http://localhost:8000/docs`
3. **Run tests**: `pytest` in the backend directory
4. **Set up monitoring**: Configure logging and health checks

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
