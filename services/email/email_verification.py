import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from pathlib import Path
import json



class EmailService:
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = os.getenv('SENDER_EMAIL', 'info@aialpha.ai')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.api_key = 'alpha_I0fLqLVhQnNbQwUHU7RU5aN957Vv181r_2664'
        
        if not self.email_password:
            raise ValueError("EMAIL_PASSWORD environment variable is not set")

    def send_verification_email(self, to_email, verification_link):
        """
        Send a verification email with API key verification
        """
        try:
            message = self._prepare_email_message(to_email, verification_link)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                print(f"Attempting to login with email: {self.sender_email}")
                server.login(self.sender_email, self.email_password)
                server.send_message(message)
                
            return {"success": True, "message": f"Verification email sent successfully to {to_email}"}
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}

    def _prepare_email_message(self, to_email, verification_link):
        """
        Prepare the email message with HTML template including API key instructions
        """
        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = to_email
        message['Subject'] = 'Email Verification - AI Alpha'
        
        html_content = self._get_email_template(verification_link)
        message.attach(MIMEText(html_content, 'html'))
        return message

    def _get_email_template(self, verification_link):
        """
        Get and populate email template with verification link and API key
        """
        # Crear un link que incluya instrucciones para el frontend
        frontend_verification_link = f"{verification_link}"
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Verify your email</h2>
                    <p>Please click the button below to verify your email:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{frontend_verification_link}" 
                           style="background-color: #3498db; 
                                  color: white; 
                                  padding: 12px 24px; 
                                  text-decoration: none; 
                                  border-radius: 5px; 
                                  display: inline-block;">
                            Verify Email
                        </a>
                    </div>
                    <p style="font-size: 12px; color: #7f8c8d;">
                        If the button doesn't work, you can copy and paste this URL into your browser:
                        <br>
                        {frontend_verification_link}
                    </p>
                </div>
            </body>
        </html>
        """

