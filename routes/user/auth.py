import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

auth0Domain = os.getenv("AUTH0_DOMAIN")
auth0ManagementAPI_Client = os.getenv("AUTH0_MANAGEMENTAPI_CLIENT")
auth0ManagementAPI_Secret = os.getenv("AUTH0_MANAGEMENTAPI_SECRET")

async def get_management_api_token():
    """
    Get Auth0 Management API access token.
    
    Returns:
        str: The access token for Auth0 Management API.
        
    Raises:
        Exception: If token retrieval fails.
    """
    url = f"https://{auth0Domain}/oauth/token"
    payload = {
        'client_id': auth0ManagementAPI_Client,
        'client_secret': auth0ManagementAPI_Secret,
        'audience': f'https://{auth0Domain}/api/v2/',
        'grant_type': 'client_credentials',
        'scope': 'read:users update:users'
    }
    headers = {'content-type': 'application/json'}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get management token. Status: {response.status_code}")
        
    return response.json()['access_token']

async def patchPassword(email: str, new_password: str) -> bool:
    """
    Update user's password in Auth0.
    
    Args:
        email (str): User's email address.
        new_password (str): New password to set.
        
    Returns:
        bool: True if password was successfully updated.
        
    Raises:
        Exception: If password update fails or user authentication type is incompatible.
    """
    management_token = await get_management_api_token()
    if not management_token:
        raise Exception("Failed to obtain management API token")

    # Find user in Auth0
    url = f"https://{auth0Domain}/api/v2/users-by-email?email={email}"
    headers = {
        'Authorization': f'Bearer {management_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    users = response.json()
    
    if not users:
        raise Exception(f"No user found in Auth0 with email: {email}")
        
    user = users[0]
    user_id = user['user_id']
    
    # Verify authentication type
    if 'google-oauth2' in user_id:
        raise Exception("This account uses Google Sign-In")
    elif 'apple' in user_id:
        raise Exception("This account uses Apple Sign-In")
    elif 'auth0' not in user_id:
        raise Exception("This account uses external authentication")
        
    # Verify database connection
    identities = user.get('identities', [])
    if not any(identity.get('connection') == 'Username-Password-Authentication' for identity in identities):
        raise Exception("This account does not use password authentication")
        
    # Update password
    update_url = f"https://{auth0Domain}/api/v2/users/{user_id}"
    payload = {
        "password": new_password,
        "connection": "Username-Password-Authentication"
    }
    
    update_response = requests.patch(update_url, json=payload, headers=headers)
    
    if update_response.status_code != 200:
        error_data = update_response.json()
        error_message = error_data.get('message', f"Failed to update password. Status: {update_response.status_code}")
        raise Exception(f"Auth0 error: {error_message}")
        
    return True