from playwright.sync_api import sync_playwright


def save_tiktok_login_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")
        print("➡ Please log in manually in the opened browser window.")
        input("Press Enter once you're logged in...")
        context.storage_state(path="tiktok_state.json")
        browser.close()


save_tiktok_login_state()
