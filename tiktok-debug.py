from playwright.sync_api import sync_playwright


def inspect_tiktok_search_page(query="shop sonderposten"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        url = f"https://www.tiktok.com/search/live?q={query.replace(' ', '%20')}"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(10000)
        html_content = page.content()
        print(html_content)
        browser.close()


inspect_tiktok_search_page()
