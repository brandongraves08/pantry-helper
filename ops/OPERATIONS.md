# Pantry Helper Operations

> Canonical operations guide for the live Pantry Helper deployment.

## Service Location

- **Host:** Proxmox LXC 202 on `proxmox-02` (192.168.2.202)
- **Project path (in LXC):** `/home/brandon/pantry-helper`
- **Project path (host-side):** `/home/brandon/pantry-helper`
- **Always verify live path** before redeploying — use `pct exec 202 -- pwd` to confirm.

## URLs

| Service | URL | Nagios |
|---------|-----|--------|
| Web UI | http://pantry-helper.thelab.lan:3000 | ✅ |
| API | http://pantry-helper.thelab.lan:8000 | ✅ |
| Flower (Celery) | http://pantry-helper.thelab.lan:5555 | ✅ |
| API Health | http://pantry-helper.thelab.lan:8000/health | — |

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

- **Nagios:** API (port 8000), Web (port 3000), Flower (port 5555) — all checked from `loki.thelab.lan`
- **NetBox:** device `pantry-helper`, primary IPv4 `192.168.2.202/24`
- **Loki/Promtail:** `pantry-promtail` ships all Docker container logs to `loki.thelab.lan:3100`
- **Docker healthchecks:** All services have `healthcheck` stanzas; unhealthy containers are reported through Nagios

## Configuration

Key env config: `/home/brandon/pantry-helper/.env`

```env
VISION_PROVIDER=openclaw
OPENCLAW_VISION_URL=http://172.16.1.1:18790/analyze
OPENCLAW_GATEWAY_TOKEN_FILE=/run/secrets/openclaw_gateway_token
OPENCLAW_VISION_MODEL=openai/gpt-5.4-mini
```

Vision routing:
- `mock` — returns canned results, no API calls
- `openclaw` — routes recognition through the OpenClaw gateway's chat completions endpoint

Docker containers reach OpenClaw image understanding through the user service
`openclaw-docker-gateway-proxy.service`, which binds only to the Pantry Docker bridge
`172.16.1.1:18790` and runs `openclaw infer image describe`.

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

## OpenClaw Integration

- **Skill:** `skills/pantry-helper/SKILL.md`
- **Scripts:** `skills/pantry-helper/scripts/` (pantry_status, pantry_api, pantry_report)
- **Plan:** `plans/active/pantry-helper-openclaw-integration-plan.md`
- **Cron jobs:** Daily digest (pantry state, low-stock, expiry, health)
- **Vision routing:** Uses the OpenClaw vision bridge (`http://172.16.1.1:18790/analyze`) for recognition
