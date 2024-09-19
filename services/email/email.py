# from flask import current_app
# from flask_mail import Message, Mail

# class EmailService:
#     def __init__(self):
#         self.mail = Mail(current_app)

#     def send_email(self, to, subject, body):
#         msg = Message(subject, recipients=[to], body=body)
#         self.mail.send(msg)

#     def send_registration_confirmation(self, to, username):
#         subject = "Welcome to The Internal Dashboard - AI ALPHA"
#         body = f"Hello {username},\n\nThank you for registering on our platform. Your account has been successfully created."
#         self.send_email(to, subject, body)

#     def send_password_reset(self, to, reset_token):
#         subject = "Password Reset Request"
#         body = f"You have requested to reset your password. Please use the following token to reset your password: {reset_token}\n\nIf you did not request this, please ignore this email."
#         self.send_email(to, subject, body)


from flask import render_template_string
from flask_mail import Message, Mail
from typing import List, Optional, Dict, Any
import logging

class EmailError(Exception):
    """Custom exception for email-related errors."""
    pass

class EmailService:
    def __init__(self, app=None):
        """
        Initialize the EmailService.
        
        :param app: Flask application instance (optional)
        """
        self.mail = Mail()
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the service with a Flask application.
        
        :param app: Flask application instance
        """
        self.mail.init_app(app)

    def send_email(self, to: str, subject: str, template: str, context: Dict[str, Any],
                   cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> None:
        """
        Send an email using a template.
        
        :param to: Recipient email address
        :param subject: Email subject
        :param template: HTML template string
        :param context: Dictionary containing template variables
        :param cc: List of CC recipients (optional)
        :param bcc: List of BCC recipients (optional)
        :raises EmailError: If there's an error sending the email
        """
        try:
            html_content = render_template_string(template, **context)
            msg = Message(subject, recipients=[to], cc=cc, bcc=bcc, html=html_content)
            self.mail.send(msg)
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise EmailError(f"Failed to send email: {str(e)}")

    def send_registration_confirmation(self, to: str, username: str) -> None:
        """
        Send a registration confirmation email.
        
        :param to: Recipient email address
        :param username: Username of the newly registered user
        :raises EmailError: If there's an error sending the email
        """
        subject = "Welcome to The Internal Dashboard - AI ALPHA"
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to AI ALPHA</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 10px; text-align: center; }
                .content { margin-top: 20px; }
                .footer { margin-top: 20px; text-align: center; font-size: 0.8em; color: #777; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AI ALPHA</h1>
                </div>
                <div class="content">
                    <p>Hello {{ username }},</p>
                    <p>Thank you for registering on our platform. Your account has been successfully created.</p>
                    <p>We're excited to have you on board and can't wait to see what you'll accomplish with AI ALPHA!</p>
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                </div>
                <div class="footer">
                    <p>© 2024 AI ALPHA. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        context = {'username': username}
        self.send_email(to, subject, template, context)

    def send_password_reset(self, to: str, reset_token: str, reset_url: str) -> None:
        """
        Send a password reset email.
        
        :param to: Recipient email address
        :param reset_token: Password reset token
        :param reset_url: URL for password reset page
        :raises EmailError: If there's an error sending the email
        """
        subject = "Password Reset Request - AI ALPHA"
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Request</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #3498db; color: white; padding: 10px; text-align: center; }
                .content { margin-top: 20px; }
                .button { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }
                .footer { margin-top: 20px; text-align: center; font-size: 0.8em; color: #777; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>You have requested to reset your password for your AI ALPHA account.</p>
                    <p>Please use the following token to reset your password: <strong>{{ reset_token }}</strong></p>
                    <p>Alternatively, you can click the button below to reset your password:</p>
                    <p><a href="{{ reset_url }}" class="button">Reset Password</a></p>
                    <p>If you did not request this password reset, please ignore this email or contact our support team if you have any concerns.</p>
                </div>
                <div class="footer">
                    <p>© 2024 AI ALPHA. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        context = {'reset_token': reset_token, 'reset_url': reset_url}
        self.send_email(to, subject, template, context)

    def send_admin_notification(self, to: str, new_admin_email: str) -> None:
        """
        Send a notification email when a new admin is added.
        
        :param to: Recipient email address (existing admin)
        :param new_admin_email: Email of the newly added admin
        :raises EmailError: If there's an error sending the email
        """
        subject = "New Admin Added - AI ALPHA"
        template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Admin Added</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f39c12; color: white; padding: 10px; text-align: center; }
                .content { margin-top: 20px; }
                .footer { margin-top: 20px; text-align: center; font-size: 0.8em; color: #777; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Admin Added</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>This is to inform you that a new admin has been added to the AI ALPHA platform.</p>
                    <p>New admin email: <strong>{{ new_admin_email }}</strong></p>
                    <p>Please ensure that this addition is authorized and take any necessary steps to grant appropriate permissions.</p>
                </div>
                <div class="footer">
                    <p>© 2024 AI ALPHA. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        context = {'new_admin_email': new_admin_email}
        self.send_email(to, subject, template, context)