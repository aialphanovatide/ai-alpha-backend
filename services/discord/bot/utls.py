import requests
from typing import Optional
import os
from sqlalchemy.orm import Session
from config import User

def check_email_in_database(email: str, session: Session) -> bool:
    """
    Check if an email exists in the database.

    Args:
        email (str): The email address to check.

    Returns:
        bool: True if the email exists in the database, False otherwise.
    """
    # Check the database directly for the email
    existing_user = session.query(User).filter_by(email=email).first()
    if existing_user:
        return True  # Email exists in the database

    return False  # Email does not exist

# Example usage
# if __name__ == "__main__":
#     email = "!verify+m.mengo@novatidelabs.com"
#     exists = check_email_in_database(email)
#     print(f"User exists: {exists}")