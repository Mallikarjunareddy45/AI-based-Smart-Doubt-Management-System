import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import json

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# Lazy initialize Firebase Admin account to prevent startup blocks in dev
_firebase_initialized = False

def initialize_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True
        
    if not settings.FIREBASE_CREDENTIALS_JSON:
        logger.info("FCM credentials missing. Push notifications will run in mock mode.")
        return False
        
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Load JSON config
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}. Running in mock mode.")
        return False


def send_push_notification(token: str, title: str, content: str) -> bool:
    """Send a real-time push alert to a student's mobile device via FCM."""
    if not initialize_firebase():
        logger.info(f"[MOCK PUSH] Sent to token {token[:10]}...: Title: '{title}', Body: '{content}'")
        return True
        
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=content,
            ),
            token=token,
        )
        messaging.send(message)
        logger.info(f"FCM push notification sent to token {token[:10]}...")
        return True
    except Exception as e:
        logger.error(f"FCM send error: {e}")
        return False


def send_email_notification(recipient_email: str, title: str, content: str) -> bool:
    """Send an email alert to the user via SMTP configurations."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"[MOCK EMAIL] Sent to {recipient_email}: Subject: '{title}', Body: '{content}'")
        return True
        
    try:
        # Build email MIMEMultipart structure
        msg = MIMEMultipart()
        msg['From'] = settings.EMAILS_FROM_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = title
        
        msg.attach(MIMEText(content, 'plain'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_TLS:
            server.starttls()
            
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP send email error: {e}")
        return False
