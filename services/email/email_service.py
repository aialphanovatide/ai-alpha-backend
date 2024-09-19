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

    def send_registration_confirmation(self, to, username, temporary_password):
        subject = "Welcome to AI Alpha Dashboard"
        dashboard_url = 'https://dashboard-alpha-ai.vercel.app/#/login'  
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to AI Alpha Dashboard</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #F4F4F4;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px; margin: auto; background-color: #FFFFFF;">
                <tr>
                    <td style="padding: 40px 30px; text-align: center; background-color: #0066CC;">
                        <h1 style="color: #FFFFFF; font-size: 24px; margin: 0;">Welcome to AI Alpha Dashboard</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px 30px;">
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">Dear {username},</p>
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">Thank you for joining AI Alpha Dashboard. We're excited to have you on board!</p>
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">Your account has been created with the following credentials:</p>
                        <p style="margin: 0 0 10px; font-size: 16px; line-height: 1.5;"><strong>Username:</strong> {username}</p>
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;"><strong>Temporary Password:</strong> {temporary_password}</p>
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">Please click the button below to access the dashboard and change your password in settings menu:</p>
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: auto;">
                            <tr>
                                <td style="border-radius: 4px; background-color: #0066CC; text-align: center; padding: 10px 25px;">
                                    <a href="{dashboard_url}" style="background-color: #0066CC; color: #FFFFFF; display: inline-block; font-size: 16px; text-decoration: none;">Access Dashboard</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 30px; text-align: center; background-color: #F4F4F4; color: #888888; font-size: 14px;">
                        <p style="margin: 0;">© 2024 AI Alpha Dashboard. All rights reserved.</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        self.send_email(to, subject, html_body)

    def send_password_reset(self, to, username, reset_token):
        subject = "Password Reset - AI Alpha Dashboard"
        reset_link = f'https://your-dashboard-url.com/reset-password?token={reset_token}'  # Reemplaza con la URL real de tu página de restablecimiento de contraseña
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - AI Alpha Dashboard</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #F4F4F4;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px; margin: auto; background-color: #FFFFFF;">
                <tr>
                    <td style="padding: 40px 30px; text-align: center; background-color: #0066CC;">
                        <h1 style="color: #FFFFFF; font-size: 24px; margin: 0;">AI Alpha Dashboard Password Reset</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px 30px;">
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">Dear {username},</p>
                        <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.5;">We received a request to reset your password for the AI Alpha Dashboard. If you made this request, please click the button below to set a new password:</p>
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: auto;">
                            <tr>
                                <td style="border-radius: 4px; background-color: #0066CC; text-align: center; padding: 10px 25px;">
                                    <a href="{reset_link}" style="background-color: #0066CC; color: #FFFFFF; display: inline-block; font-size: 16px; text-decoration: none;">Reset Password</a>
                                </td>
                            </tr>
                        </table>
                        <p style="margin: 20px 0 0; font-size: 16px; line-height: 1.5;">This link will expire in 24 hours for security reasons. If you didn't request a password reset, please ignore this email or contact our support team if you have concerns.</p>
                        <p style="margin: 20px 0 0; font-size: 16px; line-height: 1.5;">For your security, please do not share this email or the reset link with anyone.</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 30px; text-align: center; background-color: #F4F4F4; color: #888888; font-size: 14px;">
                        <p style="margin: 0;">© 2024 AI Alpha Dashboard. All rights reserved.</p>
                        <p style="margin: 10px 0 0;">If you need assistance, please contact our support team.</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        self.send_email(to, subject, html_body)
