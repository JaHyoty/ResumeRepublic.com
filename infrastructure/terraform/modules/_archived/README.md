# Archived Infrastructure Architecture (ECS / RDS / VPC)

> **Historical Reference**: This directory contains the Terraform modules for ResumeRepublic's previous infrastructure architecture before migrating to a fully serverless setup (AWS Lambda + DynamoDB + API Gateway).

---

## 🏛️ Previous Architecture Overview

The previous architecture was built as a traditional containerized, VPC-bound web application on AWS:

```
[ Internet ]
      │
      ▼
[ Route 53 ]
      │
      ├───────────────────────────────┐
      ▼                               ▼
[ CloudFront (Frontend SPA) ]   [ Application Load Balancer (ALB) ]
      │                               │
      ▼                               ▼
[ S3 Bucket ]                   [ Public Subnets ]
                                      │
                                      ▼
                                [ ECS Fargate Service ]
                                (FastAPI Container in Private Subnets)
                                      │
                                      ├────────────────────────┐
                                      ▼                        ▼
                              [ RDS PostgreSQL ]        [ AWS S3 / TeX Live ]
                              (Database Subnets)        (Resumes Bucket)
                                      ▲
                                      │ (Tunnel)
                              [ EC2 Jump Host ]
                              (SSM Session Manager)
```

---

## 📦 Archived Modules

### 1. `compute/` — ECS Fargate & ALB
- **AWS ECS Cluster & Fargate Service**: Ran the monolithic FastAPI application container (`backend/Dockerfile`).
- **Application Load Balancer (ALB)**: Handled incoming HTTPS traffic, SSL termination, and forwarded API requests to Fargate tasks.
- **Auto-scaling & Health Checks**: Configured with target group health checks on `/health`.

### 2. `database/` — Amazon RDS PostgreSQL
- **Engine**: PostgreSQL 17 (db.t3.micro).
- **ORM & Migrations**: Managed via SQLAlchemy and Alembic migrations.
- **Security**: Private database subnets with no public IP; IAM database authentication and Secrets Manager password rotation.

### 3. `jump-host/` — EC2 Bastion / Jump Host
- **Instance**: A t3.nano instance deployed into a public subnet.
- **Access**: Accessed exclusively via AWS Systems Manager (SSM) Session Manager (no open port 22).
- **Purpose**: Provided port-forwarding SSH/SSM tunnels (`connect-to-database.sh`) so developers and CI could run Alembic database migrations and connect pgAdmin/psql to the private RDS instance.

### 4. `networking/` — Multi-Tier VPC
- **VPC CIDR**: `10.0.0.0/16`.
- **Subnets**:
  - 2x Public Subnets (ALB, Jump Host, Internet Gateway).
  - 2x Private Subnets (ECS Fargate tasks).
  - 2x Database Subnets (RDS PostgreSQL DB subnet group).
- **Routing**: Internet Gateway, public and private route tables, network ACLs, and VPC security groups.

---

## 🔄 Why We Migrated to Serverless

While robust, the previous architecture had several operational challenges:
1. **Idle Costs**: RDS instance, ALB, NAT/Jump host, and running Fargate containers incurred fixed monthly baseline costs even during zero-traffic periods.
2. **Maintenance Overhead**: Managing Alembic migrations, database connection pools, jump-host tunneling for schema updates, and container scaling.
3. **Execution Isolation**: Long-running or resource-intensive tasks (such as LaTeX PDF compilation and headless browser web scraping) shared CPU/memory with user-facing API requests on Fargate tasks.

The new serverless architecture replaces these components with **API Gateway HTTP API**, **AWS Lambda** (specialized micro-workers for API, PDF, and scraping), and **DynamoDB single-table design**, achieving:
- **Pay-per-request pricing** (near-zero idle cost).
- **Automatic horizontal scaling** with instant burst handling.
- **Isolated compute environments** for heavy tasks (Playwright Chromium and TeX Live run in dedicated Lambdas).
- **Zero tunnel/migration management** (DynamoDB eliminates VPC jump-hosts and database connection limits).
