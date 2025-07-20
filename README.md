# TikTok Live Stream Scraper

This Python scraper uses [Playwright](https://playwright.dev/python/) to search TikTok's live section for streamers matching specific search terms (e.g., `shop sonderposten`). It extracts usernames and relevant links from profile pages and saves the results as JSON.

---

## 💡 Features

- Searches TikTok Live using custom keywords
- Extracts usernames and outbound links (e.g. shops, imprint)
- Scrolls search result pages to find more streamers
- Uses a saved login session to bypass access restrictions
- Stores data in JSON format and avoids duplicates

---

## 📦 Requirements

Install Python 3.9+ and the required libraries:

```bash
pip install -r requirements.txt
```

Your `requirements.txt` should contain:

```
playwright
beautifulsoup4
tldextract
```

After installation, run:

```bash
playwright install
```

This installs the necessary browser engine for Playwright (e.g., Chromium).

---

## 🚀 Setup

Clone the repository and enter the project folder:

```bash
git clone https://github.com/your-username/tiktok-live-scraper.git
cd tiktok-live-scraper
```

---

## 🔐 Step 1: Login to TikTok (Manual Once)

TikTok restricts search results unless you're logged in. Use the helper below to log in and save your session:

```python
from playwright.sync_api import sync_playwright

def save_tiktok_login_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")
        print("➡ Log in manually in the browser.")
        input("✅ Press Enter here after logging in...")
        context.storage_state(path="tiktok_state.json")
        browser.close()

save_tiktok_login_state()
```

This will store your authenticated session to `tiktok_state.json`.

---

## 🔍 Step 2: Run the Scraper

Update the `SEARCH_TERMS` list in `tiktok_scraper.py` with keywords you're interested in.

Example:

```python
SEARCH_TERMS = [
    "shop sonderposten",
    "gewinnspiel live",
    "deals stream"
]
```

Then execute:

```bash
python tiktok_scraper.py
```

---

## 📁 Output

- `tiktok_results.json`: Scraped data including username and links.
- `tiktok_checked_users.txt`: Tracks which users have already been scanned to avoid duplication.

---

## 📌 Notes

- Make sure your login session (`tiktok_state.json`) remains valid.
- If TikTok logs you out or the session expires, rerun the login helper.
- Always respect TikTok’s [Terms of Service](https://www.tiktok.com/legal/terms-of-service?lang=en).

---

## 🧑‍💻 Author

Developed by herrtier

---

## 🛠️ License

MIT — use responsibly and at your own risk.