#!/usr/bin/env python3
"""Verify internal links in built Astro site."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"

    subprocess.run(["npm", "run", "build"], cwd=root, check=True)

    html_files = list(dist.rglob("*.html"))
    hrefs: set[str] = set()

    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        for href in re.findall(r'href="(/[^"#?]*/?)"', text):
            if href.startswith("/images/"):
                continue
            hrefs.add(href.rstrip("/") + ("/" if not href.endswith("/") else ""))

    missing: list[str] = []
    for href in sorted(hrefs):
        path = href.lstrip("/")
        target = dist / path
        index_target = dist / path / "index.html"
        if not target.exists() and not index_target.exists():
            missing.append(href)

    if missing:
        print(f"FAIL: {len(missing)} broken internal links")
        for link in missing[:30]:
            print(f"  - {link}")
        raise SystemExit(1)

    print(f"OK: {len(hrefs)} internal links verified across {len(html_files)} pages")


if __name__ == "__main__":
    main()
