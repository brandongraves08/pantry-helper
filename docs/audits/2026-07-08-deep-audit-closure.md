# Pantry Helper Deep Audit Closure - 2026-07-08

## Scope

Full project audit and remediation for Pantry Helper on LXC 202 (`192.168.2.202`): Docker stack, secrets/provider config, deployment hygiene, service health, backups, monitoring, host hardening, NetBox, and shared-drive standing order.

## Fixed

- Removed Gemini runtime use:
  - Removed `GEMINI_*` environment variables from Compose-managed containers.
  - Removed Gemini provider code path from `backend/app/services/vision.py`.
  - Removed `google-generativeai` from `backend/requirements.txt`.
- Prepared OpenAI vision path:
  - Kept OpenAI provider support and `OPENAI_MODEL=gpt-4o`.
  - `VISION_PROVIDER` remains `mock` until a valid OpenAI API key is available.
- Hardened Docker deployment:
  - Removed host exposure for Postgres; it is Docker-network-only.
  - Removed backend/web source bind mounts from Compose.
  - Built web as nginx static production image instead of Vite dev server.
  - Fixed API, worker, Flower, and web healthchecks.
  - Added `gunicorn` to backend requirements so the production override can run.
- Cleaned repo hygiene:
  - Added backup-directory ignore patterns to `.gitignore`.
  - Unstaged the old `pantry-helper.bak.*` backup tree.
- Host hardening:
  - Applied Debian package updates.
  - Enabled UFW with LAN-only access for SSH, web, API, and Flower.
  - Installed and enabled fail2ban with the SSH jail using the systemd backend.
  - Pruned Docker builder cache.
- Backups:
  - Updated `backup.sh` for Docker Compose v2 and absolute project paths.
  - Installed `pantry-helper-backup.timer` for daily persistent backups.
  - Verified a manual backup run created Postgres and Redis backups.
- Monitoring:
  - Added `check_pantry_helper.py` to Nagios custom plugins.
  - Added Nagios checks for API `/health`, Web UI, and Flower.
  - Validated Nagios config and restarted `nagios-core`.
- NetBox:
  - Confirmed `pantry-helper` device record exists.
  - Added `eth0`, assigned `192.168.2.202/24`, and set it as primary IPv4.

## Verified Snapshot

- `pantry-api`: healthy, `8000/tcp` exposed to LAN.
- `pantry-web`: healthy, nginx production image, `3000/tcp` exposed to LAN.
- `pantry-worker`: healthy.
- `pantry-flower`: healthy, `5555/tcp` exposed to LAN.
- `pantry-db`: healthy, Docker-network-only `5432/tcp`.
- `pantry-redis`: healthy, Docker-network-only `6379/tcp`.
- `pantry-promtail`: running.
- Nagios pre-flight: 0 warnings, 0 errors.
- NetBox primary IP: `192.168.2.202/24`.
- `apt list --upgradable`: no pending package list beyond header.

## Remaining Blocker

- Synology shared drive is not mounted in LXC 202.
- Attempted NFS mount: `media-server.thelab.lan:/volume1/Shared` to `/mnt/synology-shared`.
- Result: `mount.nfs: Operation not permitted`.
- Reason: LXC 202 is unprivileged; direct NFS mount requires host-side bind mount or container privilege/capability changes.
- Next safe fix: mount the Synology share on `proxmox-02` and bind-mount it into LXC 202 during a maintenance restart.

