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
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'}

def validate_report(text, current_user):
    text_upper = text.upper()
    data = {}
    
    # Check for dash format
    lines = [l for l in text.split('\n') if '-' in l]
    # STRICT RULE: Ignore text unless at least 3 valid 'Field - Value' lines are found
    if len(lines) < 3:
        return None, None

    for line in lines:
        key, val = line.split('-', 1)
        data[key.strip().title()] = val.strip()

    errors = []
    
    # 1. LINK DUPLICATION CHECK
    link_match = re.search(r'(HTTPS?://\S+|WWW\.\S+)', text, re.IGNORECASE)
    if link_match:
        found_link = link_match.group(1).lower()
        if found_link in link_database:
            original_owner = link_database[found_link]
            if original_owner != current_user:
                return "Duplicate", f"⚠️ THIS LINK WAS ALREADY UPLOADED BY @{original_owner}."
        else:
            link_database[found_link] = current_user
    else:
        errors.append("❌ Missing or invalid Client Link.")

    # 2. FIELD VALIDATIONS
    loc = data.get('Location', '').upper()
    if loc and any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append(f"❌ Location: {loc} restricted.")

    try:
        age_val = int(data.get('Age', 0))
        if age_val != 0 and not (MIN_AGE <= age_val <= MAX_AGE):
            errors.append(f"❌ Age: {age_val} outside {MIN_AGE}-{MAX_AGE}.")
    except: pass

    job_val = data.get('Job', '').upper()
    if any(forbidden in job_val for forbidden in NOT_ALLOWED_JOBS):
        errors.append(f"❌ Job: Restricted profession.")

    if not errors:
        return "Passed", "✅ Verified and Recorded."
    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

# --- HANDLERS ---

async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot Active. I only respond to full reports in 'Field - Value' format.")

async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸️ Bot Paused.")

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶️ Bot Resumed.")

async def handle_message(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    if not update.message.text or update.message.text.startswith('/'):
        return
    
    user = update.message.from_user
    username = user.username if user.username else user.first_name
    
    result, remark = validate_report(update.message.text, username)
    
    # If validate_report returns None, it means the format was wrong -> Stay Silent
    if result is None:
        return

    header = "🚨 DUPLICATE 🚨" if result == "Duplicate" else "--- RESULT ---"
    response = f"{header}\n\n**RESULT:** `{result}`\n\n{remark}\n\n**Member:** @{username}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

def main():
    app = Application.builder().token(TOKEN).build()
    app.bot_data[BOT_STATE_KEY] = True

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("unpause", unpause_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()
