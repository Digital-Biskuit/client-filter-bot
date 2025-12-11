from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging

# --- CONFIGURATION ---
# Replace 'YOUR_BOT_TOKEN_HERE' with the token you copied from BotFather
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- BOT RULE SET ---
# Countries considered 'Not Develop' based on your rule
NOT_DEVELOP_COUNTRIES = {
    'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM'
}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300
REQUIRED_FIELDS = ['Location', 'Age', 'Job', 'Salary', 'Client Account Link']


# --- HELPER FUNCTION: PARSE AND CHECK ---

def check_client_data(report_text):
    """
    Parses the client report text and checks against the defined rules.
    Returns 'Passed' or 'Can\'t Cut' and a detailed Remark.
    """
    data = {}
    lines = report_text.strip().split('\n')

    # 1. Parse the report into a dictionary
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            data[key.strip()] = value.strip()

    errors = []

    # 2. Check for missing required fields
    for field in REQUIRED_FIELDS:
        if not data.get(field) or data.get(field) == '':
            errors.append(f"❌ Missing required field: {field}")

    # If essential data is missing, stop further detailed checks
    if errors:
        return "Can't Cut", '\n'.join(errors)

    # 3. Check Location (Develop/Not Develop)
    location = data.get('Location', '').upper()
    if location in NOT_DEVELOP_COUNTRIES:
        errors.append("❌ Fails Location rule (Not Develop Country).")

    # 4. Check Age
    try:
        age = int(data.get('Age'))
        if not (MIN_AGE <= age <= MAX_AGE):
            errors.append(f"❌ Fails Age rule (Must be between {MIN_AGE}-{MAX_AGE}).")
    except (ValueError, TypeError):
        errors.append("❌ Invalid or missing Age value.")

    # 5. Check Salary
    try:
        salary = float(data.get('Salary').replace('$', '').replace(',', ''))
        if salary <= MIN_SALARY:
            errors.append(f"❌ Fails Salary rule (Must be more than ${MIN_SALARY}).")
    except (ValueError, TypeError):
        errors.append("❌ Invalid or missing Salary value.")

    # 6. Check Job (must have)
    job = data.get('Job')
    if not job or job.lower() == 'none' or job.lower() == 'n/a':
        errors.append("❌ Fails Job rule (Job must be specified).")

    # 7. Check Client Account Link (must include a link-like format)
    link = data.get('Client Account Link')
    if not link or 'http' not in link.lower() and '.' not in link.lower():
        errors.append("❌ Fails Link rule (Social Media Link must be included and look like a link).")

    # 8. Final Result Determination
    if not errors:
        # All requirements met
        result = "Passed"
        remark = "✅ All requirements met. Client can be developed."
    else:
        # One or more rules failed
        result = "Can't Cut"
        error_list_text = '- ' + '\n- '.join(errors)
        remark = f"⚠️ Reasons for 'Can't Cut':\n{error_list_text}"

    return result, remark


# --- HANDLER FUNCTION (What the Bot does on receiving text) ---

def client_filter_handler(update: Update, context):
    """
    The main handler that processes the user's client report text.
    """
    report_text = update.message.text

    # Ignore messages that are just commands
    if report_text.startswith('/'):
        return

    # Process the report
    result, remark = check_client_data(report_text)

    # Prepare the final response
    response_message = f"--- CLIENT FILTER RESULT ---\n\n"
    response_message += f"**RESULT:** `{result}`\n\n"
    response_message += f"**Remark:**\n{remark}"

    # Send the result back to the user
    update.message.reply_text(response_message, parse_mode='Markdown')


# --- STANDARD COMMAND HANDLERS ---

def start(update: Update, context):
    """Sends a greeting when the user issues the /start command."""
    update.message.reply_text(
        'Hello! Send me the client report using your specified format, and I will filter it for you. '
        'Example format:\nLocation - USA\nAge - 30\nJob - Engineer\nSalary - 400\nWorking Hours - 8\nClient Account Link - http://example.com/social\nRemark - '
    )


def help_command(update: Update, context):
    """Sends a help message."""
    update.message.reply_text(
        'Send me a client report in the specified format to check if they "Passed" or "Can\'t Cut."')


# --- MAIN BOT EXECUTION (Corrected for python-telegram-bot v20+) ---

def main():
    """Start the bot using the modern Application-based structure."""
    
    # 1. Create the Application (replaces Updater)
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # This handler processes the report text
    # Note: Filters.text is now filters.TEXT (lowercase module, uppercase filter)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))

    # Start the Bot (using run_polling, which replaces start_polling/idle)
    print("Client Filter Bot is running...")
    # allowed_updates=Update.ALL_TYPES is often required for modern hosting
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
