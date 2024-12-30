import httpx
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables from .env file
load_dotenv()

auth0Domain = os.getenv("AUTH0_DOMAIN")
auth0ManagementAPI_Client = os.getenv("AUTH0_CLIENT_ID")
auth0ManagementAPI_Secret = os.getenv("AUTH0_CLIENT_SECRET")

async def get_management_api_token():
    url = f"https://{auth0Domain}/oauth/token"
    headers = {'Content-Type': 'application/json'}
    body = {
        'client_id': auth0ManagementAPI_Client,
        'client_secret': auth0ManagementAPI_Secret,
        'audience': f'https://{auth0Domain}/api/v2/',
        'grant_type': 'client_credentials'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data['access_token']
        except httpx.RequestError as e:
            print(f"Error fetching management API token: {e}")
            return None

async def patchPassword(email: str, new_password: str) -> bool:
    """
    Update user password in Auth0 using password change endpoint
    """
    try:
        auth0_url = f'https://{auth0Domain}/dbconnections/change_password'
        payload = {
            'client_id': auth0ManagementAPI_Client,
            'email': email,
            'connection': 'Username-Password-Authentication',
            'new_password': new_password
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth0_url, json=payload) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise Exception(f"Password update failed. Status: {response.status}. Details: {error_detail}")
                
                return True

    except Exception as e:
        raise Exception(f"Password update failed: {str(e)}")