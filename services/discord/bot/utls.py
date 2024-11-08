import requests
from typing import Optional

def check_email_in_database(email: str) -> bool:
    """
    Check if an email exists in the database using an API.

    This function sends a GET request to a specified API endpoint to verify
    if the given email exists in the database.

    Args:
        email (str): The email address to check.

    Returns:
        bool: True if the email exists in the database, False otherwise.

    Raises:
        requests.exceptions.RequestException: If there's an error during the API request.
        ValueError: If there's an error parsing the JSON response.

    Example:
        >>> exists = check_email_in_database("example@example.com")
        >>> print(f"User exists: {exists}")
    """
    api_url = "https://aialpha.ngrok.io/check-email"

    try:
        # Send GET request to the API
        response = requests.get(api_url, params={"email": email}, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Error during the API request: {e}")
        return False
    
    try:
        # Parse the JSON response
        data: Optional[dict] = response.json()
        
        # Print the response for debugging purposes
        print(f"API Response: {data}")
        
        # Check if 'success' key exists in the response and return its value
        return data.get("success", False) if isinstance(data, dict) else False
    except ValueError as e:
        print(f"Error parsing the response JSON: {e}")
        return False

# Example usage
# if __name__ == "__main__":
#     email = "!verify+m.mengo@novatidelabs.com"
#     exists = check_email_in_database(email)
#     print(f"User exists: {exists}")