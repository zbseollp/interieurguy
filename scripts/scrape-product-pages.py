#!/usr/bin/env python3
"""Scrape live interieurguy.nl product (beste-*) pages into Astro MDX."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as mdify

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "src/content/pages"
PUBLIC_IMAGES = ROOT / "public/images"
DATA_DIR = ROOT / "src/data"
SITE_URL = "https://interieurguy.nl"
DEFAULT_IMAGE = "/images/2023/07/1-2.jpg"

DUTCH_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mrt": 3,
    "mar": 3,
    "apr": 4,
    "mei": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dec": 12,
}

BREADCRUMB_REDIRECTS = {
    "/verwarming/": "/luchtkoelers-en-verwarmers/",
    "/verkoeling/": "/luchtkoelers-en-verwarmers/",
}

REMOVE_WIDGETS = {
    "table-of-contents",
    "social-icons",
    "spacer",
    "divider",
}


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "\n" + "\n".join(f"  - {yaml_quote(i)}" for i in items)


def upload_to_local(url: str) -> str:
    if not url:
        return url
    clean = url.split("?")[0]
    if "/wp-content/uploads/" in clean:
        rel = clean.split("/wp-content/uploads/", 1)[1]
        return f"/images/{rel}"
    return clean


def rewrite_urls(content: str) -> str:
    content = re.sub(
        rf"https?://(?:www\.)?interieurguy\.nl/wp-content/uploads/([^\s\"')]+)",
        r"/images/\1",
        content,
    )
    content = re.sub(
        rf"{re.escape(SITE_URL)}/(?P<slug>[a-z0-9\-_/]+)/?",
        r"/\g<slug>/",
        content,
    )
    content = re.sub(r"(/[^/\s\"')]+)/+", r"\1/", content)
    return content


def download_image(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["curl", "-sfL", "--max-time", "45", url, "-o", str(dest)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and dest.exists() and dest.stat().st_size > 0


def fetch_html(slug: str) -> str | None:
    url = f"{SITE_URL}/{slug}/"
    result = subprocess.run(
        ["curl", "-sfL", "--max-time", "60", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout


def parse_dutch_date(text: str) -> str | None:
    match = re.search(r"(\d{1,2})\s+([a-z]{3,4})\.?\s+(\d{4})", text, re.I)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = DUTCH_MONTHS.get(month_name.lower()[:3])
    if not month:
        return None
    return f"{year}-{month:02d}-{int(day):02d}"


def widget_type(widget) -> str | None:
    for cls in widget.get("class", []):
        if cls.startswith("elementor-widget-") and cls not in {
            "elementor-widget",
            "elementor-widget-container",
        }:
            return cls.replace("elementor-widget-", "")
    return None


def extract_breadcrumbs(soup: BeautifulSoup) -> list[dict[str, str]]:
    crumbs: list[dict[str, str]] = []
    breadcrumb_list = soup.select_one(".zbmp-breadcrumb")
    if breadcrumb_list:
        for li in breadcrumb_list.find_all("li"):
            link = li.find("a", href=True)
            if link:
                label = link.get_text(" ", strip=True)
                if not label:
                    continue
                href = rewrite_urls(link["href"])
                if not href.startswith("/"):
                    href = f"/{href.lstrip('/')}"
                if href != "/" and not href.endswith("/"):
                    href += "/"
                href = BREADCRUMB_REDIRECTS.get(href, href)
                crumbs.append({"label": label, "href": href})
            else:
                label = li.get_text(" ", strip=True)
                if label:
                    crumbs.append({"label": label, "href": ""})
        return crumbs

    widget = soup.select_one(".elementor-widget-breadcrumbs")
    if not widget:
        return []

    for link in widget.find_all("a", href=True):
        href = rewrite_urls(link["href"])
        if not href.startswith("/"):
            href = f"/{href.lstrip('/')}"
        if href != "/" and not href.endswith("/"):
            href += "/"
        label = link.get_text(" ", strip=True)
        if label:
            crumbs.append({"label": label, "href": href})

    text = widget.get_text(" ", strip=True)
    parts = [p.strip() for p in re.split(r"[>›]", text) if p.strip()]
    if parts:
        last = parts[-1]
        if not crumbs or crumbs[-1]["label"] != last:
            crumbs.append({"label": last, "href": ""})

    return crumbs


def clean_html(html: str) -> str:
    html = re.sub(r"\[[^\]]*\]", "", html)
    html = re.sub(r'data-type="[^"]*"', "", html)
    html = re.sub(r'data-word="[^"]*"', "", html)
    html = re.sub(r'title="Er is een mogelijke spelfout gevonden\."', "", html)
    return html


def clean_markdown_body(body_md: str) -> str:
    lines = body_md.splitlines()
    cleaned: list[str] = []
    skip_prefixes = ("laatst bijgewerkt:", "gepubliceerd op:")

    for line in lines:
        stripped = line.strip().lower()
        if stripped.startswith(skip_prefixes):
            continue
        if re.match(r"^\d+\.\s+\[", line):
            continue
        cleaned.append(line)

    body_md = "\n".join(cleaned)
    body_md = re.sub(r"^#\s+.+\n+", "", body_md, count=1, flags=re.M)
    body_md = re.sub(r"\[([^\]]+)\]\(#\)", r"\1", body_md)
    body_md = re.sub(r"'\s*>\s*zb_mp_\w+\]", "producten", body_md)
    body_md = re.sub(r"'\s*>\s*zb_mp_\w+", "producten", body_md)
    body_md = re.sub(r"\n{3,}", "\n\n", body_md).strip()
    return body_md


def extract_page(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    wp_page = soup.find(attrs={"data-elementor-type": "wp-page"})
    if not wp_page:
        return None

    meta_desc = soup.find("meta", attrs={"name": "description"})
    og_image = soup.find("meta", property="og:image")
    description = (
        meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
    )
    featured_image = (
        upload_to_local(og_image["content"])
        if og_image and og_image.get("content")
        else DEFAULT_IMAGE
    )
    breadcrumbs = extract_breadcrumbs(soup)

    breadcrumb_widget = wp_page.select_one(".elementor-widget-breadcrumbs")
    if breadcrumb_widget:
        host = breadcrumb_widget.find_parent(
            "div", class_=lambda c: c and "elementor-element" in " ".join(c)
        )
        (host or breadcrumb_widget).decompose()

    for widget in wp_page.find_all(
        "div",
        class_=lambda c: c
        and "elementor-element" in " ".join(c)
        and "elementor-widget" in " ".join(c),
    ):
        if widget_type(widget) in REMOVE_WIDGETS:
            widget.decompose()

    for tag in wp_page.find_all(["script", "style", "iframe"]):
        tag.decompose()

    page_title = ""
    h1 = wp_page.find("h1")
    if h1:
        page_title = h1.get_text(" ", strip=True)

    updated_date: str | None = None
    published_date: str | None = None
    for p in wp_page.find_all(string=re.compile(r"(laatst bijgewerkt|gepubliceerd op)", re.I)):
        text = str(p).strip()
        if "bijgewerkt" in text.lower():
            updated_date = parse_dutch_date(text) or updated_date
        if "gepubliceerd" in text.lower():
            published_date = parse_dutch_date(text) or published_date

    body_html = rewrite_urls(wp_page.decode_contents())
    body_html = clean_html(body_html)
    body_md = mdify(body_html, heading_style="ATX", bullets="-", strip=["script", "style"])
    body_md = clean_markdown_body(body_md)
    body_md = body_md.replace("{", "\\{").replace("}", "\\}")

    if not page_title or len(body_md) < 500:
        return None

    return {
        "title": page_title,
        "description": description[:500],
        "featuredImage": featured_image,
        "updatedDate": updated_date,
        "pubDate": published_date,
        "breadcrumbs": breadcrumbs,
        "content": body_md,
    }


def write_mdx(slug: str, data: dict) -> None:
    lines = [
        "---",
        f"title: {yaml_quote(data['title'])}",
        f"description: {yaml_quote(data['description'])}",
        f"featuredImage: {yaml_quote(data['featuredImage'])}",
        'pageType: "product"',
    ]
    if data.get("updatedDate"):
        lines.append(f"updatedDate: {yaml_quote(data['updatedDate'])}")
    if data.get("pubDate"):
        lines.append(f"pubDate: {yaml_quote(data['pubDate'])}")
    if data.get("breadcrumbs"):
        lines.append("breadcrumbs:")
        for crumb in data["breadcrumbs"]:
            lines.append(f"  - label: {yaml_quote(crumb['label'])}")
            lines.append(f"    href: {yaml_quote(crumb['href'])}")
    lines.extend(["---", "", data["content"], ""])
    (PAGES_DIR / f"{slug}.mdx").write_text("\n".join(lines), encoding="utf-8")


def update_pages_json(slug: str, data: dict) -> None:
    pages_path = DATA_DIR / "pages.json"
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    if slug not in pages:
        return
    pages[slug].update(
        {
            "title": data["title"],
            "description": data["description"],
            "featuredImage": data["featuredImage"],
            "content": data["content"],
        }
    )
    pages_path.write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8")


def collect_image_urls(content: str, featured: str) -> set[str]:
    urls: set[str] = set()
    if featured.startswith("/images/"):
        urls.add(f"{SITE_URL}/wp-content/uploads/{featured.removeprefix('/images/')}")
    for match in re.findall(r"/images/([^\s\"')]+)", content):
        urls.add(f"{SITE_URL}/wp-content/uploads/{match}")
    return urls


def download_images(urls: set[str]) -> int:
    jobs = []
    for url in sorted(urls):
        rel = url.split("/wp-content/uploads/", 1)[1]
        jobs.append((url, PUBLIC_IMAGES / rel))

    success = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_image, url, dest): url for url, dest in jobs}
        for future in as_completed(futures):
            if future.result():
                success += 1
    return success


def scrape_slug(slug: str) -> tuple[str, bool, str]:
    html = fetch_html(slug)
    if not html:
        return slug, False, "fetch failed"

    data = extract_page(html)
    if not data:
        return slug, False, "parse failed"

    write_mdx(slug, data)
    update_pages_json(slug, data)
    image_urls = collect_image_urls(data["content"], data["featuredImage"])
    downloaded = download_images(image_urls)
    return slug, True, f"{len(data['content'])} chars, {downloaded} images"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape live product pages into MDX")
    parser.add_argument("--slug", help="Scrape a single slug")
    parser.add_argument("--all", action="store_true", help="Scrape all product pages")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between requests")
    args = parser.parse_args()

    if args.slug:
        slugs = [args.slug]
    elif args.all:
        pages = json.loads((DATA_DIR / "pages.json").read_text(encoding="utf-8"))
        slugs = sorted(
            slug for slug, meta in pages.items() if meta.get("type") == "product"
        )
    else:
        parser.error("Provide --slug or --all")

    print(f"Scraping {len(slugs)} page(s) from {SITE_URL}...")
    ok = 0
    failed: list[str] = []

    for index, slug in enumerate(slugs, start=1):
        slug, success, message = scrape_slug(slug)
        status = "OK" if success else "FAIL"
        print(f"[{index}/{len(slugs)}] {status} {slug}: {message}")
        if success:
            ok += 1
        else:
            failed.append(slug)
        if index < len(slugs):
            time.sleep(args.delay)

    print(f"Done: {ok}/{len(slugs)} succeeded")
    if failed:
        print("Failed:", ", ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
