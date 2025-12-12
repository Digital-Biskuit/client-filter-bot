from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import cv2
import pytesseract
import numpy as np
import re

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'
BOT_STATE_KEY = 'is_active'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load Face Detector
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# --- DETAILED RULE SETS ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'CAN', 'UK', 'EU'}
ALLOWED_LIVE_IN = {'SAUDI ARABIA', 'DUBAI', 'UAE', 'QATAR', 'KUWAIT', 'OMAN', 'MALAYSIA', 'SINGAPORE'}
MIN_AGE, MAX_AGE = 25, 45
MIN_SALARY = 300
MAX_HOURS = 12

NOT_ALLOWED_JOBS = {
    'CONTENT CREATOR', 'COMPUTER SCIENTIST', 'SOFTWARE ENGINEER', 'WEB DEVELOPER', 'DEVELOPER', 'IT COMPANY',
    'YOUTUBER', 'JOURNALIST', 'LAWYER', 'ATTORNEY', 'ADVOCATE', 'POLICE', 'SOLDIER'
}

# --- IMAGE SCANNING HANDLER ---
async def process_image_report(update: Update, context):
    if not context.bot_data.get(BOT_STATE_KEY, True): return

    try:
        # Download the photo
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # OpenCV Setup
        nparr = np.frombuffer(photo_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Face Count Detection
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        face_count = len(faces)

        # 2. OCR Text Extraction (The part that reads Job, Age, etc.)
        extracted_text = pytesseract.image_to_string(gray).upper()
        
        errors = []

        # --- VALIDATION LOGIC ---

        # A. Face Count Check
        if face_count < 10:
            errors.append(f"❌ Found only {face_count} human photos (Need 10+).")

        # B. Location Check (Smart detection for "Lives in...")
        is_safe_location = any(zone in extracted_text for zone in ALLOWED_LIVE_IN)
        if not is_safe_location:
            for country in NOT_DEVELOP_COUNTRIES:
                if country in extracted_text:
                    errors.append(f"❌ Location: {country} is not allowed.")

        # C. Job Check
        for job in NOT_ALLOWED_JOBS:
            if job in extracted_text:
                errors.append(f"❌ Job: Banned profession detected ({job}).")

        # D. Age Check (Scanning for numbers 25-45)
        ages = re.findall(r'\b\d{2}\b', extracted_text)
        age_passed = any(MIN_AGE <= int(a) <= MAX_AGE for a in ages)
        if not age_passed and ages:
            errors.append(f"❌ Age: No valid age between {MIN_AGE}-{MAX_AGE} found.")

        # E. Salary Check
        salary_match = re.search(r'SALARY\s*-\s*([\d\.,]+)', extracted_text)
        if salary_match:
            val = float(salary_match.group(1).replace(',', ''))
            if val < MIN_SALARY:
                errors.append(f"❌ Salary: ${val} is below minimum ${MIN_SALARY}.")

        # F. Link Check
        if "HTTP" not in extracted_text and "WWW." not in extracted_text:
            errors.append("❌ Link: No social media link detected in screenshot.")

        # --- FINAL RESPONSE ---
        result = "Passed" if not errors else "Can't Cut"
        remark = f"✅ Verified {face_count} faces and report data." if not errors else "⚠️ Reasons:\n" + "\n".join(errors)

        await update.message.reply_text(f"--- IMAGE SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

    except pytesseract.TesseractNotFoundError:
        await update.message.reply_text("❌ Railway Error: Tesseract engine missing. Please set NIXPACKS_PKGS variable.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Error processing image.")

# --- COMMAND HANDLERS (Add back your existing ones) ---
async def start(update: Update, context):
    context.bot_data[BOT_STATE_KEY] = True
    await update.message.reply_text("Bot is ACTIVE. Send report or screenshot.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.bot_data[BOT_STATE_KEY] = True
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, process_image_report))
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
