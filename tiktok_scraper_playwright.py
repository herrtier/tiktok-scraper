import asyncio
import json
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import tldextract
from langdetect import detect, LangDetectException

CATEGORIES = ["gaming", "music", "shopping", "talent", "wellness", "chatting"]
BASE_URL = "https://www.tiktok.com/live?category={}"
OUTPUT_FILE = "tiktok_live_results.json"
CHECKED_USERS_FILE = "tiktok_checked_users.txt"
MAX_STREAMERS_PER_CATEGORY = 1000


def extract_links_from_html(html, user_login):
    d = {}
    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]

    for link in links:
        if 'spreadshop' in link:
            d['spreadshop'] = link
        if 'spreadshirt' in link:
            d['spreadshirt'] = link
        if 'shirtee' in link:
            d['shirtee'] = link
        if 'impressum' in link:
            blacklisted = [
                'ins.gg', 'tworeach.com', 'reachout.agency', 'pure4u.de', 'streamfluence.de',
                '2ndwave.rocks', 'new-base.de', 'digitalninjas.de', 'onlinetitans.org',
                '2rea.ch', 'pingup.de', 'peoplessquare.de', 'beyondmgmt.de', 'lyaison.com',
                'snoops-1.mozello.shop', 'nextlevelnation.de', 'powmedia.de',
                'peoplessquare.link', '1up.management']
            check = sum([1 if exc in link else 0 for exc in blacklisted])
            if check == 0:
                d['imprint'] = link

        split_domain = tldextract.extract(link)
        domain = f'{split_domain.domain}.{split_domain.suffix}'
        if re.sub("[^A-Za-z0-9]", "", user_login).lower() in re.sub("[^A-Za-z0-9]", "", domain).lower():
            d['website'] = link
    return d


def is_german_speaker(bio, links):
    try:
        lang = detect(bio) if bio.strip() else ''
    except LangDetectException:
        lang = ''

    has_de_link = any('.de' in link for link in links.values())
    has_impressum = 'imprint' in links and links['imprint']

    return lang == 'de' or has_de_link or has_impressum


async def scroll_and_collect_usernames(page):
    usernames = set()
    last_height = await page.evaluate("() => document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 50

    while len(usernames) < MAX_STREAMERS_PER_CATEGORY and scroll_attempts < max_scroll_attempts:
        cards = await page.query_selector_all("a[href*='/@']")
        for card in cards:
            href = await card.get_attribute("href")
            if href and "/@" in href:
                username = href.split("/@")[-1].split("/")[0]
                usernames.add(username)
                if len(usernames) >= MAX_STREAMERS_PER_CATEGORY:
                    break

        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        new_height = await page.evaluate("() => document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
            last_height = new_height

    return usernames


async def main():
    checked_users = set()
    if os.path.exists(CHECKED_USERS_FILE):
        with open(CHECKED_USERS_FILE, 'r') as f:
            checked_users = set(line.strip() for line in f)

    if not Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for category in CATEGORIES:
            print(f"Checking category: {category}")
            await page.goto(BASE_URL.format(category), timeout=60000)
            await page.wait_for_timeout(5000)

            usernames = await scroll_and_collect_usernames(page)

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
                    bio = await page.inner_text("[data-e2e='user-bio']") if await page.query_selector(
                        "[data-e2e='user-bio']") else ""
                    links = extract_links_from_html(html, username)

                    if is_german_speaker(bio, links):
                        entry = {
                            "username": username,
                            "category": category,
                            "bio": bio,
                            "spreadshop": links.get("spreadshop", ""),
                            "spreadshirt": links.get("spreadshirt", ""),
                            "shirtee": links.get("shirtee", ""),
                            "imprint": links.get("imprint", ""),
                            "website": links.get("website", "")
                        }

                        with open(OUTPUT_FILE, 'r+', encoding='utf-8') as f:
                            data = json.load(f)
                            data.append(entry)
                            f.seek(0)
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        print(f"✓ {username} gespeichert (deutsch erkannt)")
                    else:
                        print(f"✗ {username} übersprungen (nicht deutsch)")
                except Exception as e:
                    print(f"⚠️ Fehler bei {username}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
