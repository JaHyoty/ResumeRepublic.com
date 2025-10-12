# ResumeRepublic

> AI-powered resume optimization and job application tracking platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌐 Live Application

Visit [ResumeRepublic.com](https://resumerepublic.com) to see the platform in action.

## 📋 Overview

ResumeRepublic is a comprehensive career management platform that helps job seekers create optimized, ATS-friendly resumes tailored to specific job postings. The platform combines AI-powered content optimization with professional LaTeX typesetting to generate high-quality resumes.

### Key Features

- 🤖 **AI-Powered Resume Optimization** - Uses advanced LLMs to tailor your resume content to specific job descriptions
- 📊 **Application Tracking** - Track your job applications, interviews, and follow-ups in one place
- 🎨 **Professional Templates** - Beautiful LaTeX-based resume templates with consistent formatting
- ✏️ **LaTeX Editor** - Fine-tune your resume with an integrated LaTeX editor
- 🔍 **Job Posting Parser** - Automatically extract job details from company websites
- 📈 **Real-time Updates** - WebSocket-based real-time status updates during resume generation
- ☁️ **Secure Cloud Storage** - Resumes stored securely in AWS S3 with CloudFront CDN delivery

## 🏗️ Architecture

ResumeRepublic is built with a modern, cloud-native architecture:

### Frontend
- **React 18** with TypeScript
- **Vite** for fast builds and hot module replacement
- **TailwindCSS** for responsive, modern UI
- **React Router** for client-side routing
- Deployed to **AWS S3** with **CloudFront** distribution

### Backend
- **FastAPI** (Python) for high-performance API
- **PostgreSQL** for relational data storage
- **SQLAlchemy** ORM with Alembic migrations
- **Playwright** for web scraping job postings
- **LaTeX** for professional PDF generation
- Deployed to **AWS ECS Fargate** with blue-green deployments

### Infrastructure
- **Terraform** for Infrastructure as Code
- **AWS** services: ECS, RDS, S3, CloudFront, ALB, VPC
- **IAM** authentication for secure database access
- **CloudWatch** for logging and monitoring
- **SSM Parameter Store** for secrets management

## 🚀 Deployment

This project is designed to be deployed to AWS using automated deployment scripts. Local development setup instructions are not provided at this time, as the infrastructure is optimized for cloud deployment.

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with credentials
- Terraform installed (v1.0+)
- Docker installed
- Node.js 18+ for frontend builds

### Quick Deploy

#### 1. Deploy Infrastructure

```bash
# Deploy to development environment
./scripts/deploy-infrastructure.sh --environment development

# Deploy to production environment
./scripts/deploy-infrastructure.sh --environment production
```

This script will:
- Initialize Terraform
- Create VPC, subnets, and networking
- Provision RDS PostgreSQL database
- Set up ECS cluster and services
- Create S3 buckets and CloudFront distributions
- Configure IAM roles and security groups

#### 2. Deploy Backend

```bash
# Deploy backend to development
./scripts/deploy-backend.sh --environment development

# Deploy backend to production with database migrations
./scripts/deploy-backend.sh --environment production --run-migrations
```

This script will:
- Build Docker image
- Push to AWS ECR
- Deploy to ECS Fargate with blue-green strategy
- Optionally run database migrations

#### 3. Deploy Frontend

```bash
# Deploy frontend to development
./scripts/deploy-frontend.sh --environment development

# Deploy frontend to production
./scripts/deploy-frontend.sh --environment production
```

This script will:
- Build optimized production bundle
- Upload to S3
- Invalidate CloudFront cache
- Verify deployment

### Database Management

The platform includes a secure database connection script for running migrations and administrative tasks:

```bash
# Connect to database via jump host
./scripts/connect-to-database.sh --environment production

# This will:
# - Establish secure tunnel through EC2 jump host
# - Set up port forwarding to RDS instance
# - Expose database on localhost for Alembic commands
```

Once connected, you can run Alembic migrations:

```bash
# In a separate terminal (while tunnel is active)
cd backend
alembic upgrade head              # Apply all migrations
alembic revision -m "description" # Create new migration
alembic current                   # Show current revision
```

The jump host provides secure access to the private RDS instance without exposing it to the public internet.

### Environment Configuration

Set up environment-specific variables in:
- `infrastructure/terraform/environments/development/terraform.tfvars`
- `infrastructure/terraform/environments/production/terraform.tfvars`

See `terraform.tfvars.example` files for required variables.

## 🔧 Technology Stack

### Frontend Technologies
- React 18
- TypeScript
- Vite
- TailwindCSS
- Axios
- React Router
- Context API for state management

### Backend Technologies
- FastAPI
- Python 3.11+
- SQLAlchemy
- Alembic
- Pydantic
- Playwright
- LaTeX (TeX Live)
- Structlog

### AWS Services
- ECS Fargate
- RDS PostgreSQL
- S3
- CloudFront
- Application Load Balancer
- ECR
- VPC
- IAM
- CloudWatch
- SSM Parameter Store
- Secrets Manager

## 📖 Documentation

- **Project Requirements**: See `docs/requirements.md`
- **API Documentation**: Available at `/docs` when running the backend
- **Infrastructure Diagrams**: Generated by Terraform in `infrastructure/terraform/`

## 🔐 Security

- All secrets managed via AWS Secrets Manager and SSM Parameter Store
- IAM-based database authentication
- HTTPS/TLS encryption in transit
- S3 bucket encryption at rest
- CloudFront signed URLs for secure PDF access
- CORS configuration for API security

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Created by Jaakko Hyöty

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

**Note**: This project is optimized for AWS deployment. The deployment scripts handle infrastructure provisioning, application deployment, and configuration management. For local development setup, please contact the maintainer.

