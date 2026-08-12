#!/usr/bin/env python3
"""Check internal links and required migration artifacts in an Astro build."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


# These are live Squarespace navigation routes whose content has not yet been
# converted in the deliberately partial Phase 3 prototype. They remain links at
# their exact production paths and must become real build outputs before launch.
PENDING_SQUARESPACE_ROUTES = {
    "/about",
    "/contact",
    "/expository-notes",
    "/nonmathematical-writing",
    "/open-questions",
    "/publications-and-preprints",
    "/talks-and-expository-work",
}


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
    pending: set[str] = set()
    checked = 0
    for page in dist.rglob("*.html"):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for link in parser.links:
            if link.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "http://", "https://", "//")):
                continue
            checked += 1
            path = unquote(urlsplit(link).path)
            if path in PENDING_SQUARESPACE_ROUTES:
                pending.add(path)
            elif not target_exists(dist, link):
                failures.append((page.relative_to(dist), link))

    required = [
        "index.html",
        "blog/2026/2/20/mathematics-in-the-library-of-babel/index.html",
        "teaching/mat445-winter-2026/index.html",
        "mat445_winter2026.html",
        "mat1101.html",
        "mat1190hs.html",
        "mat445.html",
        "fermat_fano_real_mesh_web.html",
        "published-paper-reviews.html",
        "AG_notes_1.pdf",
        "AG_notes_1.tex",
        "Hartshorne III.png",
        "MAT445H1_ Representation Theory 2026.docx - Google Docs (2).pdf",
        "grassmannian_frobenius_counterexample.pdf",
        "jacob_mathilde_notes.pdf",
        "s/CV-Daniel-Litt-akmg.pdf",
        "rss.xml",
        "sitemap.xml",
        "robots.txt",
        "images/site/portrait.jpg",
        "images/site/publications.png",
    ]
    for relative in required:
        if not (dist / relative).is_file():
            failures.append((Path("<required>"), f"/{relative}"))

    for relative in [
        "mat1101.html",
        "mat1190hs.html",
        "mat445.html",
        "mat445_winter2026.html",
        "fermat_fano_real_mesh_web.html",
        "published-paper-reviews.html",
    ]:
        text = (dist / relative).read_text(encoding="utf-8", errors="replace").lower()
        if "http-equiv=\"refresh\"" in text or "http-equiv='refresh'" in text:
            failures.append((Path(relative), "preserved page must not be a redirect"))

    if failures:
        for page, link in failures:
            print(f"BROKEN {page}: {link}")
        print(f"FAILED: {len(failures)} broken or missing targets")
        return 1

    print(f"PASS: {checked} internal href/src references and {len(required)} required outputs")
    if pending:
        print(
            "PENDING PHASE 5: "
            f"{len(pending)} linked Squarespace routes still require conversion at their existing paths: "
            + ", ".join(sorted(pending))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
