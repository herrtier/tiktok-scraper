import asyncio
import json
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import tldextract


SEARCH_TERMS = [
    "shop sonderposten",
    "live shopping",
    "gaming stream",
    "musik live"
]

RESULTS_FILE = "tiktok_live_results.json"
CHECKED_USERS_FILE = "tiktok_checked_users.txt"
MAX_USERS_PER_TERM = 100


def extract_links_from_html(html, username):
    links_data = {}
    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]

    for link in links:
        if 'spreadshop' in link:
            links_data['spreadshop'] = link
        if 'spreadshirt' in link:
            links_data['spreadshirt'] = link
        if 'shirtee' in link:
            links_data['shirtee'] = link
        if 'impressum' in link:
            links_data['imprint'] = link

        domain_parts = tldextract.extract(link)
        domain = f'{domain_parts.domain}.{domain_parts.suffix}'
        if re.sub(r'\W+', '', username.lower()) in re.sub(r'\W+', '', domain.lower()):
            links_data['website'] = link

    return links_data


async def collect_usernames(page):
    usernames = set()
    previous_height = await page.evaluate("() => document.body.scrollHeight")
    scroll_attempts = 0
    max_attempts = 30

    while len(usernames) < MAX_USERS_PER_TERM and scroll_attempts < max_attempts:
        cards = await page.query_selector_all("a[data-e2e^='search-card-user-link']")
        for card in cards:
            href = await card.get_attribute("href")
            if href and "/@" in href:
                username = href.split("/@")[-1]
                usernames.add(username)
                if len(usernames) >= MAX_USERS_PER_TERM:
                    break

        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        new_height = await page.evaluate("() => document.body.scrollHeight")
        if new_height == previous_height:
            scroll_attempts += 1
        else:
            previous_height = new_height
            scroll_attempts = 0

    return usernames


async def main():
    checked_users = set()
    if os.path.exists(CHECKED_USERS_FILE):
        with open(CHECKED_USERS_FILE, 'r') as f:
            checked_users = set(line.strip() for line in f)

    if not Path(RESULTS_FILE).exists():
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="tiktok_state.json")
        page = await context.new_page()

        for term in SEARCH_TERMS:
            query_url = f"https://www.tiktok.com/search/live?q={term.replace(' ', '%20')}"
            print(f"[🔍] Searching term: {term}")
            await page.goto(query_url, timeout=60000)
            await page.wait_for_timeout(5000)

            usernames = await collect_usernames(page)

            for username in usernames:
                if username in checked_users:
                    continue
                checked_users.add(username)
                with open(CHECKED_USERS_FILE, 'a') as f:
                    f.write(username + "\n")

                profile_url = f"https://www.tiktok.com/@{username}"
                try:
                    await page.goto(profile_url, timeout=30000)
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    bio = await page.inner_text("[data-e2e='user-bio']") if await page.query_selector("[data-e2e='user-bio']") else ""
                    links = extract_links_from_html(html, username)

                    entry = {
                        "username": username,
                        "search_term": term,
                        "bio": bio,
                        "spreadshop": links.get("spreadshop", ""),
                        "spreadshirt": links.get("spreadshirt", ""),
                        "shirtee": links.get("shirtee", ""),
                        "imprint": links.get("imprint", ""),
                        "website": links.get("website", "")
                    }

                    with open(RESULTS_FILE, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data.append(entry)
                        f.seek(0)
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    print(f"[✓] Saved {username}")
                except Exception as e:
                    print(f"[!] Error processing {username}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
