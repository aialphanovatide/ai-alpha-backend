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
        print("Flag")

        # Navigate to Perplexity
        await page.goto("https://www.perplexity.ai")
        print("Flag")

        # Check if Pro Search is enabled, if not, enable it
        pro_search_toggle = await page.query_selector("div[data-state='checked']")
        if not pro_search_toggle:
            await page.click("div.rounded-full.relative.size-4.shadow-sm")
            await page.wait_for_selector("div[data-state='checked']")
        print("Flag")
    
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
