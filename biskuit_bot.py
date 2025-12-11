from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import os
import sys

# --- CONFIGURATION & SECURITY ---

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the token (using the direct token from your provided code for continuity)
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

# --- BOT STATE ---
# Global state variable managed by the /pause and /unpause commands
# We use the bot's context.bot_data dictionary for persistent state during runtime
BOT_STATE_KEY = 'is_active' 

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {
    'AMERICA', 'Canada', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'
}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300  # Must be 300 or more
MAX_HOURS = 12
REQUIRED_FIELDS = ['Location', 'Age', 'Job', 'Working Hours', 'Client Account Link']

NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE',
    'POLICE', 'SOLDIER'
}


# --- HELPER FUNCTION: PARSE AND CHECK ---

def check_client_data(report_text):
    """Parses the client report text and checks against the defined rules, including disallowed jobs."""
    data = {}
    lines = report_text.strip().split('\n')

    # Standardized parsing
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            data[key.strip().title()] = value.strip()

    errors = []

    # 1. Check for missing required fields
    for field in REQUIRED_FIELDS:
        if not data.get(field) or data.get(field) == '':
            errors.append(f"❌ Missing required field: **{field}**")

    if errors and len(errors) == len(REQUIRED_FIELDS):
        return "Can't Cut", '\n'.join(errors)

    # 2. Check Location
    location = data.get('Location', '').upper()
    # Using 'any' for better phrase matching, as implemented in a previous step
    if any(country in location for country in NOT_DEVELOP_COUNTRIES):
        errors.append("❌ Fails Location rule (Not Develop Country).")

    # 3. Check Age
    try:
        age_str = data.get('Age')
        if not age_str:
            raise ValueError("Age field is empty.")
        age = int(age_str)
        if not (MIN_AGE <= age <= MAX_AGE):
            errors.append(f"❌ Fails Age rule (Must be between {MIN_AGE}-{MAX_AGE}).")
    except (ValueError, TypeError):
        errors.append("❌ Invalid or missing Age value.")

    # 4. Check Salary
    salary_str = data.get('Salary', '').strip()

    if not salary_str or salary_str.lower() in ['none', 'n/a', 'not telling', 'unknown']:
        pass
    else:
        try:
            salary = float(salary_str.replace('$', '').replace('€', '').replace('£', '').replace(',', ''))
            
            if salary < MIN_SALARY:
                errors.append(f"❌ Fails Salary rule (Must be ${MIN_SALARY} or more).")
        except (ValueError, TypeError):
            errors.append("❌ Invalid Salary value. Must be a number (>=300) or left empty/Not Telling.")

    # 5. Check Working Hours
    working_hours_str = data.get('Working Hours', '').strip().lower()

    if 'not fixed' in working_hours_str or 'flexible' in working_hours_str:
        pass
    else:
        try:
            working_hours = float(working_hours_str.split(' ')[0])
            if working_hours > MAX_HOURS:
                errors.append(
                    f"❌ Fails Working Hours rule (Must be less than or equal to {MAX_HOURS} hours, or 'Not Fixed').")
        except (ValueError, TypeError):
            errors.append("❌ Invalid Working Hours value. Must be a number (<=12) or 'Not Fixed/Flexible'.")

    # 6. Check Job
    job_input = data.get('Job', '').upper()

    if not job_input or job_input in ['NONE', 'N/A', 'UNKNOWN']:
        errors.append("❌ Fails Job rule (Job must be specified).")
    else:
        is_disallowed = False
        for disallowed_job in NOT_ALLOWED_JOBS:
            if disallowed_job in job_input:
                is_disallowed = True
                break
        
        if is_disallowed:
            errors.append("❌ Fails Job rule (Profession is not allowed to develop, or is a related position).")

    # 7. Check Client Account Link
    link = data.get('Client Account Link')
    if not link or 'http' not in link.lower() and '.' not in link.lower():
        errors.append("❌ Fails Link rule (Social Media Link must be included and look like a link).")

    # 8. Final Result Determination
    if not errors:
        result = "Passed"
        remark = "✅ **All requirements met.** Client can be developed."
    else:
        result = "Can't Cut"
        error_list_text = '- ' + '\n- '.join(errors)
        remark = f"⚠️ Reasons for 'Can't Cut':\n{error_list_text}"

    return result, remark


# --- COMMAND HANDLERS ---

async def start(update: Update, context):
    """Sends a greeting and ensures the bot is set to active."""
    # Set the bot state to active upon starting
    context.bot_data[BOT_STATE_KEY] = True 
    
    await update.message.reply_text(
        'Hello! Client Filter Bot is **ACTIVE**.\n\n'
        'Send me the client report using the required format to begin filtering:\n'
        'Example: Location - USA\nAge - 30\nJob - Engineer\n...'
    , parse_mode='Markdown')

async def pause_command(update: Update, context):
    """Pauses the client filtering message handler."""
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸️ **Bot Paused.** I will no longer process client reports until you run `/unpause`.", parse_mode='Markdown')

async def unpause_command(update: Update, context):
    """Unpauses the client filtering message handler."""
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶️ **Bot Activated.** I am now ready to process client reports.", parse_mode='Markdown')


# --- MAIN MESSAGE HANDLER (UPDATED with State Check) ---

async def client_filter_handler(update: Update, context):
    """Processes the client report text only if the bot is active."""
    # Check if the bot is currently paused
    if not context.bot_data.get(BOT_STATE_KEY, True): 
        # Optional: Send a subtle reminder that the bot is paused
        # await update.message.reply_text("I am currently paused. Use /unpause to restart.")
        return

    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return

    report_text = update.message.text
    
    result, remark = check_client_data(report_text)

    response_message = f"--- CLIENT FILTER RESULT ---\n\n"
    response_message += f"**RESULT:** `{result}`\n\n"
    response_message += f"**Remark:**\n{remark}"

    await update.message.reply_text(response_message, parse_mode='Markdown')


# --- MAIN BOT EXECUTION ---

def main():
    """Start the bot using the modern Application-based structure."""

    logger.info("Initializing Client Filter Bot Application...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Initialize the state to True if it doesn't exist (first run)
    application.bot_data[BOT_STATE_KEY] = True

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    # Note: We need /unpause to resume the bot's function
    application.add_handler(CommandHandler("unpause", unpause_command)) 
    
    # This handler processes all text messages that are NOT commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))

    logger.info("Client Filter Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
