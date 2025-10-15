# SCOUT Backend

Local-first resume and profile management system - Backend API.

## Overview

FastAPI application with PostgreSQL and pgvector for local-first data processing and storage.

## Tech Stack

- FastAPI
- Python 3.11
- PostgreSQL 16 with pgvector
- Pydantic models
- Docker Compose for local development

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start with Docker Compose:
   ```bash
   docker compose up
   ```

## Development

- `uvicorn main:app --reload` - Start development server
- `python -m pytest` - Run tests
- `ruff check .` - Run linting
- `black .` - Format code

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.