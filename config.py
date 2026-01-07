"""
Configuration file for the Telegram Bot
"""
import os

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123" 

# Google Sheets Configuration
# To change the sheet: 
# 1. Open your Google Sheet
# 2. Look at the URL: .../d/SPREADSHEET_ID/edit#gid=SHEET_GID
SPREADSHEET_ID = "1ONPOESz0sbB8Wmbk3HfuurC0RlrpqXaQU2Pe7Pt3LAQ"
SHEET_GID = "1353280152" # <--- Change this for new tabs (e.g., February)

# Column mapping (A=0, B=1, C=2, etc.)
# If you add columns to your sheet, update these numbers!
# config.py
# config.py
COLUMN_MAPPING = {
    "name": 0,          # Column A
    "share": 1,         # Column B
    "salary": 2,        # Column C
    "advance": 3,       # Column D
    "bonus": 4,         # Column E
    "penalty": 5,       # Column F
    "cover_minus": 6,   # Column G
    "cover_plus": 7,    # Column H
    "tax": 8,           # Column I
    "remains": 9        # Column J
}

# Security and DB settings
MAX_LOGIN_ATTEMPTS = 5
ACCESS_CODE_LENGTH = 8
DATABASE_FILE = "teachers.db"
BACKUP_DIR = "backups"
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24