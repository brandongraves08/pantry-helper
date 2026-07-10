"""Loki log shipping configuration for Docker containers via Promtail."""
import logging
import os

from app.log_config import setup_logging

# Initialize structured JSON logger for this service
logger = setup_logging("pantry-api")

# Re-export for use by other modules
get_logger = lambda name=None: logging.getLogger(name or "pantry-api")
