from playwright.sync_api import sync_playwright

with sync_playwright() as p:
        browser = p.chromium.launch(slow_mo=100000, headless=False)
        page = browser.new_page()

        page.goto("https://news.google.com/", timeout=50000)
        page.wait_for_load_state("domcontentloaded", timeout=50000)

# team@novatidelabs.com
# NovaTide123!