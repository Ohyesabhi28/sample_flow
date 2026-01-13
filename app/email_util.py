from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_welcome_email(email: EmailStr, username: str):
    """
    Sends a welcome email to the user using fastapi-mail.
    """
    html = f"""
    <p>Hello {username},</p>
    <p>Welcome to <b>Come On Da Sample</b>!</p> 
    <p>We are excited to have you on board.</p>
    <br>
    <p>Best regards,</p>
    <p>The Team</p>
    """

    message = MessageSchema(
        subject="Welcome to Come On Da Sample!",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    logging.info(f"Welcome email sent to {email}")
