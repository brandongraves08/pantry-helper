# Pantry Inventory Documentation Index

Welcome! This file helps you navigate all documentation for the Pantry Inventory project.

## 📚 Documentation Files

### Getting Started
- **[README.md](README.md)** - Project overview and quick start guide
  - Installation steps
  - Running the services
  - API endpoint examples
  - Troubleshooting

- **[GETTING_STARTED_PHASE_2.md](GETTING_STARTED_PHASE_2.md)** - ⭐ NEW: Complete guide to Phase 2 features
  - Setup and configuration
  - Using the image analysis system
  - Running tests
  - Common tasks and troubleshooting
  - Example curl commands
  - Production next steps

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Cheat sheet with essential commands
  - Most used commands
  - API curl examples
  - Key file locations
  - Quick troubleshooting

- **[BUILD_SUMMARY.md](BUILD_SUMMARY.md)** - What's been built in this session
  - Complete list of deliverables
  - Architecture highlights
  - Code statistics
  - Next recommended steps

### Phase 2 Implementation Details
- **[PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)** - ⭐ NEW: Summary of Phase 2 work
  - What was built and why
  - API reference for new endpoints
  - Testing steps
  - Performance notes
  - Security considerations

- **[IMPLEMENTATION_PHASE_2.md](IMPLEMENTATION_PHASE_2.md)** - ⭐ NEW: Technical deep dive
  - Complete implementation details
  - Architecture diagrams
  - Error handling strategies
  - Configuration guide
  - Usage examples
  - Future enhancements

### Understanding the System
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system design (existing)
  - Components overview
  - Data flow diagrams (conceptual)
  - Database schema
  - Security model
  - Design decisions

### Development
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Developer workflows and debugging
  - Development environment setup
  - Running services individually
  - Testing strategies
  - Debugging techniques
  - Common development tasks
  - Code organization patterns

- **[ROADMAP.md](ROADMAP.md)** - What still needs to be done
  - High priority tasks
  - Medium/low priority features
  - Testing & QA checklist
  - Deployment requirements
  - Known issues
  - Suggested implementation order

### Copilot/AI
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Guidelines for AI agents
  - Project context
  - Key architectural patterns
  - Where to find things
  - Common workflows

## 🗂️ Project Structure at a Glance

```
pantry-helper/
├── backend/                    # Python FastAPI API
│   ├── app/                    # Main application code
│   ├── tests/                  # Test suite
│   ├── scripts/                # Utilities (seed, auth)
│   └── migrations/             # Database migrations
├── firmware/                   # ESP32 C++ firmware
│   └── src/                    # Source code (modular)
├── web/                        # React web UI
│   └── src/                    # React components and styles
├── Makefile                    # Build automation
├── README.md                   # You are here!
├── QUICK_REFERENCE.md         # Command cheat sheet
├── BUILD_SUMMARY.md           # What was just built
└── ROADMAP.md                 # What's next
```

## 🚀 Quick Start

1. **New to project?** → Start with [README.md](README.md)
2. **Want to understand it?** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Ready to code?** → Go to [DEVELOPMENT.md](DEVELOPMENT.md)
4. **Need commands?** → Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
5. **Looking for tasks?** → See [ROADMAP.md](ROADMAP.md)

## 📋 Essential Commands

```bash
# Setup
make all                        # Install everything
make backend-seed              # Initialize database

# Development (open 2 terminals)
make backend-run               # Terminal 1: API at localhost:8000
make web-dev                   # Terminal 2: UI at localhost:5173

# Testing
make backend-test              # Run tests

# Firmware
make firmware-build            # Compile for ESP32
make firmware-upload           # Upload to device
```

## 🎯 Key Concepts

### Device Authentication
- ESP32 devices are identified by `device_id` and `token`
- Tokens are hashed with SHA256 in the database
- See [backend/app/auth.py](backend/app/auth.py)

### Data Flow
1. ESP32 captures image → 2. Sends to `/v1/ingest` → 3. Backend stores → 4. OpenAI Vision analyzes → 5. Inventory updates → 6. Web UI reflects changes

### Database
- **SQLite** for development (automatic)
- **PostgreSQL** for production
- Managed with Alembic migrations
- See [backend/app/db/models.py](backend/app/db/models.py)

## 📁 Important Files

### Backend
- `backend/app/main.py` - FastAPI app setup
- `backend/app/api/routes/` - API endpoints
- `backend/app/services/` - Business logic
- `backend/app/db/models.py` - Database schema
- `backend/app/auth.py` - Token authentication
- `backend/scripts/seed_db.py` - Database seeding

### Frontend
- `web/src/App.jsx` - Main React component
- `web/src/components/` - Reusable components
- `web/src/api.js` - API client

### Firmware
- `firmware/src/main.cpp` - Event loop
- `firmware/src/*/` - Modular subsystems (power, sensors, camera, net, upload, config)

## 🔧 Configuration Files

- `backend/.env` - Backend environment variables
- `backend/.env.example` - Template (copy and edit)
- `firmware/src/config/config.cpp` - Device WiFi settings
- `web/src/api.js` - Web UI API endpoint

## 📖 How to Read This Documentation

### For Quick Help
1. Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
2. Use API docs at http://localhost:8000/docs (when running)

### For Understanding
1. Start with [README.md](README.md) - what is it?
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) - how does it work?
3. Study test files - see usage examples

### For Development
1. Check [DEVELOPMENT.md](DEVELOPMENT.md) - workflows
2. Look at similar files for patterns
3. Run tests to verify changes

### For Planning Work
1. Read [ROADMAP.md](ROADMAP.md) - what's next?
2. Pick a task that interests you
3. Check related documentation

## 🐛 Debugging Resources

### Backend Issues
- Enable `LOG_LEVEL=DEBUG` in `backend/.env`
- Check [DEVELOPMENT.md - Backend Debugging](DEVELOPMENT.md#backend-debugging)
- View API docs at http://localhost:8000/docs

### Frontend Issues
- Open browser DevTools (F12)
- Check Network tab for API calls
- Check Console for JavaScript errors
- See [DEVELOPMENT.md - Web UI Debugging](DEVELOPMENT.md#web-ui-debugging)

### Firmware Issues
- Use `make firmware-monitor` for serial output
- Check [DEVELOPMENT.md - Firmware Debugging](DEVELOPMENT.md#firmware-debugging)
- Review `firmware/src/main.cpp` and subsystem modules

## 🧪 Testing

### Run Tests
```bash
make backend-test
```

### View Test Files for Examples
- `backend/tests/test_health.py` - Simple test
- `backend/tests/test_ingest.py` - Complex test with fixtures
- `backend/tests/test_inventory.py` - Database interaction

See [DEVELOPMENT.md - Testing](DEVELOPMENT.md#testing) for more details.

## 📊 Code Statistics

- **Backend**: ~1500 lines of Python
- **Frontend**: ~300 lines of React/JSX
- **Firmware**: ~400 lines of C++ stubs
- **Tests**: ~150 lines
- **Documentation**: ~5000 lines

## 🎓 Learning Path

1. **Hour 1**: Read README.md + QUICK_REFERENCE.md
2. **Hour 2**: Run `make all` and `make backend-seed`, start services
3. **Hour 3**: Test endpoints with curl, explore web UI
4. **Hour 4**: Read ARCHITECTURE.md for system design
5. **Hour 5**: Read DEVELOPMENT.md for coding patterns
6. **Hour 6+**: Start implementing from ROADMAP.md

## ❓ Common Questions

**Q: Where do I start?**  
A: Read [README.md](README.md), then run `make all` and start services.

**Q: How do I understand the system?**  
A: Read [ARCHITECTURE.md](ARCHITECTURE.md) for design overview.

**Q: How do I write code?**  
A: Follow patterns in [DEVELOPMENT.md](DEVELOPMENT.md) and existing code.

**Q: What should I work on?**  
A: Check [ROADMAP.md](ROADMAP.md) for prioritized tasks.

**Q: How do I test my changes?**  
A: Use `make backend-test` and check API with curl.

**Q: How do I debug?**  
A: See "Debugging" section in [DEVELOPMENT.md](DEVELOPMENT.md).

## 🤝 Contributing

1. Pick a task from [ROADMAP.md](ROADMAP.md)
2. Follow patterns in [DEVELOPMENT.md](DEVELOPMENT.md)
3. Write tests for your code
4. Run `make backend-test` to verify
5. Create a pull request

## 📞 Support

For issues:
1. Check [DEVELOPMENT.md](DEVELOPMENT.md) for debugging tips
2. Review [ROADMAP.md](ROADMAP.md) for known issues
3. Check logs with `LOG_LEVEL=DEBUG`

## 📅 Version Info

- Created: January 13, 2026
- Project Status: ✅ Foundation Complete - Ready for Development
- Python 3.9+
- Node.js 16+
- React 18.2+

---

## 🎯 Next Steps

- [ ] Read [README.md](README.md)
- [ ] Run `make all` to install dependencies
- [ ] Run `make backend-seed` to initialize database
- [ ] Start services with `make backend-run` and `make web-dev`
- [ ] Test API at http://localhost:8000/docs
- [ ] Explore web UI at http://localhost:5173
- [ ] Pick a task from [ROADMAP.md](ROADMAP.md)
- [ ] Read [DEVELOPMENT.md](DEVELOPMENT.md) for coding guidelines
- [ ] Start contributing! 🚀

---

**Happy Building!** 🎉

Questions? Check the relevant documentation file above, or look at [DEVELOPMENT.md](DEVELOPMENT.md#troubleshooting-development-issues) for troubleshooting.
