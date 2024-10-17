import requests

def check_email_in_database(email: str) -> bool:
    api_url = "https://aialpha.ngrok.io/check-email"

    try:
        response = requests.get(api_url, params={"email": email})
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
    except requests.exceptions.RequestException as e:
        print(f"Error during the request: {e}")
        return False
    
    try:
        data = response.json()
        print(data)  # Imprimir la respuesta en la consola para depuración
        
        # Devolver True si 'success' en la respuesta es True
        return data.get("success", False)
    except ValueError:
        print("Error parsing the response JSON")
        return False

# Ejemplo de uso
# email = "!verify+m.mengo@novatidelabs.com"
# exists = check_email_in_database(email)
# print(f"User exists: {exists}")
