-- CareerPathPro Database Schema
-- This file contains the complete database schema for CareerPathPro

-- Create database (run this separately)
-- CREATE DATABASE careerpathpro;

-- Connect to the database
-- \c careerpathpro;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    preferred_first_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- 2. Experiences table
CREATE TABLE experiences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for experiences
CREATE INDEX idx_experiences_user_id ON experiences(user_id);
CREATE INDEX idx_experiences_company ON experiences(company);
CREATE INDEX idx_experiences_dates ON experiences(start_date, end_date);

-- 3. Experience titles table
CREATE TABLE experience_titles (
    id SERIAL PRIMARY KEY,
    experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for experience titles
CREATE INDEX idx_experience_titles_experience_id ON experience_titles(experience_id);
CREATE INDEX idx_experience_titles_primary ON experience_titles(is_primary);

-- 4. Achievements table
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for achievements
CREATE INDEX idx_achievements_experience_id ON achievements(experience_id);

-- 5. Tools table
CREATE TABLE tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for tools
CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_category ON tools(category);

-- 6. Experience tools association table
CREATE TABLE experience_tools (
    experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    PRIMARY KEY (experience_id, tool_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for experience tools
CREATE INDEX idx_experience_tools_experience_id ON experience_tools(experience_id);
CREATE INDEX idx_experience_tools_tool_id ON experience_tools(tool_id);

-- 7. Skills table
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    proficiency VARCHAR(50),
    years_experience DECIMAL(3,1),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for skills
CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_proficiency ON skills(proficiency);

-- 8. Publications table
CREATE TABLE publications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    co_authors TEXT,
    publication_date DATE,
    url VARCHAR(500),
    description TEXT,
    publication_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for publications
CREATE INDEX idx_publications_user_id ON publications(user_id);
CREATE INDEX idx_publications_type ON publications(publication_type);
CREATE INDEX idx_publications_date ON publications(publication_date);

-- 9. Certifications table
CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(150),
    date_obtained DATE,
    expiration_date DATE,
    credential_url VARCHAR(500),
    credential_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for certifications
CREATE INDEX idx_certifications_user_id ON certifications(user_id);
CREATE INDEX idx_certifications_organization ON certifications(issuing_organization);
CREATE INDEX idx_certifications_expiration ON certifications(expiration_date);

-- 10. Job descriptions table
CREATE TABLE job_descriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(100),
    content TEXT NOT NULL,
    extracted_keywords JSONB,
    salary_range VARCHAR(100),
    location VARCHAR(100),
    job_type VARCHAR(50),
    experience_level VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for job descriptions
CREATE INDEX idx_job_descriptions_user_id ON job_descriptions(user_id);
CREATE INDEX idx_job_descriptions_company ON job_descriptions(company);
CREATE INDEX idx_job_descriptions_keywords ON job_descriptions USING GIN(extracted_keywords);

-- 11. Resume versions table
CREATE TABLE resume_versions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    job_description_id INTEGER REFERENCES job_descriptions(id),
    latex_content TEXT,
    pdf_url VARCHAR(500),
    resume_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for resume versions
CREATE INDEX idx_resume_versions_user_id ON resume_versions(user_id);
CREATE INDEX idx_resume_versions_job_description_id ON resume_versions(job_description_id);
CREATE INDEX idx_resume_versions_created_at ON resume_versions(created_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiences_updated_at BEFORE UPDATE ON experiences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publications_updated_at BEFORE UPDATE ON publications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_certifications_updated_at BEFORE UPDATE ON certifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resume_versions_updated_at BEFORE UPDATE ON resume_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for development
INSERT INTO users (email, first_name, last_name, preferred_first_name) VALUES
('john.doe@example.com', 'John', 'Doe', 'John'),
('jane.smith@example.com', 'Jane', 'Smith', 'Jane');

-- Insert sample tools
INSERT INTO tools (name, category) VALUES
('Python', 'Programming Language'),
('JavaScript', 'Programming Language'),
('React', 'Frontend Framework'),
('Node.js', 'Backend Framework'),
('PostgreSQL', 'Database'),
('Docker', 'DevOps'),
('AWS', 'Cloud Platform'),
('Git', 'Version Control'),
('Linux', 'Operating System'),
('SQL', 'Query Language');

-- Insert sample experience
INSERT INTO experiences (user_id, company, location, start_date, end_date, description, is_current) VALUES
(1, 'Tech Corp', 'San Francisco, CA', '2022-01-01', '2023-12-31', 'Software Engineer working on web applications', false),
(1, 'StartupXYZ', 'Remote', '2024-01-01', NULL, 'Senior Software Engineer leading full-stack development', true);

-- Insert sample experience titles
INSERT INTO experience_titles (experience_id, title, is_primary) VALUES
(1, 'Software Engineer', true),
(2, 'Senior Software Engineer', true),
(2, 'Tech Lead', false);

-- Insert sample achievements
INSERT INTO achievements (experience_id, description) VALUES
(1, 'Led development of microservices architecture serving 1M+ users'),
(1, 'Improved application performance by 40% through code optimization'),
(2, 'Built and deployed 5+ production applications'),
(2, 'Mentored 3 junior developers');

-- Insert sample skills
INSERT INTO skills (user_id, name, proficiency, years_experience, source) VALUES
(1, 'Python', 'Expert', 5.0, 'work'),
(1, 'JavaScript', 'Advanced', 4.0, 'work'),
(1, 'React', 'Advanced', 3.0, 'work'),
(1, 'PostgreSQL', 'Intermediate', 2.0, 'work'),
(1, 'Docker', 'Intermediate', 1.5, 'work');

-- Insert sample tools for experiences
INSERT INTO experience_tools (experience_id, tool_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 5), (1, 6),
(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7);

-- Insert sample publication
INSERT INTO publications (user_id, title, co_authors, publication_date, url, publication_type) VALUES
(1, 'Building Scalable Web Applications with Python', 'Jane Smith', '2023-06-15', 'https://example.com/article', 'Blog');

-- Insert sample certification
INSERT INTO certifications (user_id, name, issuing_organization, date_obtained, expiration_date, credential_id) VALUES
(1, 'AWS Certified Solutions Architect', 'Amazon Web Services', '2023-03-01', '2026-03-01', 'AWS-SAA-123456');

-- Insert sample job description
INSERT INTO job_descriptions (user_id, title, company, content, salary_range, location, job_type, experience_level) VALUES
(1, 'Senior Software Engineer', 'Google', 'We are looking for a Senior Software Engineer to join our team...', '$120,000 - $180,000', 'Mountain View, CA', 'Full-time', 'Senior');

-- Insert sample resume version
INSERT INTO resume_versions (user_id, title, job_description_id, resume_metadata) VALUES
(1, 'Senior Software Engineer - Google', 1, '{"version": "1.0", "generated_at": "2024-01-15T10:30:00Z"}');

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
