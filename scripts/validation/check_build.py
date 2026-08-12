#!/usr/bin/env python3
"""Check internal links and required migration artifacts in an Astro build."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value and key in {"href", "src"}:
                self.links.append(value)


def target_exists(dist: Path, url: str) -> bool:
    path = unquote(urlsplit(url).path)
    if not path.startswith("/"):
        return True
    relative = path.lstrip("/")
    direct = dist / relative
    if direct.is_file():
        return True
    if direct.is_dir() and (direct / "index.html").is_file():
        return True
    return (dist / relative / "index.html").is_file()


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
    if not dist.is_dir():
        print(f"Missing build directory: {dist}", file=sys.stderr)
        return 2

    failures: list[tuple[Path, str]] = []
    checked = 0
    for page in dist.rglob("*.html"):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for link in parser.links:
            if link.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "http://", "https://", "//")):
                continue
            checked += 1
            if not target_exists(dist, link):
                failures.append((page.relative_to(dist), link))

    required = [
        "index.html",
        "blog/2026/2/20/mathematics-in-the-library-of-babel/index.html",
        "teaching/mat445-winter-2026/index.html",
        "mat445_winter2026.html",
        "fermat_fano_real_mesh_web.html",
        "published-paper-reviews.html",
        "rss.xml",
        "sitemap.xml",
        "robots.txt",
        "images/daniel-litt-social-card.png",
    ]
    for relative in required:
        if not (dist / relative).is_file():
            failures.append((Path("<required>"), f"/{relative}"))

    if failures:
        for page, link in failures:
            print(f"BROKEN {page}: {link}")
        print(f"FAILED: {len(failures)} broken or missing targets")
        return 1

    print(f"PASS: {checked} internal href/src references and {len(required)} required outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
