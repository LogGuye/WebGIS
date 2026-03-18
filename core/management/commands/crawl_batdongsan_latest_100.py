import re
import time
import random
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright

BASE = "https://batdongsan.com.vn"
LIST_URLS = [
    "https://batdongsan.com.vn/nha-dat-ban",
    # If you also want rentals, add:
    # "https://batdongsan.com.vn/nha-dat-cho-thue",
]

def sleep_human(a=0.9, b=1.8):
    time.sleep(random.uniform(a, b))

def extract_detail_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    seen = set()

    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        full = urljoin(BASE, href).split("?")[0]
        path = re.sub(r"^https?://[^/]+", "", full)

        # Detail URLs usually start with /ban- or /cho-thue-
        if path.startswith("/ban-") or path.startswith("/cho-thue-"):
            if path in ("/nha-dat-ban", "/nha-dat-cho-thue"):
                continue
            if full not in seen:
                seen.add(full)
                urls.append(full)

    return urls

def parse_detail(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    title_el = soup.select_one("h1")
    title = title_el.get_text(" ", strip=True) if title_el else None

    price = None
    area = None
    address = None
    posted = None

    m_price = re.search(
        r"(Giá|Mức giá)\s*[:\-]?\s*([0-9\.,]+\s*(tỷ|triệu|nghìn|đ|VND)(?:/[a-zA-Z]+)?)",
        text,
        re.IGNORECASE,
    )
    if m_price:
        price = m_price.group(2)

    m_area = re.search(r"(Diện tích)\s*[:\-]?\s*([0-9\.,]+\s*m²)", text, re.IGNORECASE)
    if m_area:
        area = m_area.group(2)

    m_addr = re.search(r"(Địa chỉ)\s*[:\-]?\s*([^|•]{8,140})", text, re.IGNORECASE)
    if m_addr:
        address = m_addr.group(2).strip()

    m_post = re.search(
        r"(Đăng\s*(hôm nay|ngày\s*[0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4}))",
        text,
        re.IGNORECASE,
    )
    if m_post:
        posted = m_post.group(1)

    return {
        "url": url,
        "title": title,
        "price": price,
        "area": area,
        "address": address,
        "posted": posted,
    }

def crawl_latest_100(output_csv="batdongsan_latest_100.csv", headless=True):
    # 1) collect URLs
    detail_urls = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(locale="vi-VN")
        page = ctx.new_page()

        for base_list_url in LIST_URLS:
            page_num = 1
            while len(detail_urls) < 100 and page_num <= 20:
                list_url = base_list_url if page_num == 1 else f"{base_list_url}/p{page_num}"
                page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
                sleep_human()

                links = extract_detail_links(page.content())
                for lk in links:
                    if lk not in seen:
                        seen.add(lk)
                        detail_urls.append(lk)
                        if len(detail_urls) >= 100:
                            break

                page_num += 1
                sleep_human(0.8, 1.4)

            if len(detail_urls) >= 100:
                break

        detail_urls = detail_urls[:100]
        print(f"Collected {len(detail_urls)} detail URLs")

        # 2) visit + parse
        rows = []
        for i, u in enumerate(detail_urls, 1):
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=60000)
                sleep_human(1.0, 2.0)
                rows.append(parse_detail(page.content(), u))
                print(f"[{i:03d}/100] OK")
            except Exception as e:
                print(f"[{i:03d}/100] FAIL: {e}")
                rows.append({"url": u, "error": str(e)})

            sleep_human(0.6, 1.3)

        ctx.close()
        browser.close()

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Saved: {output_csv}")

class Command(BaseCommand):
    help = "Crawl latest 100 listings from batdongsan.com.vn and export CSV using Playwright."

    def add_arguments(self, parser):
        parser.add_argument("--headful", action="store_true", help="Run browser with UI (not headless).")
        parser.add_argument("--out", default="batdongsan_latest_100.csv", help="Output CSV filename.")

    def handle(self, *args, **options):
        headless = not options["headful"]
        out = options["out"]
        crawl_latest_100(output_csv=out, headless=headless)