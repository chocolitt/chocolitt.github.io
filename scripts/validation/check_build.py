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

PHASE3_PAGES = [
    "index.html",
    "404.html",
    "artifacts/index.html",
    "blog/index.html",
    "blog/2026/2/20/mathematics-in-the-library-of-babel/index.html",
    "teaching/index.html",
    "teaching/mat445-winter-2026/index.html",
]

FORBIDDEN_PUBLIC_COPY = [
    "phase 3 prototype",
    "former github pages site",
    "content conversion",
    "original course-page address",
    "hidden in this build",
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.headings: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self.headings.append(int(tag[1]))
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

    for relative in PHASE3_PAGES:
        page = dist / relative
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        parser = LinkParser()
        parser.feed(text)
        if parser.headings.count(1) != 1:
            failures.append((Path(relative), f"expected exactly one h1; found {parser.headings.count(1)}"))
        for previous, current in zip(parser.headings, parser.headings[1:]):
            if current > previous + 1:
                failures.append((Path(relative), f"heading level skips from h{previous} to h{current}"))
        lower_text = text.lower()
        for phrase in FORBIDDEN_PUBLIC_COPY:
            if phrase in lower_text:
                failures.append((Path(relative), f"internal migration copy is public: {phrase!r}"))

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

    css = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in (dist / "_astro").glob("*.css")
    ).lower()
    if "--muted:#707070" not in css:
        failures.append((Path("<styles>"), "expected accessible --muted color #707070"))
    for low_contrast_color in ["#777", "#888", "#7d7373"]:
        if low_contrast_color in css:
            failures.append((Path("<styles>"), f"low-contrast text color remains: {low_contrast_color}"))

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
