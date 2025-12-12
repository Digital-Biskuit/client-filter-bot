from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import re

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'
BOT_STATE_KEY = 'is_active'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE IN MEMORY ---
link_database = {}

# --- RULE SETS ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'CANADA'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12

NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'
}

def validate_report(text, current_user):
    text_upper = text.upper()
    data = {}
    
    for line in text.split('\n'):
        if '-' in line:
            key, val = line.split('-', 1)
            data[key.strip().title()] = val.strip()

    errors = []
    
    # 1. LINK DUPLICATION & ANTI-STEAL CHECK
    link_match = re.search(r'(HTTPS?://\S+|WWW\.\S+)', text, re.IGNORECASE)
    if link_match:
        found_link = link_match.group(1).lower()
        if found_link in link_database:
            original_owner = link_database[found_link]
            if original_owner != current_user:
                return "Duplicate", f"⚠️ THIS LINK WAS ALREADY UPLOADED BY @{original_owner}. DON'T COPY OTHERS!"
        else:
            link_database[found_link] = current_user
    else:
        errors.append("❌ Missing or invalid Client Account Link.")

    # 2. LOCATION CHECK
    loc = data.get('Location', '').upper()
    if not loc:
        errors.append("❌ Missing field: Location")
    elif any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append(f"❌ Location: {loc} is not allowed.")

    # 3. AGE CHECK
    try:
        age_val = int(data.get('Age', 0))
        if not (MIN_AGE <= age_val <= MAX_AGE):
            errors.append(f"❌ Age: {age_val} is outside {MIN_AGE}-{MAX_AGE}.")
    except ValueError:
        errors.append("❌ Age: Invalid number.")

    # 4. JOB CHECK
    job_val = data.get('Job', '').upper()
    if not job_val:
        errors.append("❌ Missing field: Job")
    elif any(forbidden in job_val for forbidden in NOT_ALLOWED_JOBS):
        errors.append(f"❌ Job: {job_val} is a restricted profession.")

    # 5. SALARY CHECK
    try:
        salary_str = data.get('Salary', '0').replace('$', '').replace(',', '')
        salary_val = float(salary_str)
        if salary_val < MIN_SALARY and salary_val != 0:
            errors.append(f"❌ Salary: ${salary_val} is below ${MIN_SALARY}.")
    except ValueError:
        pass

    # 6. WORKING HOURS CHECK
    try:
        hours_str = data.get('Working Hours', '0').split()[0]
        hours_val = float(hours_str)
        if hours_val > MAX_HOURS:
            errors.append(f"❌ Hours: {hours_val} exceeds limit of {MAX_HOURS}.")
    except ValueError:
        pass

    if not errors:
        return "Passed", "✅ Verified. Link recorded under your name."
    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

# --- COMMAND HANDLERS ---

async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is active! Send your report to get approval.")

async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸️ **Bot is Paused.** I will ignore reports until you use /unpause.")

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶️ **Bot is Resumed.** Send your reports now!")

async def handle_message(update: Update, context):
    # Check if bot is active
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    if not update.message.text or update.message.text.startswith('/'):
        return
    
    user = update.message.from_user
    username = user.username if user.username else user.first_name
    
    result, remark = validate_report(update.message.text, username)
    
    header = "🚨 DUPLICATE DETECTED 🚨" if result == "Duplicate" else "--- CLIENT FILTER RESULT ---"
    response = f"{header}\n\n**RESULT:** `{result}`\n\n{remark}\n\n**Member:** @{username}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Set default state to Active
    app.bot_data[BOT_STATE_KEY] = True

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("unpause", unpause_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
