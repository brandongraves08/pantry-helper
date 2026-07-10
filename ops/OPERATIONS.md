# Pantry Helper Operations

> Canonical operations guide for the live Pantry Helper deployment.

## Service Location

- **Host:** Proxmox LXC 202 on `proxmox-02` (192.168.2.202)
- **Project path (in LXC):** `/home/brandon/pantry-helper`
- **Project path (host-side):** `/home/brandon/pantry-helper`
- **Always verify live path** before redeploying — use `pct exec 202 -- pwd` to confirm.

## URLs

| Service | URL | Nagios | Notes |
|---------|-----|--------|-------|
| Web UI | http://pantry-helper.thelab.lan:3000 | ✅ | React dashboard — devices, inventory, captures |
| API | http://pantry-helper.thelab.lan:8000 | ✅ | FastAPI backend — docs at /docs |
| API Health | http://pantry-helper.thelab.lan:8000/health | ✅ | Enhanced: checks DB + Redis + storage, 503 on critical |
| Flower (Celery) | http://pantry-helper.thelab.lan:5555 | ✅ | Celery task queue monitoring |
| Grafana | https://grafana.homelab.graveystudios.com | — | Pantry dashboard: `/d/dfrpmw7636328d` |

## Access

```bash
# Preferred: direct service-account access to the LXC
ssh openclaw@192.168.2.202

# Proxmox host access is available for maintenance, but routine service work
# should happen through openclaw on the LXC.
ssh openclaw@192.168.2.227
```

The `openclaw` account has sudo/docker access inside LXC 202 for deployments.
The project `.env` must remain readable by `openclaw` (`root/openclaw` or
`brandon/openclaw`, mode `0640`) so `docker compose` can load it without
falling back to another account.

## Stack Status

```bash
sudo pct exec 202 -- docker ps --format 'table {{.Names}}\t{{.Status}}'
```

Expected: `pantry-api`, `pantry-worker`, `pantry-web`, `pantry-flower`, `pantry-db`, `pantry-redis`, `pantry-promtail` all healthy.

## Restart Procedures

### Full stack restart
```bash
sudo pct exec 202 -- bash -c "cd /home/brandon/pantry-helper && docker compose up -d --build"
```

### Single service rebuild
```bash
sudo pct exec 202 -- bash -c "cd /home/brandon/pantry-helper && docker compose up -d --build <service>"
# Services: pantry-api, pantry-worker, pantry-web, pantry-flower
```

### Web UI only (frontend rebuild)
```bash
sudo pct exec 202 -- bash -c "cd /home/brandon/pantry-helper && docker compose up -d --build pantry-web"
```

### Database reset (loses all data)
```bash
sudo pct exec 202 -- bash -c "cd /home/brandon/pantry-helper && docker compose down pantry-db && docker volume rm pantry-helper_postgres_data && docker compose up -d pantry-db"
```

## Backups

- **Timer:** `pantry-helper-backup.timer` (systemd on LXC)
- **Service:** `pantry-helper-backup.service`
- **Script:** `/home/brandon/pantry-helper/backup.sh`
- **Destination:** Docker volume backup or local tarball

```bash
# Check timer status
sudo pct exec 202 -- systemctl status pantry-helper-backup.timer

# Trigger manual backup
sudo pct exec 202 -- systemctl start pantry-helper-backup.service

# View last backup log
sudo pct exec 202 -- journalctl -u pantry-helper-backup.service --no-pager -n 50
```

## Monitoring

### NetBox (Source of Truth)
- **VM:** `pantry-helper` (ID 21), cluster `proxmox-02`, role `Container`
- **Primary IPv4:** `192.168.2.202/24` assigned to `eth0` virtual interface (ID 11)
- **Tags:** `lxc`, `docker`

### Nagios (✅ Active — 5 checks)

**Host definition:** `pantry-helper` (192.168.2.202) in `/home/brandon/nagios-core/custom-plugins/pantry_helper.cfg`

| Check | Type | Current Status |
|-------|------|----------------|
| Pantry API Health | HTTP (pantry-helper.thelab.lan:8000/health) | ✅ OK |
| Pantry Web UI | HTTP (pantry-helper.thelab.lan:3000/) | ✅ OK |
| Pantry Flower Dashboard | HTTP (pantry-helper.thelab.lan:5555/) | ✅ OK |
| NCPA CPU | NCPA agent (LXC 202:5693) | ✅ OK |
| NCPA Memory | NCPA agent (LXC 202:5693) | ✅ OK |

**Validate config:** `python3 scripts/nagios_validate.py` (runs `nagios -v` in container on loki.thelab.lan)

**Refresh Nagios after config change:**
```bash
ssh brandon@loki.thelab.lan "docker exec nagios-core /opt/nagios/bin/nagios -v /opt/nagios/etc/nagios.cfg"
ssh brandon@loki.thelab.lan "docker exec nagios-core /opt/nagios/bin/nagios -s /opt/nagios/var/rw/nagios.cmd"
```

### Loki / Promtail
- `pantry-promtail` ships all Docker container logs to `loki.thelab.lan:3100`
- Label: `project="pantry-helper"` — use this in LogQL queries
- Container names in `attrs_tag` stream (e.g., `pantry-api`, `pantry-web`)
- All containers emit structured JSON logs to stdout/stderr
- Nginx uses JSON format with upstream response info
- API middleware logs request IDs, timing, and status for every request

**Loki Alert Rules (3 active):**
| Rule | Condition | Severity |
|------|-----------|----------|
| PantryHelperHighErrorRate | >10 error/fatal/critical lines in 5min | warning → Discord |
| PantryHelperCriticalErrors | Any fatal/critical/panic line | critical → Discord |
| PantryHelperNoRecentLogs | Zero log activity for 10min | critical → Discord |

Rules location: `/loki/rules/fake/pantry-helper-alerts.yaml` inside Loki container.

**Grafana Dashboard:**
- URL: `/d/dfrpmw7636328d/pantry-helper-logs-and-health`
- Panels: log volume, error events, per-source breakdown, recent logs

### Docker Healthchecks
- All services have `healthcheck` stanzas
- Health endpoints: `http://pantry-helper.thelab.lan:8000/health` (API), `:3000` (web)

## Configuration

Key env config: `/home/brandon/pantry-helper/.env`

```env
VISION_PROVIDER=openclaw
OPENCLAW_VISION_URL=http://172.16.1.1:18790/analyze
OPENCLAW_GATEWAY_TOKEN_FILE=/run/secrets/openclaw_gateway_token
OPENCLAW_VISION_MODEL=openai/gpt-5.4-mini
DATABASE_URL=postgresql://pantry:***@db/pantry_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
IMAGE_RETENTION_DAYS=30
MAX_STORAGE_MB=5000
LOG_LEVEL=INFO
```

Vision routing:
- `mock` — returns canned results, no API calls
- `openclaw` — routes recognition through the OpenClaw gateway's chat completions endpoint

Docker containers reach OpenClaw image understanding through the user service
`openclaw-docker-gateway-proxy.service`, which binds only to the Pantry Docker bridge
`172.16.1.1:18790` and runs `openclaw infer image describe`.

## Docker Images

| Image | Size | Notes |
|-------|------|-------|
| pantry-helper-backend | **355MB** | Python 3.12-slim, multi-stage, no ImageMagick |
| pantry-helper-celery_worker | **355MB** | Same image as backend (different CMD) |
| pantry-helper-flower | **355MB** | Same image as backend (different CMD) |
| pantry-helper-web | **93.6MB** | Nginx alpine serving Vite-built React |

**Build optimization:** `--no-install-recommends` avoids ImageMagick (~100MB+ savings from libzbar0 Recommends).
Test deps (pytest, httpx) split into `requirements-dev.txt` — not in production images.

**Full rebuild (all services):**
```bash
ssh openclaw@192.168.2.202 "cd /home/brandon/pantry-helper && docker compose build --no-cache && docker compose up -d"
```

**Single service rebuild:**
```bash
ssh openclaw@192.168.2.202 "cd /home/brandon/pantry-helper && docker compose up -d --build <service>"
# Services: backend (API), celery_worker, web, flower
```

## Logs

```bash
# All container logs (Loki-forwarded)
sudo pct exec 202 -- docker compose logs --tail=100 -f

# Specific service
sudo pct exec 202 -- docker compose logs --tail=50 pantry-worker -f
sudo pct exec 202 -- docker compose logs --tail=50 pantry-api -f
```

## Known Blocker

**Synology shared drive not mounted in LXC 202.**
Unprivileged LXC prevents direct NFS mount. Need a Proxmox host-side bind mount during a maintenance window to mount the Synology NFS share and pass it through to the LXC.

## Deployment Flow

1. Make changes to `/home/brandon/pantry-helper/`.
2. Copy changed files to LXC 202 with `scp` or git sync as `openclaw`.
3. SSH into LXC as `openclaw` and rebuild: `cd /home/brandon/pantry-helper && docker compose up -d --build`
4. Verify: `curl -fsS http://localhost:8000/health && curl -fsS -o /dev/null -w "%{http_code}" http://localhost:3000`

## API Endpoints (Key Routes)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (DB, Redis, storage; HTTP 503 on critical) |
| GET | `/docs` | Swagger API docs |
| GET | `/v1/inventory` | List current inventory |
| POST | `/v1/inventory/override` | Manually set item count (with location/expiry) |
| GET | `/v1/inventory/export/csv` | Download inventory as CSV |
| GET | `/v1/inventory/history` | Inventory change history (query: `?days=7`) |
| GET | `/v1/devices` | List registered devices |
| POST | `/v1/devices` | Register new device (returns token) |
| GET | `/v1/devices/{id}/health` | Device health metrics (battery, captures, success%) |
| DELETE | `/v1/devices/{id}` | Remove device |
| POST | `/v1/captures/manual` | Upload image manually (multipart form) |
| POST | `/v1/ingest` | ESP32 image ingest (token auth) |
| GET | `/v1/reviews` | Pending review queue (detections needing approval) |
| GET | `/v1/zones` | List storage zones/locations |
| GET | `/v1/household/members` | List household members |
| POST | `/admin/storage/cleanup` | Trigger image retention cleanup (`?days=30`) |

Full API reference: http://pantry-helper.thelab.lan:8000/docs

## OpenClaw Integration

- **OpenClaw Project Plan:** `~/.openclaw/workspace/projects/pantry-helper/plan.json`
- **Check-in cron:** Weekly (Monday 5pm CT) — `checkin:pantry-helper`
- **Vision routing:** Currently configured as `VISION_PROVIDER=openclaw` on the LXC (OpenClaw gateway). Provider can be switched to `nvidia` (NVIDIA NIM) or `openai` via `.env`
