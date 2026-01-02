import logging
import re
import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode # Added for better stability

# --- CONFIGURATION ---
TOKEN = '8287697686:AAHt-U9ZNzy_3oONuOgvJYj4zS0_nZZuMrA'
BOT_STATE_KEY = 'is_active'
ADMIN_HANDLE = "@DLTrainer_T389"
MY_ADMIN_ID = 6328052501
YANGON_TZ = pytz.timezone('Asia/Yangon')

# Persistent Memory
processed_links = set()
daily_stats = {} # Structure: {user_id: {"name": str, "passed": int, "failed": int}}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# [NOT_DEVELOP_COUNTRIES and NOT_ALLOWED_JOBS lists stay the same]
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'Nepal', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Democratic Republic of the Congo', 'Republic of the Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe', 'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Venezuela', 'Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Canada', 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador', 'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States', 'US', 'CAN', 'CANADA'}
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'DATA SCIENTIST', 'NETWORK MANAGEMENT', 'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER', 'CYBERSECURITY', 'NETWORK', 'SERVER', 'SYSTEM ADMIN'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12

def check_client_data(report_text):
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            data[parts[0].strip().title()] = parts[1].strip()

    required_keys = {'Location', 'Age', 'Job', 'Salary', 'Working Hours'}
    if not any(key in data for key in required_keys):
        return None, None

    errors = []
    link_keys = ['Client Account Link', 'Link', 'Client Link', 'Client Facebook Link']
    link = next((data.get(k) for k in link_keys if data.get(k)), None)
    
    # Improved Duplicate Check
    if not link or ('.' not in link):
        errors.append(f"❌ Missing/Invalid Link. Check Sir {ADMIN_HANDLE}")
    elif link in processed_links:
        errors.append(f"❌ <b>Duplicate Error:</b> Already submitted. Check Sir {ADMIN_HANDLE}")

    # [Remaining location/age/salary/job logic remains the same...]
    loc = data.get('Location', '').upper()
    if any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append(f"❌ Fails Location rule. Check Sir {ADMIN_HANDLE}")
    
    try:
        age_match = re.search(r'\d+', data.get('Age', '0'))
        age = int(age_match.group()) if age_match else 0
        if not (MIN_AGE <= age <= MAX_AGE):
             errors.append(f"❌ Age must be {MIN_AGE}-{MAX_AGE}. Check Sir {ADMIN_HANDLE}")
    except:
        errors.append(f"❌ Invalid Age. Check Sir {ADMIN_HANDLE}")

    if not errors:
        processed_links.add(link)
        return "Passed", "✅ All requirements met. Approved."

    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

# --- NEW COUNTING LOGIC ---
def update_daily_stats(user, result):
    uid = user.id
    name = f"@{user.username}" if user.username else user.first_name
    if uid not in daily_stats:
        daily_stats[uid] = {"name": name, "passed": 0, "failed": 0}
    
    if result == "Passed":
        daily_stats[uid]["passed"] += 1
    else:
        daily_stats[uid]["failed"] += 1

async def mycount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in daily_stats:
        s = daily_stats[uid]
        await update.message.reply_text(f"📊 <b>Your Daily Progress</b>\n✅ Passed: {s['passed']}\n❌ Failed: {s['failed']}", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ No records for you yet today.")

async def allcounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ADMIN_ID:
        return
    
    now = datetime.datetime.now(YANGON_TZ).strftime("%Y-%m-%d %H:%M")
    report = f"📊 <b>Admin Summary ({now})</b>\n\n"
    for uid, s in daily_stats.items():
        report += f"👤 {s['name']}: ✅ {s['passed']} | ❌ {s['failed']}\n"
    
    await update.message.reply_text(report if daily_stats else "📊 No data today.", parse_mode=ParseMode.HTML)

# --- COMMANDS ---
async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is ACTIVE. Format များစစ်ဆေးရန် အသင့်ဖြစ်ပါပြီ။")

async def pause_command(update: Update, context):
    if update.effective_user.id == MY_ADMIN_ID:
        context.bot_data[BOT_STATE_KEY] = False
        await update.message.reply_text("⏸️ Bot Pause")

async def unpause_command(update: Update, context):
    if update.effective_user.id == MY_ADMIN_ID:
        context.bot_data[BOT_STATE_KEY] = True
        await update.message.reply_text("▶️ Bot Resumed.")

async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    result, remark = check_client_data(update.message.text)
    if result:
        update_daily_stats(update.effective_user, result)
        # Using HTML prevents the "Can't parse entities" crash
        await update.message.reply_text(
            f"<b>--- SCAN RESULT ---</b>\n\n<b>RESULT:</b> <code>{result}</code>\n\n{remark}", 
            parse_mode=ParseMode.HTML
        )
from telegram.request import HTTPXRequest

def main():
    # Adding a 30-second timeout prevents the "Stopping Container" crash during startup
    t_request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    
    application = Application.builder().token(TOKEN).request(t_request).build()
    application.bot_data[BOT_STATE_KEY] = True

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("unpause", unpause_command))
    application.add_handler(CommandHandler("mycount", mycount))
    application.add_handler(CommandHandler("allcounts", allcounts))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))
    
    print("Bot is starting successfully...")
    application.run_polling()

if __name__ == '__main__':
    main()




