# ResumeRepublic

> AI-powered resume optimization and job application tracking platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌐 Live Application

Visit [ResumeRepublic.com](https://resumerepublic.com) to see the platform in action.

## 📋 Overview

ResumeRepublic is a comprehensive career management platform that helps job seekers create optimized, ATS-friendly resumes tailored to specific job postings. The platform combines AI-powered content optimization with professional LaTeX typesetting to generate high-quality resumes.

### Key Features

- 🤖 **AI-Powered Resume Optimization** - Uses advanced LLMs to tailor resume content to specific job descriptions with fact-checking verification
- 📊 **Application Tracking** - Track job applications, interviews, and follow-ups in one place
- 🎨 **Professional Templates** - Beautiful LaTeX-based resume templates with ATS-friendly formatting
- ✏️ **LaTeX Editor** - Fine-tune resumes with an integrated LaTeX editor and real-time PDF generation
- 🔍 **Job Posting Parser** - Automatically extract job details from company websites using headless browser scraping
- 📈 **Real-time Updates** - Webhook-based real-time status updates during resume generation
- ☁️ **Secure Cloud Storage** - Resumes stored securely in AWS S3 with CloudFront CDN delivery

---

## 🏗️ Architecture

> ℹ️ **Looking for the previous infrastructure?**  
> ResumeRepublic was originally deployed on a containerized, VPC-bound infrastructure using Amazon ECS Fargate, RDS PostgreSQL, and an EC2 Bastion/Jump Host. The documentation and Terraform modules for that legacy setup are archived in [**`infrastructure/terraform/modules/_archived/`**](infrastructure/terraform/modules/_archived/README.md).

ResumeRepublic now runs on a modern, fully **Serverless** architecture on AWS designed for high performance, infinite scalability, and zero idle costs:

```
[ User Browser ]
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[ CloudFront CDN ]              [ API Gateway (HTTP API) ]
       │                                 │
       ▼                                 ▼
  [ S3 Bucket ]                 [ Backend API Lambda ]
 (Frontend SPA)                 (FastAPI + Mangum Adapter)
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
        [ DynamoDB Table ]      [ PDF Worker Lambda ]   [ Scraper Worker Lambda ]
       (Single-Table Design)    (TeX Live + Claude LLM)   (Playwright Chromium)
                                         │
                                         ▼
                                [ S3 Resumes Bucket ]
                                         │
                                         ▼
                             [ CloudFront Resumes CDN ]
```

### 1. Frontend
- **Framework**: **React 18** with **TypeScript**
- **Bundler & Tooling**: **Vite** for optimized production builds
- **Styling**: **TailwindCSS** for responsive, clean design
- **Hosting**: Static assets hosted on **AWS S3** and distributed globally via **Amazon CloudFront** CDN with SPA routing

### 2. Backend API
- **Framework**: **FastAPI** (Python 3.12) wrapped with the **Mangum** adapter for AWS Lambda
- **Routing**: **AWS API Gateway (HTTP API v2)** with CORS and JWT bearer authentication
- **Execution**: Runs as a lightweight containerized Lambda function (`resumerepublic-api`) with sub-second response times

### 3. Asynchronous Worker Lambdas
To keep the API fast and responsive, heavy workloads are dispatched asynchronously to dedicated worker Lambdas:
- **PDF & Resume Generation Worker (`resumerepublic-pdf`)**:
  - Containerized Lambda packaged with **TeX Live** (`pdflatex`)
  - Multi-stage LLM pipeline (Keyword Extraction → Content Alignment → LaTeX Generation → Fact-checking Verification)
  - Compiles `.tex` into PDF and uploads artifacts to the resumes S3 bucket
- **Job Posting Scraper Worker (`resumerepublic-scraper`)**:
  - Containerized Lambda running headless **Playwright Chromium**
  - Handles dynamic JavaScript-rendered career sites with anti-bot resilience and fallback heuristic extraction

### 4. Database (Amazon DynamoDB)
- **Model**: **Single-Table Design** (`resumerepublic-production`) with Pay-Per-Request billing
- **Primary Keys**: Composite `PK` and `SK` supporting all entity relationships (Users, Applications, Job Postings, Resumes, Experiences, Skills, Certifications, Publications, Projects, Websites)
- **Secondary Index**: Global Secondary Index (`GSI1`) for email lookups and inverse entity queries

### 5. Storage, CDN, & Secrets
- **S3 & CloudFront**: Dedicated S3 buckets for the frontend web application and generated resume PDFs, delivered via separate CloudFront distributions with TLS 1.2+ encryption
- **Secrets Management**: Configuration and credentials (OAuth client secrets, OpenRouter API keys, JWT signing keys) managed securely via **AWS Systems Manager (SSM) Parameter Store**

---

## 🚀 Deployment

ResumeRepublic uses the unified deployment script [`scripts/deploy.sh`](scripts/deploy.sh) to build containers, apply Terraform infrastructure, update Lambda functions, and deploy the frontend.

### Prerequisites

- AWS CLI configured with credentials (`us-east-1`, profile `jahyoty-admin` by default or set via `AWS_PROFILE`)
- Docker installed and running (for building container images)
- Terraform (v1.6.0+)
- Node.js 18+ & npm (for frontend production builds)

---

### Deployment Commands

```bash
# 1. Full Deployment (Builds all 3 Lambdas, applies Terraform, builds & syncs frontend to S3/CloudFront)
./scripts/deploy.sh

# 2. Backend Only (Builds all 3 Lambdas and applies Terraform, skips frontend)
./scripts/deploy.sh --backend-only

# 3. Frontend Only (Builds frontend and syncs to S3 with CloudFront cache invalidation)
./scripts/deploy.sh --frontend-only

# 4. Targeted Lambda Updates (Fast iteration when editing a single service)
./scripts/deploy.sh --api-only      # Build, push & update API Lambda only
./scripts/deploy.sh --pdf-only      # Build, push & update PDF / LaTeX Lambda only
./scripts/deploy.sh --scraper-only  # Build, push & update Scraper Lambda only

# 5. Additional Flags
./scripts/deploy.sh --skip-terraform # Update containers & Lambdas without running terraform apply
./scripts/deploy.sh --skip-frontend  # Skip building and uploading the frontend
```

---

## 🔧 Technology Stack

### Frontend
- React 18, TypeScript, Vite
- TailwindCSS
- Axios, React Router, Context API

### Backend
- Python 3.12, FastAPI, Mangum
- Pydantic v2
- Boto3 (DynamoDB, S3, Lambda invocation)
- TeX Live (LaTeX compiler)
- Playwright Chromium (Web scraping)
- OpenRouter API (Claude Sonnet LLM)

### AWS Serverless Services
- **AWS Lambda** (Container images: API, PDF compiler, Playwright scraper)
- **Amazon API Gateway** (HTTP API v2)
- **Amazon DynamoDB** (Single-table architecture)
- **Amazon S3** (Frontend hosting & resume PDF storage)
- **Amazon CloudFront** (Global CDN for frontend and PDFs)
- **Amazon ECR** (Elastic Container Registry for Lambda images)
- **AWS SSM Parameter Store** (Secure secrets and configuration)
- **Amazon CloudWatch** (Structured JSON logging & metrics)

---

## 🔐 Security

- **Zero Open Ports**: No EC2 instances, public databases, or SSH ports exposed.
- **TLS 1.2+ Enforcement**: Strict HTTPS/TLS enforcement on all API calls, CloudFront distributions, and outbound external connections.
- **Secrets Encryption**: All application secrets and API keys are stored in AWS SSM Parameter Store with KMS encryption.
- **Least Privilege IAM**: Dedicated Lambda execution roles scoped strictly to required DynamoDB table keys and S3 buckets.
- **Content Security**: CloudFront CDN security headers and CORS whitelisting for verified domains.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
