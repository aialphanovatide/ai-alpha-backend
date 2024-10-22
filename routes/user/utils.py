import json
import os
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import string
from requests import Session
from config import User


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_valid_student_email(email):
    # Check if email ends with .edu or .uni
    if re.search(r'\.(edu|uni|com)$', email):
        return True

    # Get the directory of the current file
    current_dir = Path(__file__).parent

    # Construct the path to the students.json file
    json_file_path = current_dir / 'students.json'

    # Load and check against the student_mail_list
    try:
        with open(json_file_path, 'r') as file:
            universities = json.load(file)

        domain = email.split('@')[-1]
        for university in universities:
            if domain in university['domains']:
                return True

    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        # You might want to log this error or handle it differently
        return False

    return False


def generate_verification_token():
    """
    Generate a unique verification token for email verification.

    Args:
        user_id (int): The ID of the user for whom the token is being generated.
        length (int, optional): The length of the token. Defaults to 32.
        max_attempts (int, optional): Maximum number of attempts to generate a unique token. Defaults to 100.

    Returns:
        str: A unique verification token.

    Raises:
        ValueError: If unable to generate a unique token after max_attempts.
    """
    return secrets.token_urlsafe(32)