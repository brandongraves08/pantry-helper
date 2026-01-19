# Phase 7: Production Deployment Guide

**Status**: Phase 6 Complete → Phase 7 In Progress  
**Date**: January 19, 2026  
**Objective**: Deploy full stack (backend + web UI + database) using Docker

---

## 🐳 Docker Deployment

### Prerequisites
- Docker Engine 20.10+ (✓ installed)
- Docker Compose v2+ (✓ v5.0.1)
- Vision API key (OpenAI or Gemini)

### Quick Start (Recommended)

**Step 1: Configure environment**
```bash
cp .env.docker .env
# Edit .env with your Vision API key
```

**Step 2: Build images**
```bash
docker compose build
```

**Step 3: Start services**
```bash
# Start all services (db, redis, backend, worker, flower, web)
docker compose up -d

# Watch logs
docker compose logs -f

# Check status
docker compose ps
```

**Step 4: Seed test data**
```bash
docker compose exec backend python scripts/seed_db.py seed
```

**Step 5: Access services**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Web UI**: http://localhost:3000
- **Flower (Job Monitor)**: http://localhost:5555

---

## 📊 Service Architecture

### Services Running
1. **PostgreSQL** (db:5432)
   - Primary data store
   - Migrations auto-run
   
2. **Redis** (redis:6379)
   - Job queue broker
   - Celery result backend
   - Cache backend

3. **FastAPI Backend** (backend:8000)
   - API endpoints
   - Device authentication
   - Image ingestion
   - Auto-reloads on code changes

4. **Celery Worker** (celery_worker:5555)
   - Async image analysis
   - Vision API calls
   - Inventory processing

5. **Flower** (flower:5555)
   - Job monitoring UI
   - Task history
   - Worker stats

6. **React Web UI** (web:3000)
   - Inventory dashboard
   - Device management
   - Analytics

---

## 🔧 Common Operations

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery_worker
```

### Stop Services
```bash
# Stop (keep data)
docker compose stop

# Restart
docker compose up -d
```

### Full Cleanup
```bash
# Stop + Remove containers + Remove volumes
docker compose down -v
```

### Execute Commands in Container
```bash
# Run migrations
docker compose exec backend python -m alembic upgrade head

# Run tests
docker compose exec backend pytest tests/ -v

# Access database
docker compose exec db psql -U pantry -d pantry_db
```

---

## 🧪 Testing End-to-End Flow

### 1. Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/v1/admin/health/db
```

### 2. Create Test Device
```bash
curl -X POST http://localhost:8000/v1/admin/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "device_id": "test-camera-001"
  }'
```

### 3. Simulate Image Upload
```bash
# Get a test device token first
curl http://localhost:8000/v1/devices | jq '.devices[0]'

# Upload image (requires actual JPEG)
curl -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@test_image.jpg" \
  -F "device_id=test-camera-001" \
  -F "trigger_type=door"
```

### 4. Check Inventory
```bash
# Get current inventory
curl http://localhost:8000/v1/inventory | jq .

# Get device status
curl http://localhost:8000/v1/devices | jq .
```

---

## 🔒 Security Checklist

- [ ] Change `DB_PASSWORD` from default
- [ ] Set valid `OPENAI_API_KEY`
- [ ] Set `DEBUG=false` in production
- [ ] Use HTTPS reverse proxy (nginx/traefik)
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Monitor logs for errors
- [ ] Set resource limits in docker-compose

---

## 📈 Scaling Considerations

### Single Server (Current Setup)
- Good for: Development, small-scale testing
- Max throughput: ~10 captures/min with default config

### Multi-Worker Setup
```yaml
# Scale Celery workers
celery_worker_1:
  # ... config

celery_worker_2:
  # ... config
  # Worker 2 config same as Worker 1
```

### Distributed Deployment
- Use managed PostgreSQL (RDS, Cloud SQL)
- Use managed Redis (ElastiCache, Memorystore)
- Deploy backend to Kubernetes/ECS
- Use CDN for images
- Add load balancer

---

## 🚨 Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs

# Verify images built
docker images | grep pantry

# Rebuild
docker compose build --no-cache
```

### Database connection errors
```bash
# Check database is running
docker compose ps db

# Test connection
docker compose exec backend \
  python -c "from app.db.database import engine; \
  engine.execute('SELECT 1')"
```

### Worker not processing jobs
```bash
# Check worker is running
docker compose ps celery_worker

# View worker logs
docker compose logs -f celery_worker

# Check job queue in Flower: http://localhost:5555
```

### Out of storage
```bash
# Check space usage
docker compose exec backend du -sh /app/storage

# Configure retention
# Edit .env: IMAGE_RETENTION_DAYS=7  # Keep only 7 days
```

---

## 📝 Production Checklist

Before deploying to production:

- [ ] Set strong database password
- [ ] Configure vision API key securely (use secrets manager)
- [ ] Enable HTTPS with valid certificate
- [ ] Set up log aggregation (e.g., ELK stack)
- [ ] Configure database backups
- [ ] Set resource limits on containers
- [ ] Configure health checks
- [ ] Set up monitoring and alerting
- [ ] Create incident runbooks
- [ ] Document runbook procedures

---

## 🔄 CI/CD Integration

Add to GitHub Actions:
```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Build Docker images
      run: docker compose build
    - name: Run tests
      run: docker compose run backend pytest
    - name: Deploy
      run: docker compose up -d
```

---

## 📞 Support & Next Steps

**Immediate**: 
- [ ] Configure .env with real API keys
- [ ] Run `docker compose up` and verify all services start
- [ ] Test API endpoints and Web UI

**Short-term**:
- [ ] Set up production database backups
- [ ] Configure log aggregation
- [ ] Implement monitoring/alerting

**Long-term**:
- [ ] Kubernetes deployment
- [ ] Multi-region replication
- [ ] Advanced analytics

