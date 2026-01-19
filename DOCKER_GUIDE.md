# Docker Deployment Guide

## Quick Start

Run the entire pantry inventory system with one command:

```bash
docker-compose up
```

This starts:
- PostgreSQL database
- Redis (job queue)
- FastAPI backend
- Celery worker (image processing)
- Flower (job monitoring)
- React web UI

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Vision API key (OpenAI or Google Gemini)

## Configuration

### 1. Create Environment File

Create `.env` in the project root:

```bash
# Vision Provider (choose one)
VISION_PROVIDER=openai  # or 'gemini'

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-vision-preview

# Gemini Configuration (alternative)
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-1.5-flash

# Database
DB_USER=pantry
DB_PASSWORD=pantry_secure_pass
DB_NAME=pantry_db

# Optional
LOG_LEVEL=INFO
DEBUG=false
```

### 2. Start Services

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### 3. Initialize Database

The database tables are created automatically when the backend starts.

To seed test data:

```bash
docker-compose exec backend python scripts/seed_db.py seed
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Backend REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Web UI | http://localhost:3000 | React dashboard |
| Flower | http://localhost:5555 | Celery job monitoring |
| PostgreSQL | localhost:5432 | Database (connect with DB_USER/DB_PASSWORD) |
| Redis | localhost:6379 | Job queue |

## Development vs Production

### Development Mode (default)

- Hot reload enabled
- Volumes mounted for live code changes
- Debug logging
- Development server (not production-ready)

### Production Mode

Update `docker-compose.yml` for production:

1. **Remove volume mounts** (use built image code):
   ```yaml
   backend:
     # Comment out or remove:
     # volumes:
     #   - ./backend:/app
   ```

2. **Use production server**:
   ```yaml
   backend:
     command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

3. **Build production web**:
   ```yaml
   web:
     command: npm run preview  # Serves built assets
   ```

4. **Add secrets management**:
   - Use Docker secrets
   - Or external secrets management (HashiCorp Vault, AWS Secrets Manager)

5. **Set production environment**:
   ```bash
   DEBUG=false
   LOG_LEVEL=WARNING
   ```

## Switching Vision Providers

### Switch to OpenAI

```bash
# Update .env
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Restart affected services
docker-compose restart backend celery_worker
```

### Switch to Gemini

```bash
# Update .env
VISION_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key-here

# Restart affected services
docker-compose restart backend celery_worker
```

No code changes needed - provider is selected via environment variable.

## Testing

### Upload a Test Image

```bash
# Create test device token
docker-compose exec backend python scripts/seed_db.py seed

# Upload test image (from another terminal)
curl -X POST http://localhost:8000/v1/ingest \
  -F "image=@test_image.jpg" \
  -F "device_id=test-device-001" \
  -F "device_token=test-token" \
  -F "trigger_type=manual" \
  -F "captured_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### Monitor Processing

```bash
# Watch Celery worker logs
docker-compose logs -f celery_worker

# Open Flower dashboard
open http://localhost:5555
```

### Check Inventory

```bash
# API
curl http://localhost:8000/v1/inventory | jq

# Web UI
open http://localhost:3000
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Rebuild images
docker-compose build

# Rebuild specific service
docker-compose build backend

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec backend python

# View resource usage
docker stats

# Tail logs
docker-compose logs -f --tail=100
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is ready
docker-compose exec db pg_isready -U pantry

# Connect to database
docker-compose exec db psql -U pantry -d pantry_db

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db
```

### Celery Not Processing Jobs

```bash
# Check Redis connection
docker-compose exec backend python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Check Celery worker health
docker-compose exec celery_worker celery -A app.workers.celery_app inspect active

# Restart worker
docker-compose restart celery_worker
```

### Vision API Errors

```bash
# Check environment variables
docker-compose exec backend env | grep -E 'VISION|OPENAI|GEMINI'

# Test vision provider (OpenAI)
docker-compose exec backend python -c "
from app.services.vision import VisionAnalyzer
import os
analyzer = VisionAnalyzer()
print(f'Provider: {analyzer.provider}')
print(f'Model: {analyzer.model}')
"

# Check worker logs for detailed errors
docker-compose logs celery_worker | grep -i error
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :5432

# Kill process or change port in docker-compose.yml
# Example: "8001:8000" maps host port 8001 to container 8000
```

### Out of Memory

```bash
# Check container memory usage
docker stats

# Limit Celery concurrency
docker-compose exec celery_worker celery -A app.workers.celery_app control pool_shrink 2

# Or update docker-compose.yml:
# celery_worker:
#   command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

## Health Checks

All services have health checks:

```bash
# Check all service health
docker-compose ps

# Test backend health endpoint
curl http://localhost:8000/health

# Check database
docker-compose exec backend python -c "
from app.db.database import engine
try:
    with engine.connect() as conn:
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database error: {e}')
"
```

## Data Persistence

Data is stored in Docker volumes:

- `postgres_data` - Database tables and rows
- `redis_data` - Job queue state

### Backup Database

```bash
# Dump database
docker-compose exec db pg_dump -U pantry pantry_db > backup.sql

# Restore database
docker-compose exec -T db psql -U pantry pantry_db < backup.sql
```

### Backup Images

Images are stored in `/app/uploads` inside backend container:

```bash
# Copy images from container
docker cp pantry-api:/app/uploads ./backup-uploads

# Restore images
docker cp ./backup-uploads pantry-api:/app/uploads
```

## Scaling

### Scale Celery Workers

```bash
# Run 3 worker instances
docker-compose up -d --scale celery_worker=3
```

### Load Balancing

For production, add a reverse proxy:

```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - backend
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `VISION_PROVIDER` | `openai` | Vision API provider (`openai` or `gemini`) |
| `OPENAI_API_KEY` | - | OpenAI API key (required if using OpenAI) |
| `OPENAI_MODEL` | `gpt-4-vision-preview` | OpenAI model name |
| `GEMINI_API_KEY` | - | Google Gemini API key (required if using Gemini) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `DATABASE_URL` | Auto-configured | PostgreSQL connection string |
| `DB_USER` | `pantry` | Database username |
| `DB_PASSWORD` | `pantry_secure_pass` | Database password |
| `DB_NAME` | `pantry_db` | Database name |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |

## Next Steps

1. Configure your vision provider in `.env`
2. Run `docker-compose up -d`
3. Seed test data: `docker-compose exec backend python scripts/seed_db.py seed`
4. Open web UI: http://localhost:3000
5. Check API docs: http://localhost:8000/docs
6. Monitor jobs: http://localhost:5555

For ESP32 firmware configuration, see [firmware/README.md](firmware/README.md).
