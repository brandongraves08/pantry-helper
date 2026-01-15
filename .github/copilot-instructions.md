# Copilot Instructions for Pantry Inventory Project

## Overview
This document provides essential guidelines for AI coding agents working on the Pantry Inventory project. It covers the architecture, workflows, conventions, and integration points necessary for effective contributions.

## Architecture Overview
The Pantry Inventory system consists of the following major components:
- **ESP32 Camera Node**: Captures images and uploads them to the backend.
- **Backend API**: Handles authentication, image storage, and inventory management.
- **Database**: Stores inventory items, observations, and device telemetry.
- **Web UI**: Provides a user interface for inventory management.

### Data Flow
1. Trigger occurs (door open or light on).
2. ESP32 wakes, captures images, and uploads them to the backend.
3. Backend processes images and updates the inventory.

## Developer Workflows
### Building and Testing
- Use `make build` to compile the project.
- Run tests with `make test` to ensure functionality.

### Debugging
- Utilize logging in the backend to trace API calls and responses.
- ESP32 can be debugged using serial output for real-time feedback.

## Project-Specific Conventions
- **Naming Conventions**: Use camelCase for variables and functions in JavaScript, and snake_case for Python.
- **File Structure**: Follow the recommended repository layout:
  ```
  pantry-inventory/
    ARCHITECTURE.md
    README.md
  ```

## Integration Points
- **OpenAI Vision API**: Ensure proper JSON schema is followed when sending images for analysis.
- **Database**: Use Postgres for structured data storage; ensure migrations are handled correctly.

## External Dependencies
- **ESP32 Libraries**: Include necessary libraries for camera and Wi-Fi functionality.
- **Backend Framework**: Use FastAPI or Node/Express for the backend API.

## Conclusion
These instructions aim to provide a clear understanding of the Pantry Inventory project for AI coding agents. For any unclear sections, please provide feedback for further refinement.