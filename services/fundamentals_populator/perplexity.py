import asyncio
import os
import json
import re
import tempfile
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

root_dir = os.path.abspath(os.path.dirname(__file__))
user_data_dir = os.path.join(root_dir, 'tmp', 'playwright')
os.makedirs(user_data_dir, exist_ok=True)

import os

def clear_singleton_lock():
    # Define el directorio donde se almacenan los datos del navegador (ajusta según tu estructura real)
    user_data_dir = '/ai_alpha_server_V2/services/fundamentals_populator/tmp/playwright'
    
    # Eliminar el archivo SingletonLock si existe
    lock_file = os.path.join(user_data_dir, 'SingletonLock')
    if os.path.exists(lock_file):
        os.remove(lock_file)
        print('Removed SingletonLock file.')
    else:
        print('No SingletonLock file found.')

clear_singleton_lock()

async def search_perplexity(query: str):
    # Crear un directorio temporal único para esta ejecución
    with tempfile.TemporaryDirectory() as tmpdirname:
        async with async_playwright() as p:
            # Lanzar el navegador con un contexto persistente en un directorio temporal
            browser = await p.chromium.launch_persistent_context(user_data_dir=tmpdirname, headless=False)
            page = await browser.new_page()

            # Navegar a Perplexity
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





import os
from langchain_community.chat_models import ChatPerplexity

os.environ["PERPLEXITY_API"]="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"

chat = ChatPerplexity(  
    model="llama-3.1-sonar-small-128k-online",
    temperature=0.7,
    pplx_api_key=os.getenv("PERPLEXITY_API")
)

def get_perplexity_reponse(coins):
    total_content = {}  # Usar un diccionario para almacenar las respuestas separadas
    for coin in coins:
        prompt_revenue = f"Please return only the current or past Annualised Revenue (Cumulative last 1yr revenue) for the ${coin} cryptocurrency as a single numerical value in JSON format."
        prompt_hacks = f"""Please provide, in JSON format, all available data related to historical hacks about ${coin} cryptocurrency. Structure the information for each hack as follows:  
    {{  
        "Hack Name": "",    
        "Date": "",  
        "Incident Description": "",  
        "Consequences": "",  
        "Risk Mitigation Measures": ""  
    }}  
    """
        prompt_upgrade = f"""Please provide, in JSON format, all available data related to UPGRADES about ${coin} cryptocurrency. Structure the information for each upgrade as follows:  
     {{
        "Event": "",
        "Date": "",
        "Event Overview": "",
        "Impact": ""
     }}
    """
        prompt_dapps = f"""Please provide, in JSON format, all available data related to DApps about ${coin} cryptocurrency. Structure the information for each DApp as follows:  
    {{
       "DApp": "",
       "Description": "",
       "TVL": ""
    }}
    """

        # Obtener las respuestas
        response_hacks = chat.invoke(prompt_hacks)
        response_upgrade = chat.invoke(prompt_upgrade)
        response_dapps = chat.invoke(prompt_dapps)
        response_revenue = chat.invoke(prompt_revenue)
        # Asegúrate de acceder al contenido de la respuesta correctamente
        total_content[coin] = {
            "hacks": response_hacks.content,
            "upgrades": response_upgrade.content,
            "dapps": response_dapps.content,
            "revenue": response_revenue.content
            
        }
        

    return total_content  # Devolver el diccionario con todas las respuestas
