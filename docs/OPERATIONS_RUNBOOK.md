# Pantry Helper — Operational Runbook

> **Last Updated:** 2026-07-20
> **Host:** proxmox-02 LXC 202 (192.168.2.202)
> **Stack:** FastAPI + PostgreSQL + Celery + Redis + React (Docker Compose)

## Quick Reference Card

### 🖥️ Web UI
- **Pantry Helper:** http://pantry-helper.thelab.lan:3000
- **API Docs:** http://pantry-helper.thelab.lan:8000/docs

### 🐳 Service Management
All services managed via Docker Compose. SSH into the LXC first:

```bash
ssh openclaw@192.168.2.202
cd /home/brandon/pantry-helper
```

| Action | Command |
|--------|---------|
| View all services | `docker compose ps` |
| View logs (all) | `docker compose logs --tail=50 -f` |
| View API logs | `docker compose logs backend --tail=50 -f` |
| View worker logs | `docker compose logs celery_worker --tail=50 -f` |
| View web logs | `docker compose logs web --tail=50 -f` |
| Restart all | `docker compose restart` |
| Restart one service | `docker compose restart backend` |
| Rebuild + restart | `docker compose up -d --build <service>` |
| Graceful shutdown | `docker compose down` |
| Full restart | `docker compose down && docker compose up -d` |

### 🔍 Health Checks
| Check | URL |
|-------|-----|
| API health | http://pantry-helper.thelab.lan:8000/health |
| Flower (Celery) | http://pantry-helper.thelab.lan:5555 |
| PWA manifest | http://pantry-helper.thelab.lan:3000/manifest.webmanifest |

### 📊 Monitoring
- **Nagios:** http://loki.thelab.lan:8080/nagios/ (5 checks for pantry-helper)
- **Grafana Dashboard:** `/d/dfrpmw7636328d/pantry-helper-logs-and-health`
- **PBS Backups:** Daily automatic backup of LXC 202

### 📸 For Family (Daily Use)
1. Open Safari → `pantry-helper.thelab.lan:3000`
2. Tap Share → **Add to Home Screen** (runs fullscreen like an app)
3. Use **Scan Barcode** to add items by barcode
4. Use **Review Queue** to approve items detected by the AI
5. Check **Inventory** to see what's in stock
6. Check **Dashboard** for low stock and expiring items

---

## Service Architecture

```
                     ┌─────────────────┐
                     │   Traefik (LXC) │
                     │  (if cloudflare │
                     │   routing set)  │
                     └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
       │   Backend   │ │    Web     │ │   Flower    │
       │  :8000      │ │  :3000     │ │  :5555      │
       │  FastAPI    │ │  nginx     │ │  Celery     │
       │  gunicorn   │ │  React SPA │ │  monitor    │
       └──────┬──────┘ └────────────┘ └─────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌──▼──┐ ┌────▼────┐
│Postgres│ │Redis│ │ Celery  │
│  :5432 │ │:6379│ │ Worker  │
└───────┘ └─────┘ └─────────┘
```

---

## Service Management

### Checking Status
```bash
ssh openclaw@192.168.2.202
cd /home/brandon/pantry-helper
docker compose ps
```

Expected output — all services should show `Up` or `Up (healthy)`:
```
NAME              SERVICE         STATUS
pantry-db         db              Up (healthy)
pantry-redis      redis           Up (healthy)
pantry-api        backend         Up (healthy)
pantry-worker     celery_worker   Up (healthy)
pantry-web        web             Up (healthy)
pantry-flower     flower          Up (healthy)
pantry-promtail   promtail        Up
```

### Viewing Logs
```bash
# All services, streaming
docker compose logs --tail=50 -f

# Specific service
docker compose logs backend --tail=100 -f
docker compose logs celery_worker --tail=100 -f
docker compose logs web --tail=100 -f

# Last N lines (non-streaming)
docker compose logs --tail=200 backend
```

### Restarting Services
```bash
# Quick restart (keeps data containers running)
docker compose restart backend
docker compose restart web

# Full rebuild (after code changes)
docker compose build backend
docker compose up -d backend

# Rebuild and restart everything
docker compose build
docker compose up -d
```

### Code Deployments
After making changes to the source code:

1. **Backend changes** (Python):
   ```bash
   docker compose build backend celery_worker
   docker compose up -d backend celery_worker
   ```

2. **Web changes** (React/JSX):
   ```bash
   docker compose build web
   docker compose up -d web
   ```

3. **Config changes** (.env):
   ```bash
   docker compose up -d backend celery_worker web
   ```

---

## Health Checks

### API Health Endpoint
```bash
curl http://pantry-helper.thelab.lan:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "storage": {"status": "ok", "free_bytes": 3854364672, ...}
  }
}
```

The endpoint returns:
- **HTTP 200** — all healthy, or degraded but operational
- **HTTP 503** — database is down (critical - requires immediate action)

### Web Health Check
```bash
curl -s -o /dev/null -w "%{http_code}" http://pantry-helper.thelab.lan:3000/
# Expected: 200
```

---

## Backup & Restore

### PBS Backup (Automatic)
The LXC is backed up daily via Proxmox Backup Server. No manual action needed.

To verify last backup:
```bash
# From proxmox-02 host
pct status 202 | grep -i backup
```

### Database Backup
```bash
# Manual PostgreSQL dump
docker exec pantry-api python3 -c "
from app.db.database import SessionLocal
from app.db.models import *
import subprocess, json
subprocess.run(['pg_dump', '-c', '-f', '/tmp/pantry-dump.sql'])
"
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs for the failing service
docker compose logs backend --tail=50

# Common causes:
# - Port already in use (check with: ss -tlnp | grep 8000)
# - Database not ready (wait for pantry-db to show healthy)
# - Environment variables missing (check .env file)

# Force recreate
docker compose up -d --force-recreate backend
```

### Backend returns 500 errors
```bash
# Check worker and API logs
docker compose logs backend --tail=100
docker compose logs celery_worker --tail=100

# Common causes:
# - Vision provider unavailable (check OPENCLAW_GATEWAY_TOKEN)
# - Database connection issue
# - Storage full (check /health endpoint)

# Quick fix: restart both
docker compose restart backend celery_worker
```

### Vision analysis failing
```bash
# Check worker logs for VisionAnalysisError
docker compose logs celery_worker --tail=50

# Verify gateway token is mounted correctly
docker exec pantry-api cat /run/secrets/openclaw_gateway_token

# Test with mock provider (temporary)
# Set VISION_PROVIDER=mock in .env, then restart
```

### Web UI shows blank page
```bash
# Check web container
curl -s -o /dev/null -w "%{http_code}" http://pantry-helper.thelab.lan:3000/
# Expected: 200

# Check nginx error logs
docker compose logs web --tail=50

# Clear browser cache / hard reload (Cmd+Shift+R on Mac)
```

### Performance Issues
- LXC is limited to 2 vCPUs and 2GB RAM
- If slow, check: `docker stats` for resource usage
- Celery worker processes one capture at a time
- Vision analysis is the bottleneck (calls OpenClaw API)

---

## Configuration Reference

### Environment Variables (.env)
| Variable | Default | Description |
|----------|---------|-------------|
| `VISION_PROVIDER` | `openclaw` | Vision backend (`openclaw`, `openai`, `nvidia`, `mock`) |
| `VISION_MIN_CONFIDENCE` | `0.7` | Min confidence for auto-add to inventory |
| `VISION_MIN_SCENE_CONFIDENCE` | `0.3` | Min scene quality for auto-add |
| `LOG_LEVEL` | `WARNING` | Python log level |
| `IMAGE_RETENTION_DAYS` | `30` | Days to keep captured images |
| `MAX_STORAGE_MB` | `5000` | Max storage for images |

### Vision Confidence Bands
| Confidence | Meaning | Action |
|------------|---------|--------|
| 0.9+ | Brand label visible, clear | Auto-add to inventory |
| 0.7-0.89 | Clearly identifiable | Auto-add to inventory |
| 0.4-0.69 | Partial view, no brand | Goes to review queue |
| < 0.4 | Speculative | Goes to review queue |
| Scene < 0.3 | Blurry/dark image | All items go to review |

---

## Nagios Monitoring

5 active checks:
1. **API Health** — HTTP 200 from /health
2. **Web UI** — HTTP 200 from port 3000
3. **Flower** — HTTP 200 from port 5555
4. **NCPA CPU** — CPU usage on LXC
5. **NCPA Memory** — Memory usage on LXC

Alerts route to Discord #homelab-alerts.

---

## Quick Fixes

### "Capture not found" in logs
The CaptureProcessor creates its own database session. If you see this in testing, it means the test fixture's session is different from the worker's session. This is expected behavior — in production, captures are created via the API and processed by the worker in the same database.

### Port already in use
```bash
# Check what's using the port
ss -tlnp | grep <port>

# Kill the process if it's a stale container
docker stop <container-name>
docker rm <container-name>
```
