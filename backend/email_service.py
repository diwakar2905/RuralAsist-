import os
from email.message import EmailMessage
import aiosmtplib

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL")
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME")

print("SMTP USER:", os.getenv("SMTP_USERNAME"))



async def send_otp_email(to_email: str, otp: str):
    message = EmailMessage()
    message["From"] = f"{SMTP_SENDER_NAME} <{SMTP_SENDER_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = "Your RuralAssist OTP"

    message.set_content(
        f"Your OTP is: {otp}\nThis OTP is valid for 5 minutes."
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        print("OTP email sent successfully!")

    except Exception as e:
        print("Error sending email:", e)
        raise e

async def send_welcome_email(to_email: str):
    message = EmailMessage()
    message["From"] = f"{SMTP_SENDER_NAME} <{SMTP_SENDER_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = "Welcome to RuralAssist!"

    message.set_content(
        f"Hi there,\n\nWelcome to RuralAssist! We're glad to have you."
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        print("Welcome email sent successfully!")

    except Exception as e:
        print("Error sending welcome email:", e)
        # We don't re-raise here to avoid breaking the login flow