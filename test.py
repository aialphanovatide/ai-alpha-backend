from playwright.sync_api import sync_playwright

def test_example():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.google.com")
        assert "google" in page.title()
        browser.close()

if __name__ == "__main__":
    test_example()