#!/usr/bin/env python3
"""Exercise every sitemap route and linked local download over HTTP."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DOWNLOAD_EXTENSIONS = {
    ".blend", ".doc", ".docx", ".gif", ".jpg", ".jpeg", ".obj", ".pdf",
    ".png", ".tex", ".webp", ".xls", ".xlsx", ".zip",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.values.append(values[key] or "")


def request(url: str, method: str) -> tuple[int, str, str]:
    response = urlopen(Request(url, method=method), timeout=15)
    return response.status, response.headers.get_content_type(), response.geturl()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    parser.add_argument("base_url")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    dist = args.dist.resolve()
    base = args.base_url.rstrip("/") + "/"
    failures: list[str] = []

    sitemap_root = ET.parse(dist / "sitemap.xml").getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    paths = [urlsplit(node.text or "").path for node in sitemap_root.findall("s:url/s:loc", namespace)]
    route_results = []
    for path in paths:
        url = urljoin(base, quote(unquote(path).lstrip("/"), safe="/+._~-"))
        try:
            status, content_type, final_url = request(url, "GET")
            if status != 200 or content_type != "text/html":
                failures.append(f"route {path}: status={status}, content-type={content_type}")
            route_results.append({"path": path, "status": status, "content_type": content_type, "final_url": final_url})
        except (HTTPError, URLError, TimeoutError) as error:
            failures.append(f"route {path}: {error}")

    downloads: set[str] = set()
    for html in dist.rglob("*.html"):
        link_parser = LinkParser()
        link_parser.feed(html.read_text(encoding="utf-8", errors="replace"))
        for value in link_parser.values:
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
                continue
            if Path(unquote(parsed.path)).suffix.casefold() in DOWNLOAD_EXTENSIONS:
                downloads.add(unquote(parsed.path))

    download_results = []
    for path in sorted(downloads):
        url = urljoin(base, quote(path.lstrip("/"), safe="/+._~-"))
        try:
            status, content_type, final_url = request(url, "HEAD")
            if status != 200:
                failures.append(f"download {path}: status={status}")
            download_results.append(
                {"path": path, "status": status, "content_type": content_type, "final_url": final_url}
            )
        except (HTTPError, URLError, TimeoutError) as error:
            failures.append(f"download {path}: {error}")

    for special in ("rss.xml", "sitemap.xml", "robots.txt", "404.html"):
        try:
            status, content_type, final_url = request(urljoin(base, special), "GET")
            if status != 200:
                failures.append(f"special /{special}: status={status}")
            route_results.append(
                {"path": "/" + special, "status": status, "content_type": content_type, "final_url": final_url}
            )
        except (HTTPError, URLError, TimeoutError) as error:
            failures.append(f"special /{special}: {error}")

    result = {
        "passed": not failures,
        "base_url": base,
        "routes_checked": len(paths) + 4,
        "downloads_checked": len(downloads),
        "failures": failures,
        "routes": route_results,
        "downloads": download_results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {len(paths) + 4} HTTP routes and {len(downloads)} linked downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
