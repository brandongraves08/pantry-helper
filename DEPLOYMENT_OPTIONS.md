# Deployment Options Comparison

## Two Ways to Run Pantry Inventory

### 🐳 Option 1: Docker (Recommended for Production)

**Pros:**
- ✅ One command startup (`docker-compose up -d`)
- ✅ No manual dependency installation
- ✅ Consistent across all environments
- ✅ Includes database, Redis, all services
- ✅ Easy scaling (`--scale celery_worker=5`)
- ✅ Automatic health checks and restarts
- ✅ Perfect for deployment servers

**Cons:**
- ❌ Requires Docker installation (~1GB)
- ❌ Slower startup on first build

**Quick Start:**
```bash
cp .env.docker.example .env
nano .env  # Add API key
docker-compose up -d
docker-compose exec backend python scripts/seed_db.py seed
```

**Best for:** Production deployment, team development, CI/CD

---

### 🐍 Option 2: Local Python (Recommended for Development)

**Pros:**
- ✅ Faster iteration (hot reload)
- ✅ Direct access to Python debugger
- ✅ Easier to modify code
- ✅ No Docker overhead
- ✅ Uses SQLite (no PostgreSQL needed)

**Cons:**
- ❌ Manual dependency installation
- ❌ Need to manage Python, Node.js versions
- ❌ Database migrations manual
- ❌ "Works on my machine" syndrome

**Quick Start:**
```bash
./setup.sh
source venv/bin/activate
nano backend/.env  # Add API key
make backend-run  # Terminal 1
make web-dev      # Terminal 2
```

**Best for:** Local development, rapid prototyping, learning the codebase

---

## Feature Comparison

| Feature | Docker | Local Python |
|---------|--------|--------------|
| Setup time | 5 minutes (+ Docker install) | 3 minutes (+ dependencies) |
| Services included | All (db, redis, backend, worker, web) | Backend only (manual setup for others) |
| Database | PostgreSQL (production-ready) | SQLite (dev only) |
| Job queue | Celery + Redis (full async) | Optional (needs manual setup) |
| Environment isolation | Complete | Virtual env only |
| Port conflicts | None (containers) | Possible |
| Resource usage | ~500MB RAM | ~200MB RAM |
| Restart services | `docker-compose restart` | Kill + restart processes |
| Log viewing | `docker-compose logs` | Individual process logs |
| Scaling | `--scale celery_worker=N` | Manual process management |
| Deployment-ready | Yes ✅ | No (needs server setup) |

---

## When to Use Each

### Use Docker if you:
- ✅ Are deploying to a server
- ✅ Want a production-like environment
- ✅ Need Redis and Celery (async job processing)
- ✅ Work in a team (consistent setup)
- ✅ Want easy scaling
- ✅ Don't want to manage dependencies manually

### Use Local Python if you:
- ✅ Are actively developing/debugging
- ✅ Want fast code iteration
- ✅ Don't need full async processing
- ✅ Prefer lightweight setup
- ✅ Are learning the codebase
- ✅ Have limited disk space

---

## Hybrid Approach

**Best of both worlds:**

```bash
# Use Docker for infrastructure
docker-compose up -d db redis  # Just database and queue

# Run backend locally for development
source venv/bin/activate
cd backend
export DATABASE_URL=postgresql://pantry:pantry_secure_pass@localhost:5432/pantry_db
uvicorn app.main:app --reload

# Run worker locally
celery -A app.workers.celery_app worker --loglevel=info

# Run web locally
cd web
npm run dev
```

This gives you:
- ✅ Fast code iteration
- ✅ Production database (PostgreSQL)
- ✅ Full async processing (Celery)
- ✅ Easy debugging

---

## Migration Path

### Development → Production

1. **Develop locally** with `./setup.sh`
2. **Test with Docker** using `docker-compose up`
3. **Deploy with Docker** to your server

### Switching Between Methods

**Local → Docker:**
```bash
# Backup local database (if needed)
sqlite3 backend/pantry.db .dump > backup.sql

# Start Docker
cp .env.docker.example .env
docker-compose up -d
```

**Docker → Local:**
```bash
# Stop Docker services
docker-compose down

# Setup local environment
./setup.sh
source venv/bin/activate
make backend-run
```

---

## Performance Comparison

### Startup Time (Cold Start)

| Method | First Time | Subsequent |
|--------|------------|------------|
| Docker | ~60s (build) | ~15s |
| Local | ~20s | ~5s |

### Memory Usage

| Method | Minimum | Typical | With All Services |
|--------|---------|---------|-------------------|
| Docker | 300MB | 500MB | 800MB |
| Local | 100MB | 200MB | 400MB (manual setup) |

### Development Workflow

| Task | Docker | Local |
|------|--------|-------|
| Code change reload | ~2s | ~1s |
| Add dependency | Rebuild image (~30s) | `pip install` (~5s) |
| View logs | `docker-compose logs` | Terminal output |
| Debug with breakpoint | Need remote debugging | Native pdb/debugger |
| Database query | Through container | Direct connection |

---

## Recommendations by Use Case

### Solo Developer Learning Project
👉 **Local Python** - faster iteration, easier debugging

### Team of 2-5 Developers
👉 **Docker** - consistent environment, no setup issues

### Production Deployment
👉 **Docker** - only option, production-ready

### CI/CD Pipeline
👉 **Docker** - automated testing, deployment

### ESP32 Integration Testing
👉 **Docker** - full stack running, real backend API

### MVP Demo
👉 **Docker** - reliable, impressive, one-command setup

---

## Command Reference

### Docker Commands
```bash
make docker-up          # Start all services
make docker-down        # Stop all services  
make docker-logs        # View logs
make docker-seed        # Create test data
make docker-test        # Run tests
make docker-clean       # Full cleanup
```

### Local Commands
```bash
make backend-install    # Install backend deps
make backend-run        # Start backend
make backend-test       # Run backend tests
make web-install        # Install web deps
make web-dev            # Start web UI
./setup.sh              # Full setup
```

---

## Cost Comparison

### Infrastructure Requirements

| Component | Docker | Local |
|-----------|--------|-------|
| Disk space | ~2GB (images + volumes) | ~500MB (deps) |
| RAM required | 512MB minimum | 256MB minimum |
| CPU required | 1 core | 1 core |
| Docker install | Required | Not needed |
| Python 3.11+ | Included in image | Manual install |
| Node.js 18+ | Included in image | Manual install |
| PostgreSQL | Included in compose | Manual install (or use SQLite) |
| Redis | Included in compose | Manual install (optional) |

---

## The Bottom Line

**For your use case:**

- **Just exploring?** → Start with Local Python (`./setup.sh`)
- **Building a real pantry system?** → Use Docker
- **Showing this to someone?** → Docker (impressive one-liner)
- **Contributing code?** → Local for dev, Docker for testing
- **Deploying to Raspberry Pi/server?** → Docker only

Both methods support **multi-provider vision AI** (OpenAI/Gemini) with no code changes.

---

See also:
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Docker commands
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Full Docker documentation  
- [README.md](README.md) - Main project docs
- [VISION_PROVIDERS.md](VISION_PROVIDERS.md) - AI provider setup
