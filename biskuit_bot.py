from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import os
import sys
import cv2
import pytesseract
import numpy as np
import io

# --- CONFIGURATION & SECURITY ---

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

# Load Face Detector model
# Ensure the xml file is available in your cv2 installation or local path
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# --- BOT STATE ---
BOT_STATE_KEY = 'is_active' 

# --- BOT RULE SET ---
NOT_DEVELOP_COUNTRIES = {
    'AMERICA', 'CANADA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'
}
MIN_AGE = 25
MAX_AGE = 45
MIN_SALARY = 300 
MAX_HOURS = 12
REQUIRED_FIELDS = ['Location', 'Age', 'Job', 'Working Hours', 'Client Account Link']

NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE',
    'POLICE', 'SOLDIER'
}

# --- HELPER FUNCTIONS ---

def check_client_data(report_text):
    """Parses text reports."""
    data = {}
    lines = report_text.strip().split('\n')
    for line in lines:
        if '-' in line:
            key, value = line.split('-', 1)
            data[key.strip().title()] = value.strip()

    errors = []
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"❌ Missing required field: **{field}**")

    if errors and len(errors) == len(REQUIRED_FIELDS):
        return "Can't Cut", '\n'.join(errors)

    # Location check
    location = data.get('Location', '').upper()
    if any(country in location for country in NOT_DEVELOP_COUNTRIES):
        errors.append("❌ Fails Location rule (Not Develop Country).")

    # Age check
    try:
        age = int(data.get('Age', 0))
        if not (MIN_AGE <= age <= MAX_AGE):
            errors.append(f"❌ Fails Age rule ({MIN_AGE}-{MAX_AGE}).")
    except ValueError:
        errors.append("❌ Invalid Age value.")

    # Job check
    job_input = data.get('Job', '').upper()
    if any(disallowed in job_input for disallowed in NOT_ALLOWED_JOBS):
        errors.append("❌ Fails Job rule (Banned profession).")

    if not errors:
        return "Passed", "✅ **All requirements met.**"
    return "Can't Cut", "⚠️ Reasons:\n" + '\n'.join(errors)

# --- NEW: IMAGE SCANNING HANDLER ---

async def process_image_report(update: Update, context):
    """Detects faces and reads text from uploaded screenshots."""
    if not context.bot_data.get(BOT_STATE_KEY, True):
        return

    # 1. Download Photo
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # 2. OpenCV Face Detection
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    face_count = len(faces)

    # 3. OCR Text Extraction
    extracted_text = pytesseract.image_to_string(gray)
    
    # 4. Hybrid Validation
    errors = []
    if face_count < 10:
        errors.append(f"❌ Found only {face_count} human photos. (Need 10+)")

    # Scan extracted text for banned jobs
    for job in NOT_ALLOWED_JOBS:
        if job in extracted_text.upper():
            errors.append(f"❌ Found banned job in screenshot: {job}")

    # 5. Respond
    if not errors:
        result = "Passed"
        remark = f"✅ Found {face_count} faces. Information verified via scan."
    else:
        result = "Can't Cut"
        remark = f"⚠️ **Reasons:**\n" + "\n".join(errors)

    await update.message.reply_text(f"--- IMAGE SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

# --- COMMAND HANDLERS ---

async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True 
    await update.message.reply_text('မင်္ဂလာပါ! ကျွန်တော်က T389 ရဲ့ **မန်နေဂျာပါ**.\nပို့စရာရှိတာ ပို့လို့ရပါပြီ။', parse_mode='Markdown')

async def pause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = False
    await update.message.reply_text("⏸️ **ငါ နားဦးမယ်**...", parse_mode='Markdown')

async def unpause_command(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("▶️ **ငါပြန်လာပြီ**...", parse_mode='Markdown')

async def client_filter_handler(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True) or update.message.text.startswith('/'):
        return
    result, remark = check_client_data(update.message.text)
    await update.message.reply_text(f"--- RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

# --- MAIN EXECUTION ---

def main():
    application = Application.builder().token(TOKEN).build()
    application.bot_data[BOT_STATE_KEY] = True

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("unpause", unpause_command))
    
    # Text reports handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_filter_handler))
    
    # Image reports handler (Face Detection + OCR)
    application.add_handler(MessageHandler(filters.PHOTO, process_image_report))

    application.run_polling()

if __name__ == '__main__':
    main()
