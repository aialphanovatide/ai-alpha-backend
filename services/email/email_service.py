import os
from flask import current_app, render_template
from flask_mail import Message, Mail
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

class EmailService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        # Get email configuration from environment
        username = str(os.environ.get('MAIL_USERNAME', '')).strip()
        password = str(os.environ.get('MAIL_PASSWORD', '')).strip()
        sender = str(os.environ.get('MAIL_DEFAULT_SENDER', '')).strip()
        
        app.config.update(
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=465,
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=True,
            MAIL_USERNAME=username,
            MAIL_PASSWORD=password,
            MAIL_DEFAULT_SENDER=sender
        )
        
        self.mail = Mail(app)

    def send_email(self, to, subject, body, html=None): 
        if not self.mail:
            self.mail = Mail(current_app)
        
        try:
            print(f"Attempting to send email to: {to}", flush=True)
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            msg = Message(subject, sender=sender, recipients=[to], body=body, html=html)
            self.mail.send(msg)
            print("Email sent successfully!", flush=True)
        except Exception as e: 
            print("="*50)
            print("Email Error Details:")
            print(str(e))
            print("="*50, flush=True)
            raise Exception(f'Error sending email: {str(e)}')
     
    def send_registration_confirmation(self, to, username, temporary_password):
        subject = "Welcome to AI Alpha Dashboard"
        dashboard_url = 'https://dashboard-alpha-ai.vercel.app/#/login'  

        html_body = render_template('welcome_email.html', 
                                    username=username, 
                                    temporary_password=temporary_password, 
                                    dashboard_url=dashboard_url)
        
        self.send_email(to, subject, body="", html=html_body) 

    def send_password_reset_email(self, user_email, username, reset_link):
        subject = "Password Reset Request - AI Alpha Dashboard"
        html_body = render_template('password_reset_email.html',
                            username=username,
                            reset_link=reset_link)
        
        self.send_email(to=user_email, subject=subject, body="", html=html_body)