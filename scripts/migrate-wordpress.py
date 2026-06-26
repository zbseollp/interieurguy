#!/usr/bin/env python3
"""Migrate WordPress WXR export into Astro content collections for interieurguy.nl."""

from __future__ import annotations

import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML_PATH = Path(
    os.environ.get(
        "WXR_PATH",
        "/Users/gauravkashyap/Downloads/interieurguynl.WordPress.2026-06-26.xml",
    )
)
SITE_URL = "https://interieurguy.nl"

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}

BLOG_DIR = ROOT / "src/content/blog"
PAGES_DIR = ROOT / "src/content/pages"
AUTHORS_DIR = ROOT / "src/content/authors"
CATEGORIES_DIR = ROOT / "src/content/categories"
TAGS_DIR = ROOT / "src/content/tags"
PUBLIC_IMAGES = ROOT / "public/images"
DATA_DIR = ROOT / "src/data"

SKIP_PAGE_SLUGS = {
    "home",
    "blog",
    "contact",
    "contact-us",
    "about-us",
    "zb_mp_product",
    "sitemap",
    "laatste-berichten",
}
DEFAULT_IMAGE = "/images/2023/07/1-2.jpg"

PRODUCT_IMAGES = {
    "beste-zwevend-tv-meubel": "/images/2023/07/1-2.jpg",
    "beste-beveiligingscamera-buiten": "/images/2023/07/3.jpg",
    "beste-katoenen-dekbedovertrek": "/images/2023/07/4.jpg",
    "beste-radiatorombouw": "/images/2023/07/2.jpg",
    "beste-open-boekenkast": "/images/2023/07/5.jpg",
    "beste-stoomreiniger-laminaat": "/images/2023/07/Schoonmaak.jpg",
    "beste-prullenbak-met-sensor": "/images/2023/07/ton.jpg",
    "beste-elektrische-haard": "/images/2023/07/6.jpg",
    "beste-digitale-wekker": "/images/2023/07/alarm.jpg",
    "beste-stille-mobiele-airco": "/images/2023/07/ac.jpg",
    "beste-bijzettafel-hout": "/images/2023/07/tafel.jpg",
    "beste-slimme-rookmelder": "/images/2023/07/melder.jpg",
}


def text(el) -> str:
    return el.text.strip() if el is not None and el.text else ""


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


def rewrite_urls(content: str, url_map: dict[str, str]) -> str:
    if not content:
        return ""

    def replace_upload_url(match: re.Match) -> str:
        url = match.group(0)
        local = url_map.get(url) or url_map.get(url.split("?")[0])
        if local:
            return local
        if "/wp-content/uploads/" in url:
            local_path = upload_to_local(url)
            url_map[url] = local_path
            url_map[url.split("?")[0]] = local_path
            return local_path
        return url

    content = re.sub(
        rf"https?://(?:www\.)?interieurguy\.nl/wp-content/uploads/[^\s\"'<>]+",
        replace_upload_url,
        content,
    )
    content = re.sub(
        rf"{re.escape(SITE_URL)}/(?P<slug>[a-z0-9\-_/]+)/?",
        r"/\g<slug>/",
        content,
    )
    content = re.sub(r"/(?P<slug>[a-z0-9\-]+)//", r"/\g<slug>/", content)
    return content


def extract_first_image(content: str) -> str | None:
    for pattern in [
        r'src="(/images/[^"]+)"',
        r'src="(/wp-content/uploads/[^"]+)"',
    ]:
        match = re.search(pattern, content or "")
        if match:
            src = match.group(1)
            return src if src.startswith("/images/") else upload_to_local(
                f"{SITE_URL}{src}" if src.startswith("/") else src
            )
    return None


def strip_html(html: str) -> str:
    text_value = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text_value).strip()[:300]


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


def strip_shortcodes(value: str) -> str:
    return re.sub(r"\[[^\]]*\]", "", value)


def prepare_mdx_body(html: str) -> str:
    html = re.sub(r"<!--[\s\S]*?-->", "", html or "")
    html = strip_shortcodes(html)

    try:
        from markdownify import markdownify as md
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style", "iframe"]):
            tag.decompose()
        cleaned = str(soup)
        text = md(cleaned, heading_style="ATX", bullets="-", strip=["script", "style"])
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text.replace("{", "\\{").replace("}", "\\}")
    except ImportError:
        text = strip_html(html)
        return text.replace("{", "\\{").replace("}", "\\}")


def sanitize_frontmatter_text(value: str) -> str:
    value = strip_shortcodes(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:500]


def parse_wxr() -> dict:
    authors: dict[str, dict] = {}
    categories: dict[str, dict] = {}
    tags: dict[str, dict] = {}
    attachments: dict[str, str] = {}
    items: list[dict] = []
    nav_items: list[dict] = []

    for event, elem in ET.iterparse(XML_PATH, events=("end",)):
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "author":
            login = text(elem.find("wp:author_login", NS))
            authors[login] = {
                "id": text(elem.find("wp:author_id", NS)),
                "login": login,
                "email": text(elem.find("wp:author_email", NS)),
                "displayName": text(elem.find("wp:author_display_name", NS)),
            }
            elem.clear()
            continue

        if tag == "category":
            slug = text(elem.find("wp:category_nicename", NS))
            categories[slug] = {
                "slug": slug,
                "name": text(elem.find("wp:cat_name", NS)),
                "parent": text(elem.find("wp:category_parent", NS)),
            }
            elem.clear()
            continue

        if tag != "item":
            continue

        post_type = text(elem.find("wp:post_type", NS))
        status = text(elem.find("wp:status", NS))
        post_id = text(elem.find("wp:post_id", NS))
        slug = text(elem.find("wp:post_name", NS))
        title = text(elem.find("title"))
        link = text(elem.find("link"))
        creator = text(elem.find("dc:creator", NS))
        content = text(elem.find("content:encoded", NS))
        excerpt = text(elem.find("excerpt:encoded", NS))
        pub_date = text(elem.find("wp:post_date", NS))
        modified = text(elem.find("wp:post_modified", NS))

        postmeta = {}
        for pm in elem.findall("wp:postmeta", NS):
            key = text(pm.find("wp:meta_key", NS))
            val = text(pm.find("wp:meta_value", NS))
            if key:
                postmeta[key] = val

        cats = []
        post_tags = []
        for cat in elem.findall("category"):
            domain = cat.get("domain", "")
            nicename = cat.get("nicename", "")
            label = cat.text or ""
            if domain == "category" and label:
                cats.append(label)
                if nicename and nicename not in categories:
                    categories[nicename] = {"slug": nicename, "name": label, "parent": ""}
            elif domain == "post_tag" and label:
                post_tags.append(label)
                if nicename and nicename not in tags:
                    tags[nicename] = {"slug": nicename, "name": label}

        attachment_url = text(elem.find("wp:attachment_url", NS))
        if post_type == "attachment" and attachment_url:
            attachments[post_id] = attachment_url

        if post_type == "nav_menu_item" and status == "publish":
            nav_items.append(
                {
                    "post_id": post_id,
                    "title": title,
                    "slug": slug,
                    "menu_order": int(text(elem.find("wp:menu_order", NS)) or 0),
                    "meta": postmeta,
                }
            )
        elif post_type in {"post", "page"} and status == "publish":
            items.append(
                {
                    "post_type": post_type,
                    "post_id": post_id,
                    "slug": slug,
                    "title": title,
                    "link": link,
                    "author": creator,
                    "content": content,
                    "excerpt": excerpt,
                    "pubDate": pub_date,
                    "updatedDate": modified,
                    "categories": cats,
                    "tags": post_tags,
                    "meta": postmeta,
                }
            )

        elem.clear()

    return {
        "authors": authors,
        "categories": categories,
        "tags": tags,
        "attachments": attachments,
        "items": items,
        "nav_items": nav_items,
    }


def resolve_thumbnail(item: dict, attachments: dict[str, str]) -> str | None:
    thumb_id = item["meta"].get("_thumbnail_id")
    if thumb_id and thumb_id in attachments:
        return upload_to_local(attachments[thumb_id])
    return None


def write_mdx(path: Path, frontmatter: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        if value is None:
            continue
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:{yaml_list(value)}")
        elif isinstance(value, str):
            lines.append(f"{key}: {yaml_quote(value)}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_blog_posts_json(posts: list[dict]) -> None:
    latest = sorted(posts, key=lambda p: p["pubDate"], reverse=True)
    out = []
    for item in latest:
        featured = item.get("featuredImage") or DEFAULT_IMAGE
        out.append(
            {
                "slug": item["slug"],
                "title": item["title"],
                "description": item["description"],
                "featuredImage": featured,
                "pubDate": item["pubDate"][:10],
            }
        )
    (DATA_DIR / "blog-posts.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_existing_products() -> dict:
    pages_path = DATA_DIR / "pages.json"
    products: dict = {}
    if pages_path.exists():
        data = json.loads(pages_path.read_text(encoding="utf-8"))
        products = {k: v for k, v in data.items() if v.get("type") == "product"}

    slugs_path = DATA_DIR / "slugs.json"
    if slugs_path.exists():
        for slug in json.loads(slugs_path.read_text(encoding="utf-8")):
            if not slug.startswith("beste-") or slug in products:
                continue
            title = slug.replace("beste-", "").replace("-", " ").title()
            products[slug] = {
                "slug": slug,
                "title": f"Beste {title}",
                "description": f"Lees alles over {title.lower()} op InterieurGuy.nl.",
                "featuredImage": PRODUCT_IMAGES.get(slug, DEFAULT_IMAGE),
                "content": "",
                "type": "product",
                "url": f"/{slug}/",
            }
    return products


def write_pages_json(page_items: list[dict], products: dict) -> None:
    pages_data = dict(products)
    for item in page_items:
        slug = item["slug"]
        page_type = "category" if slug in {
            "meubels",
            "slaapkamer",
            "elektrische-apparaten",
            "veiligheid",
            "rekken-en-manden",
            "decoratie",
            "luchtkoelers-en-verwarmers",
        } else "page"
        pages_data[slug] = {
            "slug": slug,
            "title": item["title"],
            "description": item["description"],
            "featuredImage": item.get("featuredImage", DEFAULT_IMAGE),
            "content": item.get("content", ""),
            "type": page_type,
            "url": f"/{slug}/",
        }
    blog_slugs = [p["slug"] for p in json.loads((DATA_DIR / "blog-posts.json").read_text())] if (DATA_DIR / "blog-posts.json").exists() else []
    slugs = sorted(set(pages_data.keys()) | set(blog_slugs) | set(json.loads((DATA_DIR / "slugs.json").read_text()) if (DATA_DIR / "slugs.json").exists() else []))
    (DATA_DIR / "pages.json").write_text(
        json.dumps(pages_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (DATA_DIR / "slugs.json").write_text(json.dumps(slugs, indent=2), encoding="utf-8")


def migrate() -> None:
    print(f"Parsing {XML_PATH}...")
    data = parse_wxr()
    url_map: dict[str, str] = {}
    image_urls: set[str] = set()

    for url in data["attachments"].values():
        image_urls.add(url)

    posts_raw = [i for i in data["items"] if i["post_type"] == "post"]
    pages_raw = [
        i
        for i in data["items"]
        if i["post_type"] == "page" and i["slug"] not in SKIP_PAGE_SLUGS
    ]
    existing_products = load_existing_products()

    print(f"Migrating {len(posts_raw)} posts, {len(pages_raw)} pages...")

    for directory in (BLOG_DIR, PAGES_DIR):
        if directory.exists():
            for pattern in ("*.mdx", "*.md"):
                for f in directory.glob(pattern):
                    f.unlink()

    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    migrated_posts: list[dict] = []
    migrated_pages: list[dict] = []

    for item in posts_raw:
        body = rewrite_urls(item["content"], url_map)
        featured = resolve_thumbnail(item, data["attachments"]) or extract_first_image(body)
        if featured:
            full_url = (
                featured
                if featured.startswith("http")
                else f"{SITE_URL}/wp-content/uploads/{featured.split('/images/', 1)[-1]}"
                if featured.startswith("/images/")
                else f"{SITE_URL}{featured}"
            )
            if "/wp-content/uploads/" in full_url or featured.startswith("/images/"):
                image_urls.add(
                    full_url
                    if full_url.startswith("http")
                    else f"{SITE_URL}/wp-content/uploads/{featured.split('/images/', 1)[-1]}"
                )

        description = sanitize_frontmatter_text(
            strip_html(item["excerpt"]) or strip_html(body) or item["title"]
        )
        pub_iso = item["pubDate"].replace(" ", "T")
        updated_iso = item["updatedDate"].replace(" ", "T")

        frontmatter = {
            "title": sanitize_frontmatter_text(item["title"]),
            "description": description,
            "pubDate": pub_iso,
            "updatedDate": updated_iso,
            "author": item["author"],
            "categories": item["categories"] or ["Blog"],
            "tags": item["tags"],
            "featuredImage": featured or DEFAULT_IMAGE,
            "imageAlt": sanitize_frontmatter_text(item["title"]),
        }

        write_mdx(BLOG_DIR / f"{item['slug']}.mdx", frontmatter, prepare_mdx_body(body))

        migrated_posts.append(
            {
                "slug": item["slug"],
                "title": frontmatter["title"],
                "description": description,
                "featuredImage": frontmatter["featuredImage"],
                "pubDate": item["pubDate"],
            }
        )

        for match in re.findall(
            rf"https?://(?:www\.)?interieurguy\.nl/wp-content/uploads/[^\s\"'<>]+",
            body,
        ):
            image_urls.add(match)
        for match in re.findall(r"/images/[^\s\"'<>]+", body):
            rel = match.split("/images/", 1)[-1]
            image_urls.add(f"{SITE_URL}/wp-content/uploads/{rel}")

    for item in pages_raw:
        body = rewrite_urls(item["content"], url_map)
        featured = resolve_thumbnail(item, data["attachments"]) or extract_first_image(body)
        description = sanitize_frontmatter_text(
            strip_html(item["excerpt"]) or strip_html(body) or item["title"]
        )
        pub_iso = item["pubDate"].replace(" ", "T")
        updated_iso = item["updatedDate"].replace(" ", "T")

        frontmatter = {
            "title": sanitize_frontmatter_text(item["title"]),
            "description": description,
            "pubDate": pub_iso,
            "updatedDate": updated_iso,
            "featuredImage": featured or DEFAULT_IMAGE,
        }

        write_mdx(PAGES_DIR / f"{item['slug']}.mdx", frontmatter, prepare_mdx_body(body))

        migrated_pages.append(
            {
                "slug": item["slug"],
                "title": frontmatter["title"],
                "description": description,
                "featuredImage": frontmatter["featuredImage"],
                "content": prepare_mdx_body(body),
            }
        )

        for match in re.findall(
            rf"https?://(?:www\.)?interieurguy\.nl/wp-content/uploads/[^\s\"'<>]+",
            body,
        ):
            image_urls.add(match)

    AUTHORS_DIR.mkdir(parents=True, exist_ok=True)
    for login, author in data["authors"].items():
        safe = re.sub(r"[^\w\-]", "-", login)
        (AUTHORS_DIR / f"{safe}.json").write_text(
            json.dumps(author, indent=2), encoding="utf-8"
        )

    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    (CATEGORIES_DIR / "categories.json").write_text(
        json.dumps(list(data["categories"].values()), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    (TAGS_DIR / "tags.json").write_text(
        json.dumps(list(data["tags"].values()), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_blog_posts_json(migrated_posts)
    write_pages_json(migrated_pages, existing_products)

    print(f"Downloading {len(image_urls)} images...")
    download_jobs = []
    for url in sorted(image_urls):
        if "/wp-content/uploads/" not in url:
            continue
        rel = url.split("/wp-content/uploads/", 1)[1]
        dest = PUBLIC_IMAGES / rel
        download_jobs.append((url, dest))

    success = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(download_image, url, dest): (url, dest)
            for url, dest in download_jobs
        }
        for future in as_completed(futures):
            if future.result():
                success += 1

    print(f"Downloaded {success}/{len(download_jobs)} images")

    summary = {
        "posts": len(posts_raw),
        "pages": len(pages_raw),
        "products_preserved": len(existing_products),
        "authors": len(data["authors"]),
        "categories": len(data["categories"]),
        "tags": len(data["tags"]),
        "images": success,
        "nav_items": len(data["nav_items"]),
    }
    (ROOT / "migration-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    migrate()
