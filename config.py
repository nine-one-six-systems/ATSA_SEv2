import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DATABASE_PATH = BASE_DIR / 'database.db'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# File upload configuration
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# OCR Configuration
TESSERACT_CMD = os.environ.get('TESSERACT_CMD', None)  # Path to tesseract executable if needed

