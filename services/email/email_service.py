import os
from flask import current_app, render_template
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

    def send_email(self, to, subject, body, html=None): 
        if not self.mail:
            self.mail = Mail(current_app)
        
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        msg = Message(subject, sender=sender, recipients=[to], body=body, html=html)
        
        try:
            self.mail.send(msg)  # Attempt to send the email
        except Exception as e: 
            raise  Exception(f'Error sending email: {str(e)}')
     
    def send_registration_confirmation(self, to, username, temporary_password):
        subject = "Welcome to AI Alpha Dashboard"
        dashboard_url = 'https://dashboard-alpha-ai.vercel.app/#/login'  

        html_body = render_template('welcome_email.html', 
                                    username=username, 
                                    temporary_password=temporary_password, 
                                    dashboard_url=dashboard_url)
        
        # Use the send_email method to send the registration confirmation email
        self.send_email(to, subject, body="", html=html_body) 

    def send_password_reset_email(self, user_email, username, reset_link):
        subject = "Password Reset Request - AI Alpha Dashboard"
        html_body = render_template('password_reset_email.html',
                            username=username,
                            reset_link=reset_link)
        
        # Use the send_email method to send the password reset email
        self.send_email(to=user_email, subject=subject, body="", html=html_body)