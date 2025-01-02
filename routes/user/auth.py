import asyncio
import httpx
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables from .env file
load_dotenv(override=True)

auth0Domain = os.getenv("AUTH0_DOMAIN")
auth0ManagementAPI_Client = os.getenv("AUTH0_MANAGEMENTAPI_CLIENT")
auth0ManagementAPI_Secret = os.getenv("AUTH0_MANAGEMENTAPI_SECRET")

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


async def get_users_by_name_or_email(search_term: str):
    token = await get_management_api_token()
    if not token:
        raise Exception("Failed to obtain Management API token")

    url = f"https://{auth0Domain}/api/v2/users"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    params = {
        'q': f'name:*{search_term}* OR email:*{search_term}*',
        'search_engine': 'v3'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Error fetching users: {e.response.text}")


async def list_all_users(per_page: int = 100, page: int = 1):
    token = await get_management_api_token()
    if not token:
        raise Exception("Failed to obtain Management API token")

    url = f"https://{auth0Domain}/api/v2/users"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    params = {
        'per_page': per_page,
        'page': page
    }

    all_users = []
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                users = response.json()
                if not users:
                    break
                all_users.extend(users)
                params['page'] += 1
            except httpx.HTTPStatusError as e:
                raise Exception(f"Error fetching users: {e.response.text}")

    return all_users


async def patchPassword(email: str, new_password: str) -> bool:
    """
    Update user password in Auth0 using Management API
    """
    try:
        # Step 1: Get Management API token
        token = await get_management_api_token()
        if not token:
            raise Exception("Failed to obtain Management API token")

        # Step 2: Fetch user by email
        users_url = f'https://{auth0Domain}/api/v2/users-by-email'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        params = {'email': email}
        
        async with httpx.AsyncClient() as client:
            # Get user ID from email
            response = await client.get(users_url, headers=headers, params=params)
            response.raise_for_status()
            users = response.json()
            
            if not users:
                raise Exception("No user found with the provided email")
            
            user_id = users[0]['user_id']
            
            # Step 3: Update password
            auth0_url = f'https://{auth0Domain}/api/v2/users/{user_id}'
            payload = {
                'password': new_password,
                'connection': 'Username-Password-Authentication'
            }
            
            response = await client.patch(auth0_url, headers=headers, json=payload)
            response.raise_for_status()
            return True

    except httpx.HTTPStatusError as e:
        raise Exception(f"Password update failed: {e.response.text}")
    except Exception as e:
        raise Exception(f"Password update failed: {str(e)}")
