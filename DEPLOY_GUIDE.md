# Phase 4: Quick Deployment Guide

## One-Command Deployment

### Development (Local)

```bash
# Clone and deploy
git clone https://github.com/brandongraves08/pantry-helper.git
cd pantry-helper
chmod +x deploy.sh
./deploy.sh start
```

**Access:**
- 🌐 Web UI: http://localhost:3000
- 📚 API Docs: http://localhost:8000/docs
- 📊 Task Monitor: http://localhost:5555

### Production (VPS/Cloud)

```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone https://github.com/brandongraves08/pantry-helper.git
cd pantry-helper

# Create .env with production values
cp .env.example .env
nano .env  # Edit with real values

# Deploy with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database
docker-compose exec backend python scripts/seed_db.py

# Check status
./deploy.sh status
```

## File Structure

```
pantry-helper/
├── docker-compose.yml          # Development config
├── docker-compose.prod.yml     # Production overrides
├── .env.example               # Environment template
├── deploy.sh                  # Deployment script
├── backup.sh                  # Database backup script
├── backend/
│   ├── Dockerfile             # Backend container
│   ├── requirements.txt        # Python dependencies
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Configuration
│   │   ├── db/               # Database models
│   │   ├── api/              # API routes
│   │   ├── workers/          # Celery tasks
│   │   └── middleware/       # Rate limiting
│   └── tests/                # Test suite
├── web/
│   ├── Dockerfile             # Frontend container
│   ├── package.json          # Node dependencies
│   └── src/                  # React code
├── .github/
│   └── workflows/
│       └── cicd.yml          # GitHub Actions
└── PHASE_4_DEPLOYMENT.md     # Full documentation
```

## Docker Compose Services

| Service | Port | Purpose | Language |
|---------|------|---------|----------|
| `backend` | 8000 | API server | Python/FastAPI |
| `web` | 3000 | Frontend | React/Vite |
| `db` | 5432 | Database | PostgreSQL |
| `redis` | 6379 | Job broker | C |
| `celery_worker` | - | Task processor | Python |
| `flower` | 5555 | Monitoring | Python |

## Configuration

### .env File

```bash
# Copy template
cp .env.example .env

# Required variables
DB_USER=pantry
DB_PASSWORD=<secure_password>
OPENAI_API_KEY=<your_api_key>
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `OPENAI_API_KEY` | - | OpenAI Vision API key |
| `LOG_LEVEL` | INFO | Logging level |
| `DEBUG` | false | Enable debug mode |

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### Database Operations

```bash
# Connect to database
docker-compose exec db psql -U pantry -d pantry_db

# Run migrations
docker-compose exec backend alembic upgrade head

# Backup database
./backup.sh

# Restore backup
docker-compose exec -i db psql -U pantry pantry_db < backups/pantry_db_*.sql
```

### Worker Management

```bash
# View active tasks
docker-compose exec celery_worker celery -A app.workers.celery_app inspect active

# Scale workers
docker-compose up -d --scale celery_worker=4

# Restart worker
docker-compose restart celery_worker
```

### Performance Monitoring

```bash
# View resource usage
docker stats

# Check service health
docker-compose ps

# View specific logs
docker-compose logs --tail=100 backend
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs <service>

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Database connection error

```bash
# Test connection
docker-compose exec db psql -U pantry -d pantry_db -c "SELECT 1"

# Check logs
docker-compose logs db
```

### Out of disk space

```bash
# Clean up
docker system prune -a
docker volume prune

# Remove all and rebuild
docker-compose down -v
docker-compose up -d --build
```

## Security Checklist

- [ ] Changed default PostgreSQL password
- [ ] Set strong OpenAI API key
- [ ] Configured firewall rules
- [ ] Enabled HTTPS/SSL certificate
- [ ] Set up automatic backups
- [ ] Configured monitoring alerts
- [ ] Reviewed rate limiting settings
- [ ] Set up log rotation

## Backup Strategy

```bash
# Daily automated backup
0 2 * * * cd /opt/pantry-helper && ./backup.sh

# Manual backup
./backup.sh

# Restore from backup
gunzip -c backups/pantry_db_20260115_020000.sql.gz | \
  docker-compose exec -i db psql -U pantry pantry_db
```

## Scaling

```bash
# Add more workers
docker-compose up -d --scale celery_worker=8

# Add more API instances (with load balancer)
docker-compose up -d --scale backend=3

# Check status
docker-compose ps
```

## Next Steps

1. ✅ Deploy locally with `./deploy.sh start`
2. ✅ Test all endpoints
3. ✅ Configure production `.env`
4. ✅ Deploy to VPS/Cloud
5. ✅ Setup monitoring (Flower, logs)
6. ✅ Configure backups
7. ✅ Monitor performance

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- View deployment guide: `PHASE_4_DEPLOYMENT.md`
- Check GitHub issues: https://github.com/brandongraves08/pantry-helper/issues

---

**Phase 4 Status: ✅ COMPLETE** 🚀

All services containerized and ready for production deployment!
