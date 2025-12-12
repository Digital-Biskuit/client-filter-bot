from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import logging
import cv2
import pytesseract
import numpy as np
import re

# --- CONFIGURATION ---
TOKEN = '8287697686:AAGrq9d1R3YPW7Sag48jFA4T2iD7NZTzyJA'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load Face Detector
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# --- RULES ---
NOT_DEVELOP_COUNTRIES = {'AMERICA', 'CANADA', 'AFRICA', 'MYANMAR', 'THAILAND', 'CAMBODIA', 'LAOS', 'CHINA', 'VIETNAM', 'USA', 'US', 'UK', 'EU'}
NOT_ALLOWED_JOBS = {'CONTENT CREATOR', 'SOFTWARE ENGINEER', 'DEVELOPER', 'POLICE', 'SOLDIER', 'LAWYER', 'YOUTUBER'}

# --- IMAGE SCANNING LOGIC ---
async def process_image_report(update: Update, context):
    """Scans screenshot for faces and required text data."""
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # 1. Image Setup
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Face Detection
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    face_count = len(faces)

    # 3. Text Extraction (OCR)
    extracted_text = pytesseract.image_to_string(gray).upper()
    
    errors = []

    # 4. Validate Faces
    if face_count < 10:
        errors.append(f"❌ Found only {face_count} faces. (Need 10+)")

    # 5. Validate Location (Scanning text for banned countries)
    for country in NOT_DEVELOP_COUNTRIES:
        if country in extracted_text:
            errors.append(f"❌ Location Rule: Banned country detected ({country}).")

    # 6. Validate Job (Scanning text for banned jobs)
    for job in NOT_ALLOWED_JOBS:
        if job in extracted_text:
            errors.append(f"❌ Job Rule: Banned profession detected ({job}).")

    # 7. Validate Age (Looking for numbers in the text)
    # This is a basic check to see if an age between 25-45 exists in the text
    ages_found = re.findall(r'\b\d{2}\b', extracted_text)
    valid_age = any(25 <= int(a) <= 45 for a in ages_found)
    if not valid_age and ages_found:
        errors.append("❌ Age Rule: No valid age (25-45) found in text.")

    # 8. Result
    if not errors:
        result = "Passed"
        remark = f"✅ Verified: {face_count} faces found. Info checks out."
    else:
        result = "Can't Cut"
        remark = f"⚠️ Reasons:\n" + "\n".join(errors)

    await update.message.reply_text(f"--- SCAN RESULT ---\n\n**RESULT:** `{result}`\n\n{remark}", parse_mode='Markdown')

async def start(update: Update, context):
    await update.message.reply_text("Bot Active. Send a screenshot to scan.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, process_image_report))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
