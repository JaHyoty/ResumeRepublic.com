# CareerPathPro Requirements Document

## 1. Introduction

CareerPathPro is a web application designed to help computer science professionals compile, optimize, and manage their career profiles and resumes.

## 2. Objectives

- Centralize professional history into an Experience and Skills Catalog (ESC).
- Parse existing resumes and job descriptions using LLMs or rule-based methods.
- Generate ATS-optimized LaTeX resumes tailored to job postings.
- Provide secure authentication and intuitive user experience.
- Showcase scalable architecture and clean code practices.

## 3. Scope

**In-Scope:**
- User registration and authentication (OAuth + email).
- ESC creation, editing, and storage.
- Resume parsing and generation.
- Job description ingestion and resume versioning.

**Out-of-Scope (v1):**
- Mobile-native apps.
- Real-time job board integrations.
- Collaboration or recruiter-facing tools.

## 4. Stakeholders

- **Primary Users:** CS graduates, engineers, career switchers.
- **Secondary Users:** Recruiters reviewing resumes.
- **Product Owner:** Jaakko.
- **Development Team:** Full-stack engineers, DevOps, QA.

## 5. User Personas

- **Alex (CS Graduate):** Wants to compile internships and projects into a polished resume.
- **Morgan (Mid-Level Engineer):** Targets fintech roles, highlights relevant achievements.
- **Riley (Career Switcher):** Translates non-tech roles into transferable skills.

## 6. Functional Requirements

### 6.1 Must-Have Features

1. **Landing Page**
   - Simple, responsive design with clear CTA and conversion flow.

2. **Authentication**
   - Google, Apple, GitHub OAuth + email/password.

3. **Experience and Skills Catalog (ESC)**
   - Stores work history, achievements, tools, skills, publications.
   - Editable via UI.

4. **Resume Parsing**
   - Upload PDF/DOCX → auto-populate ESC using LLM or parser.

5. **Job Description Ingestion**
   - Paste job posting → extract keywords and requirements.

6. **LaTeX Resume Generation**
   - ATS-optimized resume using ESC + job description.
   - Selectively includes relevant experience and skills.

7. **PDF Preview and Export**
   - Render LaTeX resume in-browser.
   - Downloadable PDF.

8. **Resume Versioning**
   - Save resume with timestamp, job description, and salary range.

### 6.2 Nice-to-Have Features

1. **LinkedIn Integration**
   - Enrich ESC via LinkedIn URL or OAuth.

2. **Salary Parsing**
   - NLP extracts salary range from job description.

## 7. Non-Functional Requirements

- **Performance:** Resume generation < 5s.
- **Scalability:** Microservices, containerized deployment.
- **Security:** OAuth2, JWT, RBAC, encryption at rest.
- **Availability:** 99.9% uptime.
- **Maintainability:** Modular codebase, clean APIs.
- **Accessibility:** WCAG 2.1 AA compliance.

## 8. User Workflows

| Workflow                | Steps                                                                 | Acceptance Criteria                                          |
|-------------------------|-----------------------------------------------------------------------|--------------------------------------------------------------|
| New User Signup         | Visit → Sign up → OAuth/email → Dashboard                             | Account created; ESC dashboard shown.                        |
| Resume Parsing          | Upload resume → ESC auto-filled                                       | ≥ 80% ESC fields populated; editable.                        |
| Resume Generation       | Paste job → Generate → Preview → Save                                 | Relevant ESC items shown in LaTeX PDF.                       |
| View Past Versions      | “My Resumes” → list with metadata → download                          | Metadata and download link available.                        |

## 9. Technical Architecture

- **Frontend:** React + Tailwind CSS.
- **Backend:** Node.js/Express or Python/FastAPI.
- **Database:** PostgreSQL; S3 for PDFs.
- **Parsing Service:** Python microservice with LLM integration.
- **CI/CD:** GitHub Actions, Docker, Terraform.
