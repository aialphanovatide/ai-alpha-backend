import os
from flask import current_app
from flask_mail import Message, Mail

from dotenv import load_dotenv
load_dotenv()

class EmailService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.config.update(
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=os.environ.get('MAIL_DEFAULT_SENDER'),
            MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
            MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER')
        )
        self.mail = Mail(app)

    def send_email(self, to, subject, body):
        if not self.mail:
            self.mail = Mail(current_app)
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        msg = Message(subject, sender=sender, recipients=[to], body=body)
        self.mail.send(msg)

    def send_registration_confirmation(self, to, username):
        subject = "Welcome to The Internal Dashboard - AI ALPHA"
        body = f"Hello {username},\n\nThank you for registering on our platform. Your account has been successfully created."
        self.send_email(to, subject, body)

    def send_password_reset(self, to, reset_token):
        subject = "Password Reset Request"
        body = f"You have requested to reset your password. Please use the following token to reset your password: {reset_token}\n\nIf you did not request this, please ignore this email."
        self.send_email(to, subject, body)
        

