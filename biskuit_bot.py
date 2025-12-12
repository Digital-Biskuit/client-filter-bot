import cv2
import pytesseract
import numpy as np
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'
BOT_STATE_KEY = 'is_active'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Face Detector - Ensure haarcascade_frontalface_default.xml is in your folder
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA',
                         'US', 'CAN', 'UK', 'EU'}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300
MAX_HOURS = 12
NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'
}


# --- TEXT SCANNING LOGIC ---
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
    if not loc:
        errors.append("❌ Missing required field: Location")
    elif any(country in loc for country in NOT_DEVELOP_COUNTRIES):
        errors.append("❌ Fails Location rule.")

    # 2. Age
    try:
        age = int(data.get('Age', 0))
        if not (MIN_AGE <= age <= MAX_AGE): errors.append(f"❌ Age must be {MIN_AGE}-{MAX_AGE}.")
    except:
        errors.append("❌ Invalid or missing Age.")

    # 3. Job
    job = data.get('Job', '').upper()
    if not job:
        errors.append("❌ Missing required field: Job")
    elif any(forbidden in job for forbidden in NOT_ALLOWED_JOBS):
        errors.append("❌ Banned profession.")

    # 4. Link
    link = data.get('Client Account Link') or data.get('Client Link') or data.get('Link')
    if not link or ('.' not in link): errors.append("❌ Missing or invalid Client Link.")

    if not errors:
        return "Passed", "✅ All requirements met. This client can be develop."
    return "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)


# --- IMAGE SCANNING LOGIC ---
async def process_image_report(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True): return

    # 1. Image Download & OpenCV Setup
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Face Count
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    face_count = len(faces)

    # 3. OCR Text Read
    extracted_text = pytesseract.image_to_string(gray).upper()

    # 4. Hybrid Check
    errors = []
    if face_count < 10: errors.append(f"❌ Found only {face_count} faces (Need 10+).")
    for job in NOT_ALLOWED_JOBS:
        if job in extracted_text: errors.append(f"❌ Banned job found in screenshot: {job}")

    if not errors:
        result, remark = "Passed", f"✅ Found {face_count} faces and info is valid."
    else:
        result, remark = "Can't Cut", "⚠️ Reasons:\n" + "\n".join(errors)

    await update.message.reply_text(f"--- SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')


# --- COMMANDS ---
async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is ACTIVE. စတင်ပြီး Approval တောင်းခံနိုင်ပါပြီ။")


async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸ Bot ရပ်နားမည်.")


async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶ Bot ပြန်လည်လုပ်လုပ်နေပြီဖြစ်သည်.")


async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True): return
    if not update.message.text or update.message.text.startswith('/'): return
    result, remark = check_client_data(update.message.text)
    await update.message.reply_text(f"--- RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')


# --- MAIN ---
def main():
    application = Application.builder().token(TOKEN).build()
    application.bot_data[BOT_STATE_KEY] = True

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("unpause", unpause_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))
    application.add_handler(MessageHandler(filters.PHOTO, process_image_report))

    print("Bot is running...")
    application.run_polling()


if __name__ == '__main__':
    main()
