# Phase 4: Docker Containerization & Deployment

**Status:** ✅ COMPLETE  
**Date:** January 15, 2026  
**Components:** Docker Compose, Dockerfiles, Deployment Guides

## Overview

Phase 4 provides complete containerization of the Pantry Inventory system using Docker and Docker Compose, enabling one-command deployment of all services (API, workers, database, Redis, web UI, monitoring).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React)         Backend API (FastAPI)              │
│  Port: 3000              Port: 8000                          │
│  ├─ npm run dev          ├─ uvicorn server                  │
│  └─ Hot reload           ├─ Rate limiting                    │
│                          └─ Health checks                    │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │         Celery Worker & Monitoring           │            │
│  ├──────────────────────────────────────────────┤            │
│  │  • Celery Worker (4 concurrency)             │            │
│  │  • Flower UI (Port 5555) for task monitoring │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │         Data & Message Services              │            │
│  ├──────────────────────────────────────────────┤            │
│  │  • PostgreSQL (Port 5432)                    │            │
│  │    └─ Database volume persistence            │            │
│  │  • Redis (Port 6379)                         │            │
│  │    └─ Job broker & result backend            │            │
│  │    └─ Data volume persistence                │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  Pantry Network (Bridge)                                     │
│  All containers communicate via service names                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services

### 1. PostgreSQL Database (`db`)
```yaml
Image: postgres:15-alpine
Port: 5432
Features:
  - Persistent volume storage
  - Health checks
  - Automatic recovery on restart
```

### 2. Redis Message Broker (`redis`)
```yaml
Image: redis:7-alpine
Port: 6379
Features:
  - Job queue broker
  - Result backend
  - Cache storage
  - Persistent volume
```

### 3. FastAPI Backend (`backend`)
```yaml
Build: ./backend/Dockerfile
Port: 8000
Features:
  - Auto-reload in development
  - Health checks
  - Environment configuration
  - Dependency on db and redis
```

### 4. Celery Worker (`celery_worker`)
```yaml
Build: ./backend/Dockerfile
Command: celery worker
Features:
  - 4 concurrent workers
  - Task processing
  - Auto-scaling ready
  - Depends on backend, db, redis
```

### 5. Flower Monitoring (`flower`)
```yaml
Build: ./backend/Dockerfile
Port: 5555
URL: http://localhost:5555
Features:
  - Real-time task monitoring
  - Worker statistics
  - Task history
  - Performance insights
```

### 6. React Frontend (`web`)
```yaml
Build: ./web/Dockerfile
Port: 3000
Features:
  - Hot reloading
  - Vite dev server
  - Environment configuration
  - API URL configuration
```

## Quick Start

### Prerequisites

- Docker Desktop (includes Docker & Docker Compose)
- Git
- 4GB RAM (minimum), 8GB recommended
- 10GB disk space for volumes

### 1. Clone Repository

```bash
git clone https://github.com/brandongraves08/pantry-helper.git
cd pantry-helper
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings (especially OPENAI_API_KEY)
nano .env
```

### 3. Start Services

```bash
# Start all containers in background
docker-compose up -d

# Watch logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web UI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Health | http://localhost:8000/health | Health check |
| Flower | http://localhost:5555 | Task monitoring |

## Development Workflow

### Running Commands in Container

```bash
# View logs
docker-compose logs backend
docker-compose logs celery_worker
docker-compose logs -f flower

# Access database
docker exec -it pantry-db psql -U pantry -d pantry_db

# Run tests in backend
docker-compose exec backend pytest tests/

# Database migrations
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic downgrade -1

# Seed database
docker-compose exec backend python scripts/seed_db.py
```

### Database Management

```bash
# Create backup
docker exec pantry-db pg_dump -U pantry pantry_db > backup.sql

# Restore from backup
docker exec -i pantry-db psql -U pantry pantry_db < backup.sql

# Connect to database shell
docker-compose exec db psql -U pantry -d pantry_db
```

### Worker Management

```bash
# View active tasks
docker-compose exec celery_worker celery -A app.workers.celery_app inspect active

# View worker stats
docker-compose exec celery_worker celery -A app.workers.celery_app inspect stats

# Purge queue
docker-compose exec celery_worker celery -A app.workers.celery_app purge

# Scale workers (requires docker-compose override)
docker-compose up -d --scale celery_worker=4
```

## Deployment Options

### Option 1: Development (Local Docker)

Perfect for development and testing.

```bash
# Start services
docker-compose up -d

# Logs
docker-compose logs -f

# Services auto-reload on code changes
```

### Option 2: Production Stack

For production deployment, use Docker Compose with health checks and proper resource limits.

**Create `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  backend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  celery_worker:
    restart: always
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1'
          memory: 1G

  db:
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_INITDB_ARGS: "-c shared_buffers=256MB"

  redis:
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Option 3: Kubernetes

Create `k8s-manifest.yml` for Kubernetes deployment (15+ services).

### Option 4: Cloud Deployment

#### AWS ECS
```bash
# Push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker build -t pantry-api ./backend
docker tag pantry-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/pantry-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/pantry-api:latest
```

#### Heroku
```bash
# Install Heroku CLI
npm install -g heroku

# Login and create app
heroku login
heroku create pantry-inventory

# Add database addon
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
```

#### DigitalOcean App Platform
- Connect GitHub repo
- Select Dockerfile for each service
- Configure environment variables
- Deploy (automatic on push)

## Monitoring & Debugging

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs celery_worker
docker-compose logs -f flower

# Last 50 lines
docker-compose logs --tail=50 backend

# Follow logs in real-time
docker-compose logs -f
```

### Container Management

```bash
# View running containers
docker-compose ps

# Inspect container
docker-compose exec backend sh

# Check resource usage
docker stats

# View container logs
docker logs pantry-api
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec db pg_isready -U pantry

# Redis health
docker-compose exec redis redis-cli ping

# Check service status
docker-compose ps
```

### Performance Monitoring

Access Flower at `http://localhost:5555`:
- Task execution graphs
- Worker CPU/memory usage
- Task success/failure rates
- Queue depth
- Worker health status

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Verify port availability
lsof -i :8000  # Check port 8000

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Test connection
docker-compose exec db psql -U pantry -d pantry_db -c "SELECT 1"

# View database logs
docker-compose logs db
```

### Worker Not Processing Jobs

```bash
# Check celery logs
docker-compose logs celery_worker

# Verify redis connection
docker-compose exec redis redis-cli ping

# Check active tasks
docker-compose exec celery_worker celery -A app.workers.celery_app inspect active

# Purge and restart
docker-compose restart celery_worker
```

### Out of Disk Space

```bash
# Clean up unused images/containers
docker system prune

# Remove all images and rebuild
docker-compose down
docker system prune -a
docker-compose up -d --build
```

## Performance Tuning

### Backend Settings

```env
# Number of Uvicorn workers
WORKERS=4

# Max requests before worker restart
MAX_REQUESTS=1000

# Request timeout
TIMEOUT=60
```

### Celery Settings

```env
# Worker concurrency
CELERY_CONCURRENCY=4

# Task time limit
CELERY_TIME_LIMIT=300

# Result expiration
CELERY_RESULT_EXPIRES=3600
```

### Database Optimization

```sql
-- Enable query performance logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log slow queries (>1s)

-- Increase shared buffers (for 4GB RAM server)
ALTER SYSTEM SET shared_buffers = '1GB';

-- Enable autovacuum
ALTER SYSTEM SET autovacuum = on;
```

### Redis Optimization

```bash
# For high throughput
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Enable persistence
redis-cli CONFIG SET save "60 1000"  # Save every 60s if 1000+ changes
```

## Scaling

### Horizontal Scaling (Multiple Workers)

```bash
# Scale celery workers to 4 instances
docker-compose up -d --scale celery_worker=4

# Scale backend servers (load balanced)
docker-compose up -d --scale backend=3
```

### Vertical Scaling (More Resources)

Edit `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

### Database Replication

```yaml
db-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_REPLICATION_MODE: slave
    POSTGRES_REPLICATION_HOST: db
  depends_on:
    - db
```

## Backup & Recovery

### Automated Backups

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec pantry-db pg_dump -U pantry pantry_db > $BACKUP_DIR/pantry_db_$TIMESTAMP.sql

# Backup redis
docker exec pantry-redis redis-cli BGSAVE
docker cp pantry-redis:/data/dump.rdb $BACKUP_DIR/redis_$TIMESTAMP.rdb

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh  # Run daily at 2 AM
```

## Security Best Practices

### Environment Variables

✅ **DO:**
- Store secrets in `.env` (not committed)
- Use strong database passwords
- Rotate API keys regularly

❌ **DON'T:**
- Commit `.env` file to git
- Use default passwords in production
- Expose Docker socket to containers

### Network Security

```yaml
networks:
  pantry-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-pantry

services:
  backend:
    networks:
      - pantry-network
    expose:
      - 8000  # Internal only
    ports:
      - "8000:8000"  # External access
```

### Database Security

```bash
# Change postgres password
docker-compose exec db psql -U pantry -d pantry_db \
  -c "ALTER USER pantry WITH PASSWORD 'new_secure_password';"

# Create read-only user
docker-compose exec db psql -U pantry -d pantry_db <<EOF
CREATE USER pantry_readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE pantry_db TO pantry_readonly;
GRANT USAGE ON SCHEMA public TO pantry_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pantry_readonly;
EOF
```

## Cost Optimization

### For Development
- Use `alpine` images (smaller)
- Single worker instance
- Smaller resource limits

### For Production
- Use `slim` base images
- Multiple worker instances
- Proper resource allocation
- Data volume caching

### Estimated Monthly Costs

| Platform | Config | Cost |
|----------|--------|------|
| Local Docker | 2 CPU, 4GB RAM | $0 |
| DigitalOcean | Basic app | $5-12 |
| AWS ECS | 2 tasks | $15-30 |
| Heroku | Basic plan | $25-50 |
| Kubernetes (self) | 3 node cluster | $50+ |

## Next Phase (Phase 5)

Phase 5 will add:
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing on push
- [ ] Automated deployment
- [ ] Database migrations
- [ ] Backup automation
- [ ] Monitoring alerts (Sentry, PagerDuty)

## Summary

**Phase 4 Deliverables:**
- ✅ Docker Compose stack (6 services)
- ✅ Backend Dockerfile (production-ready)
- ✅ Frontend Dockerfile (optimized)
- ✅ Environment configuration
- ✅ Development workflow documentation
- ✅ Production deployment guide
- ✅ Monitoring setup with Flower
- ✅ Scaling and performance tuning
- ✅ Backup & recovery procedures
- ✅ Security best practices
- ✅ Cost optimization guide

**Status: Phase 4 COMPLETE - Production-ready containerized deployment** 🚀
