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
    # Clean the JSON content
    json_string = json_string.strip()
    
    # Search for the JSON block using a regular expression
    match = re.search(r'```json\n(.*?)```', json_string, re.DOTALL)
    if match:
        json_content = match.group(1).strip()  # Extract the JSON content
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_content)
        return data  # Return the list of dictionaries with upgrade data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

import json
import re

def extract_revenue(json_string):
    # Clean the JSON content
    json_string = json_string.strip()
    
    # Search for the JSON block using a regular expression
    match = re.search(r'```json\n(.*?)```', json_string, re.DOTALL)
    if match:
        json_content = match.group(1).strip()  # Extract the JSON content
    else:
        print("[ERROR] No JSON content found in the string.")
        return None

    if not json_content:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_content)
        return data  # Return the dictionary with revenue data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

def extract_dapps(json_string):
    # Clean the JSON content
    json_string = json_string.strip()
    if json_string.startswith("```json"):
        json_string = json_string[7:].strip()
    if json_string.endswith("```"):
        json_string = json_string[:-3].strip()

    if not json_string:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_string)
        if isinstance(data, list):
            return data  # Return the list of dictionaries
        elif isinstance(data, dict):
            return [data]  # Return a single dictionary as a list
        else:
            print("[ERROR] The content is not a valid JSON object")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

def extract_hacks(json_string):
    # Clean the JSON content
    json_string = json_string.strip()
    if json_string.startswith("```json"):
        json_string = json_string[7:].strip()
    if json_string.endswith("```"):
        json_string = json_string[:-3].strip()

    if not json_string:
        print("[ERROR] The JSON string is empty")
        return None

    try:
        data = json.loads(json_string)
        if isinstance(data, list):
            return data  # Return the list of dictionaries
        elif isinstance(data, dict):
            return [data]  # Return a single dictionary as a list
        else:
            print("[ERROR] The content is not a valid JSON object")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error decoding JSON: {str(e)}")
    
    return None

def extract_revenue(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    target_div = soup.find('div', class_='sc-gtLWhw kqHiRG')
    if target_div:
        code_content = target_div.find('code')
        if code_content:
            json_text = code_content.text.strip()
            try:
                data = json.loads(json_text)
                revenue_key = next((key for key in data.keys() if 'revenue' in key.lower()), None)
                if revenue_key:
                    return data[revenue_key]
            except json.JSONDecodeError:
                print("[ERROR] Error decoding JSON")
    return None

def extract_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    target_div = soup.find('div', class_='sc-gtLWhw kqHiRG')
    if target_div:
        code_content = target_div.find('code')
        if code_content:
            json_text = code_content.text.strip()
            try:
                data = json.loads(json_text)
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    return data
                else:
                    print("[ERROR] The JSON does not contain a list of hacks")
            except json.JSONDecodeError:
                print("[ERROR] Error decoding JSON")
    return None

def get_query(query_type, coin_name):
    queries = {
        "revenue": f"Please return only the current or past Annualised Revenue (Cumulative last 1yr revenue) for the ${coin_name} cryptocurrency as a single numerical value in JSON format.",
        "upgrade": f"""
        Please provide, in JSON code format, all available data related to UPGRADES in ${coin_name} cryptocurrency. Structure the information for each hack as follows:
        {{
          "Event": "",
          "Date": "",
          "Event Overview": "",
          "Impact": ""
        }}
        """,
        "hacks": f"""
        Please provide, ONLY IN JSON format, all available data related to hacks about ${coin_name} cryptocurrency. Structure the information for each hack as follows:
        {{
          "Hack Name": "",
          "Date": "",
          "Incident Description": "",
          "Consequences": "",
          "Risk Mitigation Measures": ""
        }}
        """,
        "dapps": f"""
        Please provide, in JSON code format, all available data related to top DApps about ${coin_name} cryptocurrency. Structure the information for each DApp as follows:
        {{
          "DApp": "",
          "Description": "",
          "TVL": ""
        }}
        
        Ensure that the TVL is represented as an integer in dollars (e.g., 1500000000 for $1.5 billion).
        """
    }
    return queries.get(query_type.lower(), None)


def extract_data_by_section(section_name, json_string):
    """
    Main function to extract data based on the section name.
    
    Args:
        section_name (str): The name of the section to extract data from.
        json_string (str): The JSON string containing the data.
    
    Returns:
        list or dict: Extracted data based on the section name.
    """
    if section_name == "hacks":
        return extract_hacks(json_string)
    elif section_name == "dapps":
        return extract_dapps(json_string)
    elif section_name == "revenue":
        return extract_revenue(json_string)
    elif section_name == "upgrade":
        return extract_upgrades(json_string)
    else:
        print(f"[ERROR] Unknown section name: {section_name}")
        return None