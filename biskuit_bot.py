from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import os # Included for best practice token handling

# --- CONFIGURATION ---
# IMPORTANT: It is safer to load the token from an Environment Variable on the server.
# For now, we use the token directly for testing.
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {
    'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM'
}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300
REQUIRED_FIELDS = ['Location', 'Age', 'Job', 'Salary', 'Client Account Link']


# --- HELPER FUNCTION: PARSE AND CHECK (No change needed here) ---

def check_client_data(report_text):
    """Parses the client report text and checks against the defined rules."""
    data = {}
    lines = report_text.strip().split('\n')
    
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            data[key.strip()] = value.strip()

    errors = []

    for field in REQUIRED_FIELDS:
        if not data.get(field) or data.get(field) == '':
            errors.append(f"❌ Missing required field: {field}")

    if errors:
        return "Can't Cut", '\n'.join(errors)

    location = data.get('Location', '').upper()
    if location in NOT_DEVELOP_COUNTRIES:
        errors.append("❌ Fails Location rule (Not Develop Country).")

    try:
        age = int(data.get('Age'))
        if not (MIN_AGE <= age <= MAX_AGE):
            errors.append(f"❌ Fails Age rule (Must be between {MIN_AGE}-{MAX_AGE}).")
    except (ValueError, TypeError):
        errors.append("❌ Invalid or missing Age value.")

    try:
        salary = float(data.get('Salary').replace('$', '').replace(',', ''))
        if salary <= MIN_SALARY:
            errors.append(f"❌ Fails Salary rule (Must be more than ${MIN_SALARY}).")
    except (ValueError, TypeError):
        errors.append("❌ Invalid or missing Salary value.")

    job = data.get('Job')
    if not job or job.lower() == 'none' or job.lower() == 'n/a':
        errors.append("❌ Fails Job rule (Job must be specified).")

    link = data.get('Client Account Link')
    if not link or 'http' not in link.lower() and '.' not in link.lower():
        errors.append("❌ Fails Link rule (Social Media Link must be included and look like a link).")

    if not errors:
        result = "Passed"
        remark = "✅ All requirements met. Client can be developed."
    else:
        result = "Can't Cut"
        error_list_text = '- ' + '\n- '.join(errors)
        remark = f"⚠️ Reasons for 'Can't Cut':\n{error_list_text}"

    return result, remark


# --- HANDLER FUNCTION (NOW ASYNCHRONOUS) ---

async def client_filter_handler(update: Update, context):
    """The main handler that processes the user's client report text."""
    report_text = update.message.text

    if report_text.startswith('/'):
        return

    result, remark = check_client_data(report_text)

    response_message = f"--- CLIENT FILTER RESULT ---\n\n"
    response_message += f"**RESULT:** `{result}`\n\n"
    response_message += f"**Remark:**\n{remark}"

    # FIX: Must use await
    await update.message.reply_text(response_message, parse_mode='Markdown')


# --- STANDARD COMMAND HANDLERS (NOW ASYNCHRONOUS) ---

async def start(update: Update, context):
    """Sends a greeting when the user issues the /start command."""
    # FIX: Must use await
    await update.message.reply_text(
        'Hello! Send me the client report using your specified format, and I will filter it for you. '
        'Example format:\nLocation - USA\nAge - 30\nJob - Engineer\nSalary - 400\nWorking Hours - 8\nClient Account Link - http://example.com/social\nRemark - '
    )


async def help_command(update: Update, context):
    """Sends a help message."""
    # FIX: Must use await
    await update.message.reply_text(
        'Send me a client report in the specified format to check if they "Passed" or "Can\'t Cut."')


# --- MAIN BOT EXECUTION (Modern PTB Structure) ---

def main():
    """Start the bot using the modern Application-based structure."""
    
    # 1. Create the Application (replaces Updater)
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # This handler processes the report text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))

    # Start the Bot
    print("Client Filter Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
