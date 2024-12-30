import os
import logging
from flask import current_app, render_template
from flask_mail import Message, Mail
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

# Configurar el logger para el servicio de email
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the email service with the given Flask app."""
        try:
            # Get email configuration from environment variables
            username = str(os.environ.get('MAIL_USERNAME', '')).strip()
            password = str(os.environ.get('MAIL_PASSWORD', '')).strip() 
            sender = str(os.environ.get('MAIL_DEFAULT_SENDER', '')).strip()

            # Configure email settings
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
            logger.info("Email service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize email service: {str(e)}", exc_info=True)
            raise

    def send_email(self, to, subject, body, html=None):
        """
        Send an email using the configured mail service.

        Args:
            to (str): Recipient email address
            subject (str): Email subject line
            body (str): Plain text email body
            html (str, optional): HTML formatted email body
        """
        if not self.mail:
            logger.info("Mail instance not found, initializing with current_app")
            self.mail = Mail(current_app)

        try:
            logger.info(f"Attempting to send email to: {to}")
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[to],
                body=body,
                html=html
            )
            
            self.mail.send(msg)
            logger.info(f"Email sent successfully to: {to}")

        except Exception as e:
            logger.error("=" * 50)
            logger.error("Email Error Details:")
            logger.error(str(e), exc_info=True)
            logger.error("=" * 50)
            raise Exception(f'Error sending email: {str(e)}')
     
    def send_registration_confirmation(self, to, username, temporary_password):
        """
        Send a registration confirmation email to a new user.

        Args:
            to (str): The email address of the recipient
            username (str): The username/nickname of the new user
            temporary_password (str): The temporary password assigned to the user

        Raises:
            Exception: If there is an error sending the email
        """
        try:
            subject = "Welcome to AI Alpha Dashboard"
            dashboard_url = 'https://dashboard-alpha-ai.vercel.app/#/login'

            logger.info(f"Preparing registration confirmation email for user: {username}")
            
            html_body = render_template(
                'welcome_email.html',
                username=username,
                temporary_password=temporary_password,
                dashboard_url=dashboard_url
            )

            self.send_email(
                to=to,
                subject=subject,
                body="",  # Empty plain text body since we're using HTML
                html=html_body
            )

            logger.info(f"Registration confirmation email sent to: {to}")

        except Exception as e:
            logger.error(f"Failed to send registration confirmation email: {str(e)}", exc_info=True)
            raise

    def send_password_reset_email(self, user_email, username, reset_link):
        """
        Send a password reset email to a user.

        Args:
            user_email (str): The email address of the user
            username (str): The username/nickname of the user
            reset_link (str): The password reset link to include in the email

        Raises:
            Exception: If there is an error sending the email
        """
        try:
            # Prepare email subject and log attempt
            subject = "Password Reset Request - AI Alpha Dashboard"
            logger.info(f"Preparing password reset email for user: {username}")
            
            # Generate HTML email body from template
            html_body = render_template(
                'password_reset_email.html',
                username=username,
                reset_link=reset_link
            )
            
            # Send the email
            self.send_email(
                to=user_email,
                subject=subject,
                body="",  # Empty plain text body since we're using HTML
                html=html_body
            )
            logger.info(f"Password reset email sent to: {user_email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}", exc_info=True)
            raise
   
    def send_password_reset_email_user(self, user_email, username, reset_link):
        """
        Send a password reset email to a user.

        Args:
            user_email (str): The email address of the user
            username (str): The username/nickname of the user
            reset_link (str): The password reset link to include in the email

        Raises:
            Exception: If there is an error sending the email
        """
        try:
            # Prepare email subject and log attempt
            subject = "Reset Your Password - AI Alpha"
            logger.info(f"Preparing password reset email for user: {username}")
            
            # Generate HTML email body from template
            html_body = render_template(
                'user_request_reset_password.html',
                reset_link=reset_link
            )
            
            # Send the email
            self.send_email(
                to=user_email,
                subject=subject,
                body="",  # Empty plain text body since we're using HTML
                html=html_body
            )
            logger.info(f"Password reset email sent to: {user_email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}", exc_info=True)
            raise

    
   