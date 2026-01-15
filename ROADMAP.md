# Pantry Inventory - Remaining Work & Roadmap

## High Priority (Core Functionality)

### Backend
- [ ] **Implement OpenAI Vision Analysis** 
  - File: `backend/app/services/vision.py`
  - Status: Skeleton exists, needs real implementation
  - Tasks:
    - Call OpenAI Vision API with image
    - Parse JSON response
    - Handle errors gracefully
    - Add retry logic for API failures

- [ ] **Background Job Queue for Image Analysis**
  - Add task queue (Celery + Redis or RQ)
  - Process captures asynchronously
  - Track analysis status
  - Handle failed analyses

- [ ] **Device Token Validation Middleware**
  - Validate token on all endpoints that need auth
  - Current: Only ingest validates
  - Needed: Protect sensitive endpoints if added

### Firmware (ESP32)
- [ ] **Camera Module Implementation**
  - File: `firmware/src/camera/camera.cpp`
  - Capture JPEG images from OV2640
  - Handle exposure settings
  - Manage memory for large images

- [ ] **WiFi and HTTPS Upload**
  - File: `firmware/src/upload/upload.cpp`
  - Build multipart/form-data request
  - Handle certificate validation
  - Implement retry logic
  - Handle timeouts gracefully

- [ ] **Power Management**
  - File: `firmware/src/power/power.cpp`
  - Implement deep sleep cycles
  - Configure GPIO wakeup sources
  - Monitor battery voltage
  - Measure wake duration

- [ ] **Sensor Integration**
  - File: `firmware/src/sensors/sensors.cpp`
  - Debounce reed switch (door)
  - Debounce light sensor
  - Ignore repeated triggers (quiet period)

## Medium Priority (Polish & Features)

### Backend
- [ ] **Image Retention Policy**
  - Auto-delete images older than X days
  - Keep observation data longer than images
  - Implement retention configuration

- [ ] **Confidence Tuning**
  - Adjust OpenAI prompt for better results
  - Tune confidence thresholds per category
  - A/B test different prompts

- [ ] **Inventory History Queries**
  - Advanced filtering by date range
  - Filter by event type
  - Export to CSV/JSON

- [ ] **Device Management API**
  - List all devices
  - Update device settings
  - View device health metrics
  - Deregister devices

- [ ] **Better Error Logging**
  - Structured logging to file
  - Error tracking (Sentry integration)
  - Performance monitoring

### Web UI
- [ ] **User Authentication**
  - Login/logout
  - User roles (admin, viewer)
  - Secure token storage

- [ ] **Advanced Features**
  - Real-time updates (WebSocket)
  - Search and filtering
  - Analytics dashboard
  - Export functionality

- [ ] **Dark Mode**
  - Theme toggle
  - Persistent user preference

- [ ] **Mobile Responsiveness**
  - Current: Partially responsive
  - Mobile-optimized layouts
  - Touch-friendly controls

## Low Priority (Nice to Have)

- [ ] **Docker Containerization**
  - Dockerfile for backend
  - Docker Compose for full stack
  - CI/CD pipeline (GitHub Actions)

- [ ] **Barcode Scanning**
  - Add barcode detection to vision
  - Link barcodes to canonical items
  - Improve item identification

- [ ] **Multi-Device Sync**
  - Merge observations from multiple cameras
  - Conflict resolution
  - Distributed inventory tracking

- [ ] **Push Notifications**
  - Alert when low on staples
  - Notify when expiry date approaches
  - Email/SMS/mobile notifications

- [ ] **OCR for Labels**
  - Extract text from packages
  - Parse expiration dates
  - Extract nutritional info

- [ ] **Machine Learning Model**
  - Train custom model for pantry items
  - Fine-tune for local lighting
  - Improve accuracy over time

## Testing & Quality Assurance

- [ ] **Backend Test Coverage**
  - Current: Basic tests for routes
  - Needed: Service layer tests
  - Mock OpenAI API in tests
  - Integration tests with real DB

- [ ] **Frontend Tests**
  - Component tests (React Testing Library)
  - Integration tests
  - E2E tests (Cypress/Playwright)

- [ ] **Firmware Tests**
  - Unit tests for sensor logic
  - Mock WiFi for upload tests
  - Power consumption profiling

- [ ] **Performance Testing**
  - Load test API endpoints
  - Firmware battery drain testing
  - Image upload performance
  - Database query optimization

## Documentation

- [ ] **API Documentation**
  - Generate from OpenAPI/Swagger
  - Add more endpoint examples
  - Document error codes

- [ ] **Firmware Documentation**
  - Hardware setup guide
  - Pin configuration guide
  - Compilation instructions for different boards

- [ ] **User Guide**
  - How to set up ESP32
  - How to use web UI
  - Troubleshooting guide

- [ ] **Architecture Deep Dives**
  - Database schema rationale
  - Vision analysis pipeline
  - Authentication flow

## Deployment & DevOps

- [ ] **Production Database Setup**
  - PostgreSQL schema creation
  - Connection pooling
  - Backup strategy

- [ ] **Hosting**
  - Choose cloud provider (AWS/GCP/Azure)
  - Set up deployment
  - Configure domain name
  - SSL/TLS certificates

- [ ] **Monitoring & Alerts**
  - Application health checks
  - Error rate monitoring
  - Performance monitoring
  - Alert configuration

- [ ] **Secrets Management**
  - Secure OpenAI API key storage
  - Device token security
  - Database password management

## Future Enhancements

- [ ] **Mobile App**
  - React Native version
  - Push notifications
  - Offline support

- [ ] **Smart Home Integration**
  - IFTTT support
  - Alexa skills
  - Home Assistant integration

- [ ] **Computer Vision Improvements**
  - Multi-angle capture strategy
  - 3D reconstruction
  - Weight estimation

- [ ] **Expiration Tracking**
  - OCR for expiry dates
  - Alerts for items nearing expiry
  - Usage tracking

## Known Issues to Fix

- [ ] Vision service returns placeholder data
- [ ] No background job processor
- [ ] Firmware is all stubs
- [ ] Web UI has hardcoded colors
- [ ] No CORS configuration for production
- [ ] No rate limiting on endpoints
- [ ] Database migrations need real schema testing

## Quick Wins (< 1 hour each)

- [ ] Add more test cases to backend
- [ ] Implement `get_image_size()` in firmware
- [ ] Add confidence badges to web inventory table
- [ ] Create Docker Compose file
- [ ] Add `.env.production.example`
- [ ] Create GitHub issue templates
- [ ] Add pre-commit hooks for linting

## Blocked/Waiting

- [ ] Real ESP32 hardware (for firmware development)
- [ ] OpenAI API access verification
- [ ] Production database provisioning

## Priority Queue (Suggested Order)

### Week 1
1. Implement OpenAI Vision service
2. Add background job queue
3. Create more comprehensive tests
4. Set up CI/CD pipeline

### Week 2
1. Complete firmware camera module
2. Implement WiFi upload
3. Test end-to-end with real images
4. Performance optimization

### Week 3
1. Deploy to production
2. Add user authentication
3. Enhance web UI
4. Set up monitoring

### Week 4+
1. Mobile app
2. Advanced features
3. Community contributions
4. Scale and optimize

---

## How to Contribute

1. Pick an item from this list
2. Create a GitHub issue
3. Fork and create a feature branch
4. Implement with tests
5. Create a pull request
6. Get review from maintainers
7. Merge and celebrate! 🎉

## Metrics to Track

- Test coverage percentage
- API response times
- ESP32 power consumption
- Image upload success rate
- Vision API accuracy (false positives/negatives)
- Database query performance

---

**Last Updated**: January 13, 2026  
**Project Status**: Foundation Complete, Ready for Implementation
