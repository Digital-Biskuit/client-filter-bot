from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300
MAX_HOURS = 12

NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'
}

# --- HELPER FUNCTION ---
def check_client_data(report_text):
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            data[key.strip().title()] = value.strip()

    errors = []
    
    # 1. Location
    loc = data.get('Location', '').upper()
    if not loc: errors.append("❌ Missing required field: Location")
    elif loc in NOT_DEVELOP_COUNTRIES: errors.append("❌ Fails Location rule (Not Develop Country).")

    # 2. Age
    try:
        age = int(data.get('Age', 0))
        if not (MIN_AGE <= age <= MAX_AGE): errors.append(f"❌ Fails Age rule ({MIN_AGE}-{MAX_AGE}).")
    except: errors.append("❌ Invalid or missing Age.")

    # 3. Job
    job = data.get('Job', '').upper()
    if not job: errors.append("❌ Missing required field: Job")
    elif any(forbidden in job for forbidden in NOT_ALLOWED_JOBS): errors.append("❌ Fails Job rule (Banned profession).")

    # 4. Salary & Hours (Rules applied if values are provided)
    try:
        salary_str = data.get('Salary', '0').replace('$', '').replace(',', '')
        if float(salary_str) < MIN_SALARY and salary_str != '0': errors.append(f"❌ Salary must be ${MIN_SALARY}+")
        
        hours_str = data.get('Working Hours', '0').split()[0]
        if float(hours_str) > MAX_HOURS: errors.append(f"❌ Hours must be <= {MAX_HOURS}")
    except: pass

    # 5. Link (FLEXIBLE CHECK: Checks for 'Client Link' OR 'Client Account Link')
    link = data.get('Client Account Link') or data.get('Client Link') or data.get('Client Facebook Link') or data.get('Client Tiktok Link') or data.get('Client Instagram Link') 
    if not link or ('.' not in link):
        errors.append("❌ Missing or invalid Client Account Link")

    if not errors:
        return "Passed", "✅ All requirements met."
    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

# --- HANDLERS ---
async def start(update: Update, context):
    await update.message.reply_text("Bot is active. Send your report.")

async def client_filter_handler(update: Update, context):
    if not update.message.text or update.message.text.startswith('/'): return
    result, remark = check_client_data(update.message.text)
    await update.message.reply_text(f"--- RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

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
