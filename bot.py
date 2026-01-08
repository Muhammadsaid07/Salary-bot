"""
Main Telegram Bot for English Learning Center Salary Tracker
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from database import Database
from sheets_handler import SheetsHandler
import config
from flask import Flask
import threading
from telegram.request import HTTPXRequest
# -------------------- FLASK KEEP-ALIVE (RENDER FIX) --------------------

app = Flask(__name__)

@app.route("/")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()


load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_ROLE = 0
WAITING_FOR_ADMIN_PASSWORD = 1
WAITING_FOR_TEACHER_CODE = 2
ADMIN_MENU = 3
TEACHER_MENU = 4
CREATE_TEACHER_NAME = 5
DELETE_TEACHER_NAME = 6
RESET_CODE_NAME = 7

# Initialize database and sheets handler
db = Database()
sheets_handler = None

# User states (tracking login attempts and current state)
user_states = {}

def init_sheets_handler():
    """Initialize SheetsHandler"""
    global sheets_handler
    try:
        sheets_handler = SheetsHandler()
        logger.info("SheetsHandler initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize SheetsHandler: {str(e)}")
        logger.warning("Bot will start but salary fetching will be unavailable")
        sheets_handler = None

# -------------------- START & BUTTONS --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("Admin Login", callback_data="admin_login")],
        [InlineKeyboardButton("Teacher Login", callback_data="teacher_login")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # If this is a command /start
    if update.message:
        await update.message.reply_text(
            "Welcome to the English Learning Center Salary Tracker Bot!\n\n"
            "Please select your role:",
            reply_markup=reply_markup
        )
    # If this is called via callback (like logout)
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "Please select your role:",
            reply_markup=reply_markup
        )
    return CHOOSING_ROLE

async def role_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the first button click after /start"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_login":
        await query.edit_message_text("Please enter the admin password:")
        return WAITING_FOR_ADMIN_PASSWORD
    elif query.data == "teacher_login":
        await query.edit_message_text("Please enter your access code:")
        return WAITING_FOR_TEACHER_CODE
    return CHOOSING_ROLE

async def admin_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles buttons pressed while in the ADMIN_MENU state"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "create_teacher":
        await query.edit_message_text("Enter the new teacher's name:")
        return CREATE_TEACHER_NAME
    elif data == "delete_teacher":
        await query.edit_message_text("Enter the teacher's name to delete:")
        return DELETE_TEACHER_NAME
    elif data == "reset_code":
        await query.edit_message_text("Enter the teacher's name to reset code:")
        return RESET_CODE_NAME
    elif data == "list_teachers":
        return await list_all_teachers(update, context)
    elif data == "backup_db":
        return await backup_database(update, context)
    elif data == "admin_logout":
        return await admin_logout(update, context)
    elif data == "admin_menu":
        await show_admin_menu(update, context)
        return ADMIN_MENU
    return ADMIN_MENU

async def teacher_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles buttons pressed while in the TEACHER_MENU state"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "my_salary":

        await get_my_salary(update, context)
        return TEACHER_MENU
    elif data == "teacher_logout":
        return await teacher_logout(update, context)
    elif data == "teacher_menu":
        await show_teacher_menu(update, context)
        return TEACHER_MENU
    return TEACHER_MENU

# -------------------- ADMIN HANDLERS --------------------

async def handle_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    password = update.message.text.strip()

    if password == config.ADMIN_PASSWORD:
        user_states[user_id] = {"role": "admin"}
        await update.message.reply_text("✅ Admin access granted!")
        await show_admin_menu(update, context, from_message=True)
        return ADMIN_MENU
    else:
        await update.message.reply_text("❌ Incorrect password. Try again or /cancel.")
        return WAITING_FOR_ADMIN_PASSWORD

async def handle_create_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states or user_states[user_id].get("role") != "admin":
        return ConversationHandler.END

    teacher_name = update.message.text.strip()
    access_code = db.create_teacher(teacher_name)
    await update.message.reply_text(
        f"✅ Teacher account created!\n\nName: {teacher_name}\nAccess Code: {access_code}"
    )
    await show_admin_menu(update, context, from_message=True)
    return ADMIN_MENU

async def handle_delete_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    teacher_name = update.message.text.strip()
    if db.delete_teacher(teacher_name):
        await update.message.reply_text(f"✅ Teacher '{teacher_name}' deleted.")
    else:
        await update.message.reply_text(f"❌ Teacher '{teacher_name}' not found.")
    await show_admin_menu(update, context, from_message=True)
    return ADMIN_MENU

async def handle_reset_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teacher_name = update.message.text.strip()
    new_code = db.reset_access_code(teacher_name)
    if new_code:
        await update.message.reply_text(f"✅ Code reset for {teacher_name}: {new_code}")
    else:
        await update.message.reply_text(f"❌ Teacher '{teacher_name}' not found.")
    await show_admin_menu(update, context, from_message=True)
    return ADMIN_MENU

async def list_all_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teachers = db.get_all_teachers()
    message = "📋 All Teachers:\n\n" + "\n".join([f"{n}: {c}" for n, c in teachers]) if teachers else "No teachers found."
    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="admin_menu")]]
    await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_MENU

async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    backup_path = db.create_backup()
    message = f"✅ Backup created: {os.path.basename(backup_path)}" if backup_path else "❌ Backup failed."
    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="admin_menu")]]
    await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_MENU

# -------------------- TEACHER HANDLERS --------------------

# -------------------- TEACHER HANDLERS --------------------

async def handle_teacher_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    access_code = update.message.text.strip().upper()

    if user_id not in user_states:
        user_states[user_id] = {"attempts": 0}

    attempts = user_states[user_id].get("attempts", 0)
    teacher_info = db.get_teacher_by_code(access_code)

    if teacher_info:
        # 1. Save teacher info
        teacher_id, teacher_name = teacher_info
        user_states[user_id] = {"role": "teacher", "teacher_name": teacher_name}
        
        # 2. Skip the menu and show salary IMMEDIATELY
        await update.message.reply_text(f"✅ Code accepted! Fetching details for {teacher_name}...")
        
        # We call get_my_salary and tell it we are coming from a message login
        return await get_my_salary(update, context, from_login=True)
    else:
        attempts += 1
        user_states[user_id]["attempts"] = attempts
        remaining = config.MAX_LOGIN_ATTEMPTS - attempts
        if remaining <= 0:
            await update.message.reply_text("❌ Too many attempts. Locked.")
            return ConversationHandler.END
        await update.message.reply_text(f"❌ Incorrect code. {remaining} left.")
        return WAITING_FOR_TEACHER_CODE

async def get_my_salary(update: Update, context: ContextTypes.DEFAULT_TYPE, from_login=False):
    user_id = update.effective_user.id
    teacher_name = user_states[user_id].get("teacher_name")
    
    if not teacher_name:
        await update.message.reply_text("❌ Session expired. Please /start again.")
        return ConversationHandler.END

    if not sheets_handler:
        msg = "❌ Salary service unavailable."
        if from_login: await update.message.reply_text(msg)
        else: await update.callback_query.edit_message_text(msg)
        return TEACHER_MENU

    try:
        salary_data = sheets_handler.find_teacher_row(teacher_name)
        
        if salary_data:
            message_text = sheets_handler.format_salary_message(salary_data)
            
            # Buttons to Refresh data or Logout
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh Data", callback_data="my_salary")],
                [InlineKeyboardButton("🚪 Logout", callback_data="teacher_logout")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            full_text = f"💰 **Your Salary Details:**\n\n{message_text}"
            
            if from_login:
                # If they just entered their code, send a NEW message
                await update.message.reply_text(full_text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # If they clicked "Refresh", EDIT the existing message
                try:
                    await update.callback_query.edit_message_text(full_text, reply_markup=reply_markup, parse_mode='Markdown')
                except Exception as e:
                    if "Message is not modified" in str(e):
                        await update.callback_query.answer("Already up to date!")
                    else:
                        raise e
        else:
            error_msg = f"❌ Data for '{teacher_name}' not found in the sheet."
            if from_login: await update.message.reply_text(error_msg)
            else: await update.callback_query.edit_message_text(error_msg)
            
    except Exception as e:
        logger.error(f"Error in get_my_salary: {e}")
        
    return TEACHER_MENU

    try:
        salary_data = sheets_handler.find_teacher_row(teacher_name)
        
        if salary_data:
            message = sheets_handler.format_salary_message(salary_data)
            keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="teacher_menu")]]
            
            # THE FIX: Wrap the edit in a try block
            try:
                await update.callback_query.edit_message_text(
                    f"💰 **Your Salary Details:**\n\n{message}", 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            except Exception as e:
                # If the error is about "Message is not modified", just ignore it
                if "Message is not modified" in str(e):
                    await update.callback_query.answer("Data is already up to date!")
                else:
                    raise e
        else:
            await update.callback_query.edit_message_text(
                f"❌ Data for '{teacher_name}' not found in the current sheet tab."
            )
    except Exception as e:
        # Check if the query was already answered to avoid crash
        print(f"Error in get_my_salary: {e}")

# -------------------- OTHER --------------------

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message=False):
    keyboard = [
        [InlineKeyboardButton("Create Teacher", callback_data="create_teacher")],
        [InlineKeyboardButton("Delete Teacher", callback_data="delete_teacher")],
        [InlineKeyboardButton("Reset Code", callback_data="reset_code")],
        [InlineKeyboardButton("List Teachers", callback_data="list_teachers")],
        [InlineKeyboardButton("Backup DB", callback_data="backup_db")],
        [InlineKeyboardButton("Logout", callback_data="admin_logout")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "🔐 Admin Menu:"
    if from_message: await update.message.reply_text(text, reply_markup=markup)
    else: await update.callback_query.edit_message_text(text, reply_markup=markup)

async def show_teacher_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message=False):
    keyboard = [
        [InlineKeyboardButton("My Salary", callback_data="my_salary")],
        [InlineKeyboardButton("Logout", callback_data="teacher_logout")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "💼 Teacher Menu:"
    if from_message: await update.message.reply_text(text, reply_markup=markup)
    else: await update.callback_query.edit_message_text(text, reply_markup=markup)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states: del user_states[user_id]
    await update.message.reply_text("Cancelled. /start to restart.")
    return ConversationHandler.END

async def admin_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states: del user_states[user_id]
    return await start(update, context)

async def teacher_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states: del user_states[user_id]
    return await start(update, context)

async def periodic_backup(context: ContextTypes.DEFAULT_TYPE):
    if config.BACKUP_ENABLED: db.create_backup()

# -------------------- MAIN --------------------

def main():
    init_sheets_handler()

    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )

    application = (
        Application.builder()
        .token(os.getenv("BOT_TOKEN"))
        .request(request)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(role_selection_callback)],
            WAITING_FOR_ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_password)],
            WAITING_FOR_TEACHER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_teacher_code)],
            ADMIN_MENU: [CallbackQueryHandler(admin_button_callback)],
            TEACHER_MENU: [CallbackQueryHandler(teacher_button_callback)],
            CREATE_TEACHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_teacher)],
            DELETE_TEACHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_teacher)],
            RESET_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reset_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)

    if config.BACKUP_ENABLED:
        application.job_queue.run_repeating(
            periodic_backup,
            interval=config.BACKUP_INTERVAL_HOURS * 3600,
            first=10
        )

    application.run_polling()


if __name__ == "__main__":
    main()