# 🐳 Docker Quick Start

## One-Line Setup

```bash
# 1. Configure environment
cp .env.docker.example .env
# Edit .env with your vision API key

# 2. Start everything
docker-compose up -d

# 3. Seed test data
docker-compose exec backend python scripts/seed_db.py seed

# 4. Open web UI
open http://localhost:3000
```

## Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs  
- **Web UI**: http://localhost:3000
- **Flower (jobs)**: http://localhost:5555

## Essential Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Fresh restart (deletes data)
docker-compose down -v && docker-compose up -d

# Check status
docker-compose ps

# Run tests
docker-compose exec backend pytest tests/ -v
```

## Makefile Shortcuts

```bash
make docker-up       # Start all services
make docker-down     # Stop all services
make docker-build    # Rebuild images
make docker-logs     # Tail logs
make docker-seed     # Create test devices
make docker-test     # Run tests
make docker-clean    # Full cleanup
```

## Switch Vision Providers

### Use OpenAI
```bash
# Edit .env
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Restart
docker-compose restart backend celery_worker
```

### Use Gemini
```bash
# Edit .env
VISION_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key-here

# Restart
docker-compose restart backend celery_worker
```

## Test Upload

```bash
# Get device token
docker-compose exec backend python scripts/auth_utils.py test-device-001

# Upload image
curl -X POST http://localhost:8000/v1/ingest \
  -F "image=@your_image.jpg" \
  -F "device_id=test-device-001" \
  -F "device_token=YOUR_TOKEN_HERE" \
  -F "trigger_type=manual" \
  -F "captured_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Check inventory
curl http://localhost:8000/v1/inventory | jq
```

## Troubleshooting

```bash
# Check service health
docker-compose ps

# View specific service logs
docker-compose logs backend
docker-compose logs celery_worker

# Check database
docker-compose exec db psql -U pantry -d pantry_db

# Check environment
docker-compose exec backend env | grep VISION

# Restart specific service
docker-compose restart celery_worker
```

## Production Deployment

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for:
- Production configuration
- Security hardening
- Scaling workers
- Load balancing
- Backup/restore
- Monitoring

---

**Full documentation**: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
