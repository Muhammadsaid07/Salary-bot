# English Learning Center Salary Tracker Bot

A Telegram bot that allows teachers to securely check their monthly salary details from Google Sheets, with admin controls to manage teacher accounts.

## Features

### 🔐 Admin Account
- **Predefined credentials** stored in `config.py`
- **Create teacher accounts** with auto-generated unique access codes
- **Delete teacher accounts**
- **Reset teacher access codes**
- **View all teachers** and their access codes
- **Backup database** manually or automatically (periodic backups)

### 👨‍🏫 Teacher Account
- **Login with unique access code** (stored securely in SQLite database)
- **Must enter code every time** - no persistent sessions, ensures security
- **View monthly salary** fetched from Google Sheets
- **5-attempt login limit** - account gets blocked after 5 failed attempts
- **Secure access** - teachers can only see their own salary data
- **User-friendly error messages** - clear guidance when issues occur

### 📊 Google Sheets Integration
- **Read-only access** via Google Sheets API (no writing or deleting)
- **Automatic mapping** of teacher names to rows
- **Configurable column mapping** in `config.py` - easy to adjust for sheet changes
- **Robust error handling** - retries on temporary failures, graceful handling of API downtime
- **Clear error messages** - user-friendly notifications when connection issues occur

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))
- Google Cloud Project with Sheets API enabled
- Service Account JSON key file for Google Sheets API

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Sheets API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create a Service Account:
     - Go to "IAM & Admin" → "Service Accounts"
     - Click "Create Service Account"
     - Give it a name and create
     - Click on the service account → "Keys" → "Add Key" → "Create new key" → JSON
     - Download the JSON file and save it as `credentials.json` in the project root
   - Share your Google Sheet with the service account email (found in the JSON file)
   - Make sure the sheet is shared with "Viewer" permissions (read-only)

4. **Configure the bot:**
   - Open `config.py` and update:
     - `ADMIN_USERNAME` and `ADMIN_PASSWORD` (change the password!)
     - `GOOGLE_SHEETS_CREDENTIALS_FILE` (default: "credentials.json")
     - `SPREADSHEET_ID` (found in your Google Sheet URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`)
     - `SHEET_NAME` (default: "Sheet1")
     - `COLUMN_MAPPING` (adjust based on your sheet structure)

5. **Set up environment variables:**
   - Create a `.env` file in the project root:
     ```
     BOT_TOKEN=your_telegram_bot_token_here
     ```
   - Or export it in your terminal:
     ```bash
     export BOT_TOKEN=your_telegram_bot_token_here
     ```

## Google Sheets Format

Your Google Sheet should have the following columns (in order):
- Column A: Teacher Name
- Column B: Salary
- Column C: Advance
- Column D: Bonus
- Column E: Penalty
- Column F: Cover Minus
- Column G: Cover Plus
- Column H: TAX
- Column I: Remains

**Note:** You can adjust the column mapping in `config.py` if your sheet has a different structure.

Example sheet structure:
```
| Name | Salary    | Advance   | Bonus | Penalty | Cover Minus | Cover Plus | TAX     | Remains  |
|------|-----------|-----------|-------|---------|-------------|------------|---------|----------|
| Max  | 11,107,427| 11,571,461| 0     | 130,000 | 0           | 0          | 198,000 | -792,034 |
```

## Running the Bot

```bash
python bot.py
```

The bot will start polling for updates. Keep the terminal open while the bot is running.

## Usage

### For Admins

1. Start the bot with `/start`
2. Click "Admin Login"
3. Enter the admin password (set in `config.py`)
4. Use the admin menu to:
   - **Create Teacher Account**: Enter teacher name, bot generates access code
   - **Delete Teacher Account**: Remove a teacher from the system
   - **Reset Access Code**: Generate a new access code for a teacher
   - **List All Teachers**: View all teachers and their access codes
   - **Backup Database**: Create a manual backup of the database

### For Teachers

1. Start the bot with `/start`
2. Click "Teacher Login"
3. Enter your access code (provided by admin)
4. Click "My Salary This Month" to view your salary details
5. Use "Logout" when done

**Important:** 
- You must enter your access code every time you use the bot (no persistent sessions)
- You have 5 attempts to enter the correct access code per login session
- After 5 failed attempts, your account will be blocked
- Contact admin to reset your access code if blocked
- Error messages will guide you if something goes wrong

## Configuration

### Admin Credentials

Edit `config.py`:
```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_secure_password_here"  # Change this!
```

### Google Sheets Column Mapping

If your sheet has a different structure, update `COLUMN_MAPPING` in `config.py`:
```python
COLUMN_MAPPING = {
    "name": 0,          # Column A (0-indexed)
    "salary": 1,        # Column B
    "advance": 2,       # Column C
    # ... etc
}
```

### Security Settings

```python
MAX_LOGIN_ATTEMPTS = 5        # Maximum failed login attempts
ACCESS_CODE_LENGTH = 8        # Length of generated access codes
```

### Backup Settings

```python
BACKUP_DIR = "backups"                    # Directory to store backups
BACKUP_ENABLED = True                     # Enable automatic backups
BACKUP_INTERVAL_HOURS = 24                # Backup every 24 hours (0 to disable)
```

## Database

The bot uses SQLite to store teacher accounts and access codes. The database file (`teachers.db`) is created automatically on first run. **All data is stored persistently** - bot restarts do not delete teacher accounts.

**Database Schema:**
- `teachers` table:
  - `id`: Primary key
  - `name`: Teacher name (unique)
  - `access_code`: Unique access code
  - `failed_attempts`: Number of failed login attempts
  - `is_blocked`: Whether account is blocked (0 or 1)
  - `created_at`: Timestamp

**Backup System:**
- Automatic periodic backups (configurable interval)
- Manual backup via admin menu
- Keeps last 10 backups automatically
- Backups stored in `backups/` directory

## Security Features

- ✅ Admin credentials stored in code (change password in `config.py`)
- ✅ Teacher access codes stored securely in SQLite database (not in Google Sheets)
- ✅ Teachers must enter access code every time - no persistent sessions
- ✅ 5-attempt login limit with automatic blocking
- ✅ Read-only Google Sheets access (no writing or deleting)
- ✅ Teachers can only access their own data
- ✅ Input validation to prevent errors
- ✅ Persistent data storage - bot restarts don't delete teacher accounts
- ✅ Automatic database backups (configurable)

## Troubleshooting

### Bot doesn't start
- Check that `BOT_TOKEN` is set correctly
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Google Sheets errors
- Verify `credentials.json` file exists and is valid
- Check that the service account email has access to the sheet
- Verify `SPREADSHEET_ID` and `SHEET_NAME` are correct
- Ensure Google Sheets API is enabled in your Google Cloud project

### Teacher not found in sheet
- Verify teacher name in database matches exactly (case-insensitive) with name in Google Sheet
- Check column mapping in `config.py`
- Ensure the sheet has data in the expected format

### Access code issues
- Use admin menu to reset access code
- Verify teacher exists in database (use "List All Teachers")

## File Structure

```
admin_teacher_important_bot/
├── bot.py                 # Main bot file
├── database.py            # SQLite database handler with backup functionality
├── sheets_handler.py      # Google Sheets API integration with error handling
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── SETUP.md               # Quick setup guide
├── credentials.json       # Google Sheets API credentials (not in repo)
├── .env                   # Bot token (not in repo)
├── teachers.db            # SQLite database (created automatically)
└── backups/               # Database backups directory (created automatically)
```

## License

This project is provided as-is for the English Learning Center.

## Support

For issues or questions, contact the system administrator.

