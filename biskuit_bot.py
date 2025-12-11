from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import os  # Included for best practice token handling

# --- CONFIGURATION ---
# IMPORTANT: It is safer to load the token from an Environment Variable on the server.
# For now, we use the token directly for testing.
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- BOT RULE SET (UPDATED WITH DISALLOWED JOBS) ---
NOT_DEVELOP_COUNTRIES = {
    'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'
}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300  # Must be 300 or more
MIN_HOURS = 0
MAX_HOURS = 12
# Salary is REMOVED from REQUIRED_FIELDS
REQUIRED_FIELDS = ['Location', 'Age', 'Job', 'Working Hours', 'Client Account Link']

# NEW RULE SET: Jobs that are not allowed to 'develop'
NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE',
    'POLICE', 'SOLDIER'
}


# --- HELPER FUNCTION: PARSE AND CHECK (UPDATED) ---

def check_client_data(report_text):
    """Parses the client report text and checks against the defined rules, including disallowed jobs."""
    data = {}
    lines = report_text.strip().split('\n')

    # Standardized parsing
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            # Use .title() for consistent key access in the dictionary
            data[key.strip().title()] = value.strip()

    errors = []

    # 1. Check for missing required fields (Excludes Salary)
    # Using .title() on REQUIRED_FIELDS to match the key conversion above
    for field in REQUIRED_FIELDS:
        if not data.get(field) or data.get(field) == '':
            errors.append(f"❌ Missing required field: {field}")

    if errors and len(errors) == len(REQUIRED_FIELDS):
        return "Can't Cut", '\n'.join(errors)

    # 2. Check Location
    location = data.get('Location', '').upper()
    if location in NOT_DEVELOP_COUNTRIES:
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
            # Added more robust cleaning for symbols
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
            # Use split(' ')[0] to handle inputs like "8 hours"
            working_hours = float(working_hours_str.split(' ')[0])
            if working_hours > MAX_HOURS:
                errors.append(
                    f"❌ Fails Working Hours rule (Must be less than or equal to {MAX_HOURS} hours, or 'Not Fixed').")
        except (ValueError, TypeError):
            errors.append("❌ Invalid Working Hours value. Must be a number (<=12) or 'Not Fixed/Flexible'.")

    # 6. Check Job (UPDATED WITH DISALLOWANCE RULE)
    job_input = data.get('Job', '').upper()

    # A. Check if the job field is missing or generic
    if not job_input or job_input in ['NONE', 'N/A', 'UNKNOWN']:
        errors.append("❌ Fails Job rule (Job must be specified).")
    else:
        # B. Check if the job is on the disallowed list
        is_disallowed = False
        for disallowed_job in NOT_ALLOWED_JOBS:
            # Check if the disallowed job phrase is contained within the input job description
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
        remark = "✅ All requirements met. Client can be developed."
    else:
        result = "Can't Cut"
        error_list_text = '- ' + '\n- '.join(errors)
        remark = f"⚠️ Reasons for 'Can't Cut':\n{error_list_text}"

    return result, remark


# --- HANDLER FUNCTION (NOW ASYNCHRONOUS) ---

async def client_filter_handler(update: Update, context):
    """The main handler that processes the user's client report text."""
    # Ensure update.message and update.message.text exist
    if not update.message or not update.message.text:
        return
        
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
