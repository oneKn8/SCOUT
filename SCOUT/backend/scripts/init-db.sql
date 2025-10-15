-- SCOUT Database Initialization Script
-- This script sets up the core tables and pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    file_path VARCHAR(512) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    embedding vector(384),  -- For sentence-transformers/all-MiniLM-L6-v2
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status processing_status DEFAULT 'pending',

    -- Schema versioning for ProfileJSON compatibility
    profile_schema_version VARCHAR(20) DEFAULT '1.0.0',
    profile_data JSONB,  -- Parsed profile JSON conforming to schema
    validation_errors JSONB DEFAULT '[]'::jsonb  -- Schema validation errors if any
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_active ON resumes(is_active);
CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON resumes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_artifacts_user_id ON artifacts(user_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_resume_id ON artifacts(resume_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_schema_version ON artifacts(profile_schema_version);

-- Vector similarity search index (IVFFlat for approximate search)
CREATE INDEX IF NOT EXISTS idx_artifacts_embedding ON artifacts
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create trigger function for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (for development only)
INSERT INTO users (email, settings)
VALUES ('admin@scout.local', '{"role": "admin", "created_by": "init_script"}')
ON CONFLICT (email) DO NOTHING;

-- Create a view for active resumes with user info
CREATE OR REPLACE VIEW active_resumes AS
SELECT
    r.id,
    r.user_id,
    u.email as user_email,
    r.title,
    r.version,
    r.created_at,
    r.updated_at,
    (SELECT COUNT(*) FROM artifacts a WHERE a.resume_id = r.id) as artifact_count
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE r.is_active = TRUE AND u.is_active = TRUE;

-- Create a view for artifact statistics
CREATE OR REPLACE VIEW artifact_stats AS
SELECT
    status,
    COUNT(*) as count,
    AVG(file_size) as avg_file_size,
    SUM(file_size) as total_size
FROM artifacts
GROUP BY status;

-- Grant permissions (adjust as needed for production)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO scout_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO scout_user;

-- Log initialization completion
DO $$
BEGIN
    RAISE NOTICE 'SCOUT database initialization completed successfully';
    RAISE NOTICE 'pgvector extension enabled';
    RAISE NOTICE 'Core tables created: users, resumes, artifacts';
    RAISE NOTICE 'Indexes and triggers configured';
    RAISE NOTICE 'Default admin user created: admin@scout.local';
END $$;