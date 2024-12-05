import json
import re
from bs4 import BeautifulSoup


def extract_raw_json(json_string):
    print(f"[DEBUG] JSON content received: {json_string}")  # Log for debugging
    if not json_string.strip():
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_string)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            print("[ERROR] The content is not a valid JSON object")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None


def extract_upgrades(json_string):
    # Limpiar el contenido
    json_string = json_string.strip()
    
    # Buscar el bloque JSON usando una expresión regular
    match = re.search(r'```json\n(.*?)```', json_string, re.DOTALL)
    if match:
        json_content = match.group(1).strip()  # Extraer el contenido JSON
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        # Cargar el JSON
        data = json.loads(json_content)
        return data  # Retornar la lista de diccionarios con datos de upgrades
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None


def extract_revenue(json_string):
    # Limpiar el contenido
    json_string = json_string.strip()
     
    # Buscar el bloque JSON
    if json_string.startswith('```json'):
        # Extraer el contenido entre las etiquetas de código
        json_content = json_string.split('```json')[1].split('```')[0].strip()
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        # Cargar el JSON
        data = json.loads(json_content)
        return data  # Retornar el diccionario con los datos de revenue
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

def extract_dapps(json_string):
    # Limpiar el contenido
    json_string = json_string.strip()
    
    # Buscar el bloque JSON usando una expresión regular
    match = re.search(r'```json\n(.*?)```', json_string, re.DOTALL)
    if match:
        json_content = match.group(1).strip()  # Extraer el contenido JSON
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        # Cargar el JSON
        data = json.loads(json_content)
        if isinstance(data, list):
            return data  # Retornar la lista de diccionarios con datos de DApps
        else:
            print("[ERROR] The content is not a valid list of DApps")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

def extract_hacks(json_string):
    json_string = json_string.strip()
    
    match = re.search(r'```json\n(.*?)```', json_string, re.DOTALL)
    if match:
        json_content = match.group(1).strip()
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_content)
        
        if isinstance(data, list):
            return data
        else:
            print("[ERROR] The content is not a valid list of hacks")
            print(f"[DEBUG] JSON content: {json_content}")  # Imprimir el contenido JSON para depuración
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
        print(f"[DEBUG] JSON content: {json_content}")  # Imprimir el contenido JSON para depuración
    
    return None



def get_query(query_type, coin_name):
    queries = {
        "revenue": f"Please return only the current or past Annualised Revenue (Cumulative last 1yr revenue) for the ${coin_name} cryptocurrency as a single numerical value in JSON format.",
        "upgrade": f"""
        Please provide, in JSON format, all available data related to UPGRADES in ${coin_name} cryptocurrency. Structure the information for each hack as follows:
        {{
          "Event": "",
          "Date": "",
          "Event Overview": "",
          "Impact": ""
        }}
        """,
        "hacks": f"""
        Please provide, in JSON format, all available data related to hacks about ${coin_name} cryptocurrency. Structure the information for each hack as follows:
        {{
          "Hack Name": "",
          "Date": "",
          "Incident Description": "",
          "Consequences": "",
          "Risk Mitigation Measures": ""
        }}
        """,
        "dapps": f"""
        Please provide, in JSON format, all available data related to top DApps about ${coin_name} cryptocurrency. Structure the information for each DApp as follows:
        {{
          "DApp": "",
          "Description": "",
          "TVL": ""
        }}
        
        Ensure that the TVL is represented as an integer in dollars (e.g., 1500000000 for $1.5 billion).
        """
    }
    return queries.get(query_type.lower(), None)


def extract_data_by_section(section_name, total_content):
    extracted_data = {}
    for coin, content in total_content.items():
        if section_name in content:
            print(f"[DEBUG] Extracting data for section: {section_name} for coin: {coin}")
            # Llamar a la función de extracción correspondiente
            if section_name == "hacks":
                extracted_data[coin] = extract_hacks(content[section_name])
            elif section_name == "upgrades":
                extracted_data[coin] = extract_upgrades(content[section_name])
            elif section_name == "dapps":
                extracted_data[coin] = extract_dapps(content[section_name])
            elif section_name == "revenue":
                extracted_data[coin] = extract_revenue(content[section_name])
            else:
                print(f"[ERROR] Unknown section name: {section_name}")
        else:
            print(f"[WARNING] Section '{section_name}' not found for coin: {coin}")

    return extracted_data 