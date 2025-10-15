# SCOUT Local Development Runbook

## Prerequisites

- Docker and Docker Compose
- Node.js 20 (for frontend)
- Python 3.11 (for backend development)
- Git

## Quick Start

1. **Clone repositories**
   ```bash
   git clone <repo-url> scout
   cd scout
   ```

2. **Start services**
   ```bash
   cd scout-backend
   docker compose up -d
   ```

3. **Setup frontend**
   ```bash
   cd ../scout-frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

## Service Health Checks

### Database Health Check
```bash
docker compose exec db psql -U scout -d scout -c "SELECT 1;"
```

Expected output: `1`

### pgvector Extension Check
```bash
docker compose exec db psql -U scout -d scout -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

Expected output: Extension details showing pgvector is installed

### Backend API Health Check
```bash
curl http://localhost:8000/health
```

Expected output: `{"status": "healthy", "service": "scout-backend", "version": "0.1.0"}`

### Upload Service Health Check
```bash
curl http://localhost:8000/api/uploads/health
```

Expected output: Upload service info with max file size and allowed types

### Frontend Health Check
```bash
curl http://localhost:3000
```

Expected output: HTML page with SCOUT interface

## Upload Functionality Testing

### Test File Upload via API
```bash
# Create a test file
echo "Test PDF content" > test.pdf

# Upload via curl
curl -X POST http://localhost:8000/api/uploads/resume \
  -F "file=@test.pdf" \
  -H "Content-Type: multipart/form-data"
```

Expected response: JSON with resume_id, run_id, file_hash, etc.

### Verify File Storage
```bash
# Check if file was stored
ls -la data/original/$(date +%Y)/$(date +%m)/
```

Expected: Directory with run_id containing uploaded file

### Test File Validation
```bash
# Test invalid file type
echo "test" > test.txt
curl -X POST http://localhost:8000/api/uploads/resume \
  -F "file=@test.txt"
```

Expected response: 400 error with validation message

### Test File Size Limit
```bash
# Create large file (>10MB)
dd if=/dev/zero of=large.pdf bs=1M count=15
curl -X POST http://localhost:8000/api/uploads/resume \
  -F "file=@large.pdf"
```

Expected response: 413 error with size limit message

## Environment Variables

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `DATA_ROOT`: Local storage root directory
- `ENCRYPTION_KEY`: Key for at-rest encryption
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL`: Backend API base URL
- `NEXT_PUBLIC_ENVIRONMENT`: Development environment flag

## Common Operations

### Reset Database
```bash
docker compose down -v
docker compose up -d db
# Wait for DB to initialize
docker compose up -d api
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f db
```

### Run Tests
```bash
# Backend
cd scout-backend
python -m pytest

# Frontend
cd scout-frontend
npm test
```

### Linting and Formatting
```bash
# Backend
cd scout-backend
ruff check .
black .

# Frontend
cd scout-frontend
npm run lint
npm run format
```

## Troubleshooting

### Database Connection Issues
1. Ensure PostgreSQL container is running: `docker compose ps`
2. Check database logs: `docker compose logs db`
3. Verify connection string in `.env`

### Port Conflicts
- Database: 5432
- Backend API: 8000
- Frontend: 3000

If ports are in use, update `docker-compose.yml` and environment files.

### Permission Issues
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

## Performance Monitoring

### Database Performance
```bash
# Check active connections
docker compose exec db psql -U scout -d scout -c "SELECT count(*) FROM pg_stat_activity;"

# Check table sizes
docker compose exec db psql -U scout -d scout -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname='public';"
```

### API Performance
- Check `/metrics` endpoint for performance data
- Monitor logs for slow queries and requests

## Backup and Recovery

### Database Backup
```bash
docker compose exec db pg_dump -U scout scout > backup.sql
```

### Data Directory Backup
```bash
tar -czf data-backup.tar.gz data/
```

### Restore Database
```bash
docker compose exec -T db psql -U scout scout < backup.sql
```