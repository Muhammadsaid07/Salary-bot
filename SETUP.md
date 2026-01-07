# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Get Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 3: Set Up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "telegram-bot-service")
   - Click "Create and Continue"
   - Skip role assignment, click "Done"
5. Create Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON" format
   - Download the file
   - Rename it to `credentials.json` and place it in the project folder
6. Share Your Sheet:
   - Open your Google Sheet
   - Click "Share" button
   - Add the service account email (found in `credentials.json`, looks like `xxx@xxx.iam.gserviceaccount.com`)
   - Give it "Viewer" permission (read-only)
   - Click "Send"

## Step 4: Configure the Bot

1. **Set Bot Token:**
   - Create a `.env` file in the project root:
     ```
     BOT_TOKEN=your_bot_token_here
     ```

2. **Update `config.py`:**
   - Change `ADMIN_PASSWORD` to a secure password
   - Set `SPREADSHEET_ID` (found in your Google Sheet URL)
   - Adjust `SHEET_NAME` if your sheet tab has a different name
   - Verify `COLUMN_MAPPING` matches your sheet structure

## Step 5: Prepare Your Google Sheet

Your sheet should have this structure (starting from row 1):

| Name | Salary    | Advance   | Bonus | Penalty | Cover Minus | Cover Plus | TAX     | Remains  |
|------|-----------|-----------|-------|---------|-------------|------------|---------|----------|
| Max  | 11,107,427| 11,571,461| 0     | 130,000 | 0           | 0          | 198,000 | -792,034 |

**Important:** 
- First row can be headers
- Teacher names should be in the first column (Column A)
- Names are matched case-insensitively

## Step 6: Run the Bot

```bash
python bot.py
```

The bot should start and you'll see: `Bot started!`

## Step 7: Test the Bot

1. Open Telegram and find your bot
2. Send `/start`
3. Test admin login with your password
4. Create a test teacher account
5. Test teacher login with the generated access code

## Troubleshooting

### "BOT_TOKEN environment variable is not set!"
- Make sure you created a `.env` file with `BOT_TOKEN=your_token`
- Or export it: `export BOT_TOKEN=your_token` (Linux/Mac) or `set BOT_TOKEN=your_token` (Windows)

### "Credentials file not found"
- Make sure `credentials.json` is in the project root folder
- Check the filename matches `GOOGLE_SHEETS_CREDENTIALS_FILE` in `config.py`

### "Error reading from Google Sheets"
- Verify the service account email has access to your sheet
- Check that `SPREADSHEET_ID` is correct
- Ensure Google Sheets API is enabled

### "Teacher not found"
- Verify the teacher name in the database matches exactly (case-insensitive) with the name in Google Sheets
- Check that the sheet has data in the expected format
- Verify column mapping in `config.py`

## Next Steps

- Change admin password in `config.py`
- Create teacher accounts via admin menu
- Share access codes with teachers securely

