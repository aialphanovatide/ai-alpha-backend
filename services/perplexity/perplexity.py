import asyncio
import os
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

root_dir = os.path.abspath(os.path.dirname(__file__))
user_data_dir = os.path.join(root_dir, 'tmp', 'playwright')
os.makedirs(user_data_dir, exist_ok=True)

async def search_perplexity(query: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir, headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Navigate to Perplexity
        await page.goto("https://www.perplexity.ai")
        
        # Check if Pro Search is enabled, if not, enable it
        pro_search_toggle = await page.query_selector("div[data-state='checked']")
        if not pro_search_toggle:
            await page.click("div.rounded-full.relative.size-4.shadow-sm")
            await page.wait_for_selector("div[data-state='checked']")
        
        # Wait for the textarea to be available and visible
        textarea = await page.wait_for_selector("textarea[placeholder='Ask anything...']", state="visible")
        
        # Fill the textarea with the query
        await textarea.fill(query)
        
        # Press Enter to submit the query
        await textarea.press("Enter")
        
        # Wait for 20 seconds
        await asyncio.sleep(60)
        
        # Get the entire page content
        content = await page.content()
        
        # Close the browser
        await browser.close()
        
        return content

def extract_revenue(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    target_div = soup.find('div', class_='sc-gtLWhw kqHiRG')
    
    if target_div:
        code_content = target_div.find('code')
        if code_content:
            json_text = code_content.text.strip()
            try:
                data = json.loads(json_text)
                # Buscar cualquier clave que contenga 'revenue'
                revenue_key = next((key for key in data.keys() if 'revenue' in key.lower()), None)
                if revenue_key:
                    return data[revenue_key]
            except json.JSONDecodeError:
                print("Error al decodificar JSON")
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
                    print("El JSON no contiene una lista de hacks")
            except json.JSONDecodeError:
                print("Error al decodificar JSON")
    return None

# Run the function
async def main():
    revenue_query = "Please return only the current or past Annualised Revenue (Cumulative last 1yr revenue) for the $SOL cryptocurrency as a single numerical value in JSON format."
    upgrade_query="""
    Please provide, in JSON code format, all available data related to UPGRADES in $ETH. Structure the information for each hack as follows:

{
  "Event": "",
  "Date": "",
  "Event Overview": "",
  "Impact": ""
}"""
    hacks_query = """Please provide, ONLY IN JSON format, all available data related to hacks in the Polkadot (DOT) protocol. Structure the information for each hack as follows:

{
  "Hack Name": "",
  "Date": "",
  "Incident Description": "",
  "Consequences": "",
  "Risk Mitigation Measures": ""
}"""
    dapps_query="""Please provide, in JSON code format, all available data related to top DApps on the Ethereum. Structure the information for each DApp as follows:

{
  "DApp": "",
  "Description": "",
  "TVL": ""
}

Ensure that the TVL is represented as an integer in dollars (e.g., 1500000000 for $1.5 billion). 

    """
    result = await search_perplexity(hacks_query)
    r=extract_json(result)
    print(r)
    # revenue = extract_revenue(result)
    # if revenue is not None:
    #     print(f"Annual Revenue: {revenue}")
    # else:
    #     print("No se encontró la información de Revenue")
    

asyncio.run(main())