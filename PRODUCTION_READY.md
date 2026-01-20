# 🚀 PRODUCTION DEPLOYMENT - LIVE SYSTEM

## System Status: **PRODUCTION** ✅

**Deployed:** January 19, 2026  
**Version:** 1.0.0  
**Environment:** Production

---

## Production Configuration

### Security Hardening
- ✅ DEBUG mode disabled (`DEBUG=false`)
- ✅ Production database credentials set
- ✅ Logging set to WARNING level (production-appropriate)
- ✅ Test data completely removed
- ✅ All services configured with `restart: always`

### Database Configuration
```
Database: pantry_production
User: pantry
Password: [Secured - see .env.docker]
```

### Services Running
```
✅ PostgreSQL 15 - Production database
✅ Redis 7 - Job queue and caching
✅ FastAPI - Backend API (port 8000)
✅ React/Vite - Web UI (port 3000)
✅ Celery Worker - Async image processing
✅ Flower - Task monitoring (port 5555)
```

---

## Access Points

### API Endpoints
- **Health Check:** http://rhel-01.thelab.lan:8000/health
- **API Docs:** http://rhel-01.thelab.lan:8000/docs
- **Device Ingest:** http://rhel-01.thelab.lan:8000/v1/ingest
- **Inventory API:** http://rhel-01.thelab.lan:8000/v1/inventory

### Web Interface
- **Dashboard:** http://rhel-01.thelab.lan:3000

### Monitoring
- **Flower Dashboard:** http://rhel-01.thelab.lan:5555

---

## ESP32 Configuration

### Firmware Settings Required
Edit `firmware/src/config/config.cpp`:

```cpp
strcpy(Config::settings.ssid, "YOUR_WIFI_SSID");
strcpy(Config::settings.password, "YOUR_WIFI_PASSWORD");
strcpy(Config::settings.device_id, "pantry-cam-001");  // Choose unique ID
strcpy(Config::settings.api_endpoint, "http://rhel-01.thelab.lan:8000/v1/ingest");
strcpy(Config::settings.api_token, "YOUR_DEVICE_TOKEN");  // Generate via API
```

### Generate Device Token
```bash
# Register new device
curl -X POST http://rhel-01.thelab.lan:8000/v1/admin/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kitchen Pantry Camera",
    "device_id": "pantry-cam-001"
  }'

# Response will include token - copy this to firmware config
```

### Build and Upload Firmware
```bash
cd firmware
python3 -m platformio run -e esp32-cam        # Build
python3 -m platformio run -e esp32-cam -t upload  # Upload to device
python3 -m platformio device monitor           # Monitor output
```

---

## Production Operations

### Start All Services
```bash
docker compose up -d
```

### Stop All Services
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f celery_worker  # Worker only
```

### Check Service Status
```bash
docker compose ps
```

### Database Backup
```bash
docker compose exec db pg_dump -U pantry pantry_production > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
cat backup_YYYYMMDD.sql | docker compose exec -T db psql -U pantry pantry_production
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# API health
curl http://rhel-01.thelab.lan:8000/health

# Database connectivity
docker compose exec db psql -U pantry -d pantry_production -c "SELECT COUNT(*) FROM devices;"

# Redis connectivity
docker compose exec redis redis-cli ping
```

### View Active Devices
```bash
curl http://rhel-01.thelab.lan:8000/v1/devices
```

### View Current Inventory
```bash
curl http://rhel-01.thelab.lan:8000/v1/inventory
```

### Task Queue Monitoring
Visit http://rhel-01.thelab.lan:5555 for Flower dashboard

---

## Production Checklist ✅

- [x] DEBUG mode disabled
- [x] Production database credentials set
- [x] Test data removed
- [x] All services configured with restart policies
- [x] Logging set to appropriate level (WARNING)
- [x] Health checks configured
- [x] Database backups planned
- [x] Monitoring enabled (Flower)
- [x] API documentation available
- [x] Web UI accessible
- [ ] ESP32 devices configured
- [ ] WiFi credentials added to firmware
- [ ] First device registered and tested

---

## Next Steps

1. **Configure ESP32 WiFi:**
   - Edit `firmware/src/config/config.cpp`
   - Add your WiFi network credentials

2. **Register First Device:**
   - Use admin API to register device
   - Get authentication token

3. **Update Firmware:**
   - Add device ID and token to config
   - Rebuild and upload firmware

4. **Test First Capture:**
   - Trigger ESP32 camera
   - Verify image upload
   - Check inventory update

5. **Production Monitoring:**
   - Monitor Flower for job processing
   - Check logs for errors
   - Verify inventory accuracy

---

## Support & Troubleshooting

### Common Issues

**Issue:** Device not connecting  
**Solution:** Check WiFi credentials, verify device token, check API endpoint

**Issue:** Images not processing  
**Solution:** Check Celery worker logs, verify Gemini API key, check worker status

**Issue:** Database connection errors  
**Solution:** Verify PostgreSQL is running, check credentials in .env.docker

### Logs Location
```bash
# Application logs
docker compose logs backend

# Worker logs
docker compose logs celery_worker

# Database logs
docker compose logs db
```

### Emergency Restart
```bash
docker compose restart
```

---

## Version History

### v1.0.0 - Production Release (2026-01-19)
- Initial production deployment
- All core features implemented
- Multi-provider vision support (OpenAI/Gemini)
- ESP32 firmware ready
- Web UI dashboard complete
- Docker containerized deployment
- Production security hardening

---

**System is LIVE and ready for ESP32 device connections!** 🎉
