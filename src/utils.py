import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select

from src.models.users import Tokens
from src.settings import settings


async def unique_token_generator(transaction):
    letters = string.ascii_letters

    while True:
        generated_token = ''.join(random.choice(letters) for i in range(64))

        query = select(Tokens).where(Tokens.token == generated_token)
        existing_token = await transaction.execute(query)
        existing_token = existing_token.scalar_one_or_none()

        if existing_token is None:
            return generated_token


async def send_message(email: str, message: str):
    smtp_obj = smtplib.SMTP('smtp.yandex.ru', 587)
    smtp_obj.starttls()
    smtp_obj.login(settings.admin_email, settings.admin_email_password)

    msg = MIMEMultipart()
    text = message

    msg = MIMEMultipart()
    msg["From"] = settings.admin_email
    msg["To"] = email
    msg["Subject"] = ""
    msg.attach(MIMEText(text, "plain"))

    smtp_obj.send_message(msg)
