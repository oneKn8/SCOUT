# SCOUT

Local-first resume and profile management system - Full Stack Application.

## Overview

SCOUT is a comprehensive resume and profile management system built with a modern tech stack, featuring both frontend and backend components designed for local-first data processing and privacy-focused user experiences.

## Architecture

This repository contains both the frontend and backend components of SCOUT:

- **Frontend** (`/frontend`): Next.js 14 application with App Router, Tailwind CSS, and shadcn/ui components
- **Backend** (`/backend`): FastAPI application with PostgreSQL and pgvector for data processing and storage

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Node.js 20

### Backend
- FastAPI
- Python 3.11
- PostgreSQL 16 with pgvector
- Pydantic models
- Docker Compose for local development

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker and Docker Compose
- Git

### Running the Full Stack Application

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Sant0-9/SCOUT.git
   cd SCOUT
   ```

2. **Start the backend:**
   ```bash
   cd backend
   docker compose up
   ```

3. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development

### Frontend Development
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run format       # Run Prettier
```

### Backend Development
```bash
cd backend
uvicorn main:app --reload    # Start development server
python -m pytest            # Run tests
ruff check .                # Run linting
black .                     # Format code
```

## Project Structure

```
SCOUT/
├── frontend/                 # Next.js frontend application
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   ├── package.json         # Dependencies
│   └── ...
├── backend/                 # FastAPI backend application
│   ├── app/                 # Application code
│   ├── docs/                # Documentation
│   ├── requirements.txt     # Python dependencies
│   └── ...
├── README.md               # This file
├── CONTRIBUTING.md         # Contribution guidelines
└── LICENSE                 # License file
```

## Features

- **Local-first data processing**: All data processing happens locally for maximum privacy
- **Modern UI/UX**: Built with shadcn/ui components and Tailwind CSS
- **Type-safe**: Full TypeScript support across frontend and backend
- **Scalable architecture**: Microservices-ready with FastAPI and Next.js
- **Database integration**: PostgreSQL with pgvector for advanced data processing
- **Docker support**: Easy deployment with Docker Compose

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please open an issue in this repository.