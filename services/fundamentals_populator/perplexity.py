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
