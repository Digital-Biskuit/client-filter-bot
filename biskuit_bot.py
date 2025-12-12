import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = 'YOUR_NEW_BOT_TOKEN_HERE'
BOT_STATE_KEY = 'is_active'

# In-memory database for duplicate link check
processed_links = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY', 'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'}

def check_client_data(report_text):
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            data[parts[0].strip().title()] = parts[1].strip()

    # Only respond if the message looks like the approval format
    required_keys = {'Location', 'Age', 'Job', 'Salary', 'Working Hours'}
    if not any(key in data for key in required_keys):
        return None, None

    errors = []

    # 1. Duplicate & Validity Check for Link
    link = data.get('Client Account Link') or data.get('Link') or data.get('Client Link')
    if not link or ('.' not in link):
        errors.append("❌ Missing or invalid Client Link.")
    elif link in processed_links:
        errors.append("❌ Duplicate Error: This link has already been processed.")

    # 2. Location
    loc = data.get('Location', '').upper()
    if any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append("❌ Fails Location rule.")

    # 3. Age
    try:
        age = int(re.search(r'\d+', data.get('Age', '0')).group())
        if not (MIN_AGE <= age <= MAX_AGE): errors.append(f"❌ Age must be {MIN_AGE}-{MAX_AGE}.")
    except:
        errors.append("❌ Invalid Age.")

    # 4. Salary
    try:
        salary = int(re.search(r'\d+', data.get('Salary', '0')).group())
        if salary < MIN_SALARY: errors.append(f"❌ Salary must be at least ${MIN_SALARY}.")
    except:
        errors.append("❌ Invalid Salary.")

    # 5. Working Hours
    try:
        hours = int(re.search(r'\d+', data.get('Working Hours', '0')).group())
        if hours > MAX_HOURS: errors.append(f"❌ Working hours cannot exceed {MAX_HOURS}h.")
    except:
        errors.append("❌ Invalid Working Hours.")

    # 6. Job
    job = data.get('Job', '').upper()
    if any(forbidden in job for forbidden in NOT_ALLOWED_JOBS):
        errors.append("❌ Banned profession.")

    if not errors:
        processed_links.add(link)
        return "Passed", "✅ All requirements met. Approved."
    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

# --- COMMANDS ---
async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is ACTIVE. Format စစ်ဆေးရန် အဆင်သင့်ဖြစ်ပါပြီ။")

async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸ Bot has been paused.")

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶ Bot is now active again.")

async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return
    
    result, remark = check_client_data(update.message.text)
    if result: # Only replies if format matches
        await update.message.reply_text(f"--- RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

def main():
    application = Application.builder().token(TOKEN).build()
    application.bot_data[BOT_STATE_KEY] = True

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("unpause", unpause_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
