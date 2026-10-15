"""
AttendX - Configuration Module
Centralized application settings, database paths, and upload limits.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'attendx-academic-secret-key-2026')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'data' / 'attendx.db'))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 Megabytes limit
    ALLOWED_EXTENSIONS = {'csv'}
    JSON_SORT_KEYS = False

class TestConfig(Config):
    TESTING = True
    DATABASE_PATH = ':memory:'

