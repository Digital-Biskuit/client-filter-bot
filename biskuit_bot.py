import logging
import re
import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'
BOT_STATE_KEY = 'is_active'
REPORT_CHAT_ID = -1002283084705 
ADMIN_HANDLE = r"@DLTrainer\_T389"
YANGON_TZ = pytz.timezone('Asia/Yangon')

# --- ADMIN SECURITY ---
MY_ADMIN_ID = 6328052501  # Fixed: Only this ID can see all reports

# Data Storage
processed_links = set()
daily_stats = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# [NOT_DEVELOP_COUNTRIES and NOT_ALLOWED_JOBS lists stay exactly as you had them]
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'Nepal', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Democratic Republic of the Congo', 'Republic of the Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe', 'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Venezuela', 'Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Canada', 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador', 'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States', 'US', 'CAN', 'CANADA'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'DATA SCIENTIST', 'NETWORK MANAGEMENT', 'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER', 'CYBERSECURITY', 'NETWORK', 'SERVER', 'SYSTEM ADMIN'}

def check_client_data(report_text):
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            data[parts[0].strip().title()] = parts[1].strip()

    required_keys = {'Location', 'Age', 'Job', 'Salary', 'Working Hours'}
    if not any(key in data for key in required_keys):
        return None, None, "N/A"

    user_code = data.get('Code', 'UNKNOWN').upper()
    errors = []

    link_keys = ['Client Account Link', 'Link', 'Client Link', 'Client Facebook Link', 'Client Tiktok Link', 'Client Instagram Link']
    link = next((data.get(k) for k in link_keys if data.get(k)), None)
    
    if not link or ('.' not in link):
        errors.append(f"❌ Missing or invalid Client Link. Please Check Sir {ADMIN_HANDLE}")
    elif link in processed_links:
        errors.append(f"❌ Duplicate Error: This link has already been checked. Please Check Sir {ADMIN_HANDLE}")

    loc = data.get('Location', '').upper()
    if any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append(f"❌ Fails Location rule. Please Check Sir {ADMIN_HANDLE}")

    try:
        age_match = re.search(r'\d+', data.get('Age', '0'))
        age = int(age_match.group()) if age_match else 0
        if not (MIN_AGE <= age <= MAX_AGE): 
            errors.append(f"❌ Age must be {MIN_AGE}-{MAX_AGE}. Please Check Sir {ADMIN_HANDLE}")
    except:
        errors.append(f"❌ Invalid Age format. Please Check Sir {ADMIN_HANDLE}")

    salary_raw = data.get('Salary', '').upper()
    if 'NOT TELLING' not in salary_raw:
        try:
            salary_match = re.search(r'\d+', salary_raw)
            salary = int(salary_match.group()) if salary_match else 0
            if salary < MIN_SALARY: 
                errors.append(f"❌ Salary must be at least ${MIN_SALARY}. Less than {MIN_SALARY} not allowed. Please Check Sir {ADMIN_HANDLE}")
        except:
            errors.append(f"❌ Invalid Salary format. Please provide a number or 'Not Telling'.")

    hours_raw = data.get('Working Hours', '').upper()
    if 'NOT TELLING' not in hours_raw:
        try:
            hours_match = re.search(r'\d+', hours_raw)
            hours = int(hours_match.group()) if hours_match else 0
            if hours > MAX_HOURS: 
                errors.append(f"❌ Working hours cannot exceed {MAX_HOURS}h. Please Check Sir {ADMIN_HANDLE}")
        except:
            errors.append(f"❌ Invalid Working Hours. Please provide a number or 'Not Telling'.")

    job = data.get('Job', '').upper()
    if any(forbidden in job for forbidden in NOT_ALLOWED_JOBS):
        errors.append(f"❌ Banned profession. Please Check Sir {ADMIN_HANDLE}")

    if not errors:
        processed_links.add(link)
        return "Passed", "✅ All requirements met. Approved.", user_code

    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors), user_code

def update_stats(user, result, user_code):
    mention = f"@{user.username}" if user.username else user.first_name
    mention = mention.replace("_", "\\_")
    
    if user_code not in daily_stats:
        daily_stats[user_code] = {"mention": mention, "passed": 0, "failed": 0}
    
    if result == "Passed":
        daily_stats[user_code]["passed"] += 1
    else:
        daily_stats[user_code]["failed"] += 1

# --- COMMAND: MYCOUNT ---
async def mycount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mention = f"@{user.username}" if user.username else user.first_name
    mention = mention.replace("_", "\\_")
    
    user_data = None
    for code, data in daily_stats.items():
        if data["mention"] == mention:
            user_data = (code, data)
            break
            
    if user_data:
        code, data = user_data
        await update.message.reply_text(
            f"📊 **Your Progress (Code: {code})**\n✅ Passed: {data['passed']}\n❌ Failed: {data['failed']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ No reports found for you today yet.")

# --- NEW COMMAND: ALLCOUNTS (ADMIN ONLY) ---
async def allcounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ADMIN_ID:
        await update.message.reply_text("⛔ Access Denied. Only the Admin can view all counts.")
        return

    if not daily_stats:
        await update.message.reply_text("📊 No data recorded today yet.")
        return

    report = "📊 **Live Summary (Admin View)**\n\n"
    for code, data in daily_stats.items():
        report += f"🔑 **Code: {code}** ({data['mention']})\n"
        report += f"    ✅ Passed: {data['passed']} | ❌ Failed: {data['failed']}\n\n"

    await update.message.reply_text(report, parse_mode='Markdown')

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    if not daily_stats:
        return

    report = f"📊 **DAILY SUMMARY REPORT** 📊\nTarget: {ADMIN_HANDLE}\n\n"
    total_passed = 0
    total_failed = 0

    for code, data in daily_stats.items():
        report += f"🔑 **Code: {user.first_name}** ({data['mention']})\n"
        report += f"    ✅ Passed: {data['passed']} | ❌ Failed: {data['failed']}\n\n"
        total_passed += data['passed']
        total_failed += data['failed']

    report += "--------------------------\n"
    report += f"📈 **TOTAL TODAY**\n✅ Passed: {total_passed} | ❌ Failed: {total_failed}\n\n"

    try:
        await context.bot.send_message(chat_id=REPORT_CHAT_ID, text=report, parse_mode='Markdown')
        daily_stats.clear()
        processed_links.clear()
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")

async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is ACTIVE. Format စစ်ဆေးရန် အဆင်သင့်ဖြစ်ပါပြီ။")

async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸ Bot ခဏရပ်နားမည်.")

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶ Bot ပြန်လည်လုပ်လုပ်နေပြီဖြစ်သည်")

async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    result, remark, user_code = check_client_data(update.message.text)
    if result:
        update_stats(update.message.from_user, result, user_code)
        await update.message.reply_text(f"--- SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

def main():
    application = Application.builder().token(TOKEN).build()
    application.bot_data[BOT_STATE_KEY] = True
    
    report_time = datetime.time(hour=2, minute=0, second=0, tzinfo=YANGON_TZ)
    application.job_queue.run_daily(send_daily_report, time=report_time)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("unpause", unpause_command))
    application.add_handler(CommandHandler("mycount", mycount))
    application.add_handler(CommandHandler("allcounts", allcounts)) # Added Admin-only Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()

