from fastapi import BackgroundTasks
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def send_verification_email(email_to: str, token: str):
    verify_link = f"http://127.0.0.1:8000/auth/verify-email/{token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your email"
    msg["From"] = SMTP_USER
    msg["To"] = email_to

    text = f"Click the link to verify your email: {verify_link}"
    msg.attach(MIMEText(text, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, email_to, msg.as_string())

def send_password_reset_email(email: str, token: str):
    reset_link = f"http://localhost:8000/auth/reset-password/{token}"
    print(f"📧 Password reset link for {email}: {reset_link}")
