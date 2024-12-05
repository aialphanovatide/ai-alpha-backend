import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
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
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status() 
        data = response.json()
        return data['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching management API token: {e}")
        return None

async def patchPassword(email, new_password):
    try:
        # Step 1: Get the Auth0 Management API token
        token = await get_management_api_token()
        if not token:
            raise Exception("Failed to obtain management API token")

        # Step 2: Fetch the user data by email
        email_check_url = f"https://{auth0Domain}/api/v2/users-by-email"
        email_check_response = requests.get(email_check_url, 
                                          params={'email': email}, 
                                          headers={'Authorization': f'Bearer {token}'})
        email_check_response.raise_for_status()
        
        user_data = email_check_response.json()
        if not user_data:
            raise Exception("User not found")

        user_id = user_data[0]['user_id']

        # Step 3: Patch the password
        patch_url = f"https://{auth0Domain}/api/v2/users/{user_id}"
        patch_response = requests.patch(patch_url, 
                                      headers={
                                          'Authorization': f'Bearer {token}',
                                          'Content-Type': 'application/json'
                                      },
                                      json={
                                          'password': new_password,
                                          'connection': 'Username-Password-Authentication'
                                      })
        
        patch_response.raise_for_status()
        return True

    except requests.exceptions.RequestException as error:
        raise Exception(f"Auth0 API error: {str(error)}")
    except Exception as error:
        raise Exception(f"Password update failed: {str(error)}")