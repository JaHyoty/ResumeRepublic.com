# CareerPathPro

A comprehensive career management and resume optimization platform for computer science professionals.

## 🚀 Features

- **Experience & Skills Catalog (ESC)**: Centralized storage for work history, achievements, tools, skills, publications, and certifications
- **Resume Parsing**: Upload PDF/DOCX resumes and auto-populate ESC using AI/LLM
- **Job Description Analysis**: Extract keywords and requirements from job postings
- **ATS-Optimized Resume Generation**: Generate tailored LaTeX resumes for specific job applications
- **Resume Versioning**: Save and manage multiple resume versions with metadata
- **Multi-Provider Authentication**: Google, GitHub, Apple OAuth + email/password

## 🏗️ Architecture

This project follows a microservices architecture with the following components:

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend API**: FastAPI (Python) with PostgreSQL
- **Parsing Service**: Python microservice for document processing
- **Database**: PostgreSQL with Redis for caching
- **Storage**: AWS S3 for file storage
- **Infrastructure**: Docker containers with Docker Compose

## 📁 Project Structure

```
career-manager/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript type definitions
│   └── package.json
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   └── requirements.txt
├── parsing-service/         # Document parsing microservice
│   ├── app/
│   │   ├── parsers/        # Document parsers
│   │   ├── models/         # Data models
│   │   └── services/       # LLM and processing services
│   └── requirements.txt
├── shared/                  # Shared types and utilities
│   ├── types/              # Common type definitions
│   └── schemas/            # Validation schemas
├── infrastructure/          # Infrastructure as Code
│   ├── docker/             # Docker configurations
│   ├── terraform/          # Terraform configurations
│   └── kubernetes/         # K8s manifests
└── docs/                   # Documentation
    ├── api/                # API documentation
    └── architecture/       # Architecture docs
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd career-manager
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

4. **Access the applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Parsing Service: http://localhost:8001
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Parsing Service Setup**
   ```bash
   cd parsing-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   ```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Parsing service tests
cd parsing-service
pytest
```

## 📚 API Documentation

- Backend API: http://localhost:8000/docs
- Parsing Service API: http://localhost:8001/docs

## 🛠️ Development

### Database Migrations

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "Description"
```

### Code Quality

```bash
# Backend
cd backend
black .
isort .
flake8 .
mypy .

# Frontend
cd frontend
npm run lint
npm run format
```

## 🚀 Deployment

See `docs/deployment/` for detailed deployment instructions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support, email support@careerpathpro.com or create an issue in the repository.
