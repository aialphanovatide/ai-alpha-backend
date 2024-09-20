from flask import current_app
from flask_mail import Message, Mail

class EmailService:
    def __init__(self):
        self.mail = Mail(current_app)

    def send_email(self, to, subject, body):
        msg = Message(subject, recipients=[to], body=body)
        self.mail.send(msg)

    def send_registration_confirmation(self, to, username):
        subject = "Welcome to The Internal Dashboard - AI ALPHA"
        body = f"Hello {username},\n\nThank you for registering on our platform. Your account has been successfully created."
        self.send_email(to, subject, body)

    def send_password_reset(self, to, reset_token):
        subject = "Password Reset Request"
        body = f"You have requested to reset your password. Please use the following token to reset your password: {reset_token}\n\nIf you did not request this, please ignore this email."
        self.send_email(to, subject, body)