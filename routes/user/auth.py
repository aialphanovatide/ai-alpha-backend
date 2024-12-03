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
    
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    return data['access_token']

async def patchPassword(email, new_password):
    try:
        # Step 1: Get the Auth0 Management API token
        token = await get_management_api_token()

        # Step 2: Fetch the user data by email
        email_check_url = f"https://{auth0Domain}/api/v2/users-by-email"
        email_check_response = requests.get(email_check_url, 
                                             params={'email': email}, 
                                             headers={'Authorization': f'Bearer {token}'})
        
        user_data = email_check_response.json()
        if user_data:
            user_id = user_data[0]['user_id']
            print("User ID fetched and it's ->", user_id)

            # Step 3: If user exists, patch the password
            patch_url = f"https://{auth0Domain}/api/v2/users/{user_id}"
            patch_response = requests.patch(patch_url, 
                                            headers={
                                                'Authorization': f'Bearer {token}',
                                                'Content-Type': 'application/json'
                                            },
                                            json={
                                                'password': new_password,
                                                'connection': 'Username-Password-Authentication'  # Asegúrate de que el tipo de conexión sea correcto
                                            })
            
            if patch_response.status_code == 200:
                print('Password updated successfully')
            else:
                print('Error updating password:', patch_response.status_code)
        else:
            print('No user found with the provided email')
    except Exception as error:
        print('Error in patchPassword function:', error)