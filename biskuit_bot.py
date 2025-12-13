import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'
BOT_STATE_KEY = 'is_active'

# In-memory database to prevent duplicate links
processed_links = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'Nepal', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA',
                         'US', 'CAN', 'CANADA'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER',
                    'IT COMPANY', 'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'}


def check_client_data(report_text):
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            data[parts[0].strip().title()] = parts[1].strip()

    # STRICT FILTER: The bot ignores messages that don't match the approval format headers.
    required_keys = {'Location', 'Age', 'Job', 'Salary', 'Working Hours'}
    if not any(key in data for key in required_keys):
        return None, None

    errors = []

    # 1. Duplicate & Validity Check for Link
    link_keys = ['Client Account Link', 'Link', 'Client Link', 'Client Facebook Link', 'Client Tiktok Link', 'Client Instagram Link']
    link = next((data.get(k) for k in link_keys if data.get(k)), None)
    
    if not link or ('.' not in link):
        errors.append("❌ Missing or invalid Client Link. Please Check Sir @DLmktp1\_T389")
    elif link in processed_links:
        errors.append("❌ Duplicate Error: This link has already been checked. Please Check Sir @DLmktp1\_T389")

    # 2. Location
    loc = data.get('Location', '').upper()
    if any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append("❌ Fails Location rule. Please Check Sir @DLmktp1\_T389")

    # 3. Age
    try:
        age_match = re.search(r'\d+', data.get('Age', '0'))
        age = int(age_match.group()) if age_match else 0
        if not (MIN_AGE <= age <= MAX_AGE): 
            errors.append(f"❌ Age must be {MIN_AGE}-{MAX_AGE}. Please Check Sir @DLmktp1\_T389")
    except:
        errors.append("❌ Invalid Age format. Please Check Sir @DLmktp1\_T389")

    # 4. Salary (With "Not Telling" Option)
    salary_raw = data.get('Salary', '').upper()
    if 'NOT TELLING' not in salary_raw:
        try:
            salary_match = re.search(r'\d+', salary_raw)
            salary = int(salary_match.group()) if salary_match else 0
            if salary < MIN_SALARY: 
                errors.append(f"❌ Salary must be at least ${MIN_SALARY}. Less than {MIN_SALARY} not allowed. Please Check Sir @DLmktp1\_T389")
        except:
            errors.append("❌ Invalid Salary format. Please provide a number or 'Not Telling'.")

    # 5. Working Hours (With "Not Telling" Option)
    hours_raw = data.get('Working Hours', '').upper()
    if 'NOT TELLING' not in hours_raw:
        try:
            hours_match = re.search(r'\d+', hours_raw)
            hours = int(hours_match.group()) if hours_match else 0
            if hours > MAX_HOURS: 
                errors.append(f"❌ Working hours cannot exceed {MAX_HOURS}h. Please Check Sir @DLmktp1\_T389")
        except:
            errors.append("❌ Invalid Working Hours. Please provide a number or 'Not Telling'.")

    # 6. Job
    job = data.get('Job', '').upper()
    if any(forbidden in job for forbidden in NOT_ALLOWED_JOBS):
        errors.append("❌ Banned profession. Please Check Sir @DLmktp1\_T389")

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
    await update.message.reply_text("⏸ Bot ခဏရပ်နားမည်.")

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶ Bot ပြန်လည်လုပ်လုပ်နေပြီဖြစ်သည်.")

async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    result, remark = check_client_data(update.message.text)
    if result:
        await update.message.reply_text(f"--- SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

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

