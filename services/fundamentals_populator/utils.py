import json
from bs4 import BeautifulSoup

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
    print("Flag")
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
    print("Flag")
    return queries.get(query_type.lower(), None)
