# SCOUT Architecture

## Overview

SCOUT is a local-first resume and profile management system designed with privacy and security as core principles. The system consists of two main components:

- **Frontend**: Next.js 14 application with accessibility-first design
- **Backend**: FastAPI service with PostgreSQL + pgvector for data storage

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │   + pgvector    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │  Local Storage  │
                       │    (data/)      │
                       └─────────────────┘
```

## Core Principles

### Local-First
- All data processing happens locally
- No external cloud dependencies during development phase
- Data stored in local filesystem with versioned structure

### Privacy-Aware
- PII-aware logging with automatic redaction
- Encryption at rest for stored artifacts
- No telemetry or external tracking

### Security
- Structured logging with JSON format
- Environment-based configuration
- Pre-commit hooks for code quality

## Technology Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS + shadcn/ui
- **Language**: TypeScript
- **Runtime**: Node.js 20
- **Accessibility**: WCAG 2.1 AA compliance

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: PostgreSQL 16 with pgvector extension
- **Validation**: Pydantic models
- **Logging**: Structured JSON logging

### Infrastructure
- **Development**: Docker Compose
- **Database**: PostgreSQL 16 with pgvector
- **Storage**: Local filesystem (data/ directory)

## Data Flow

1. **Upload**: Files uploaded through frontend
2. **Processing**: Backend processes and extracts data
3. **Storage**: Data stored in PostgreSQL with embeddings in pgvector
4. **Artifacts**: Original files stored in versioned local filesystem

## Security Model

- Environment-based secrets management
- Encryption at rest for sensitive data
- Request/response logging with PII redaction
- No external network dependencies

## Development Environment

- Docker Compose for service orchestration
- Pre-commit hooks for code quality
- Conventional commits for change tracking
- Automated testing and linting

## Future Considerations

- Vector similarity search for resume matching
- Plugin architecture for extended functionality
- Export capabilities to various formats
- Advanced privacy controls