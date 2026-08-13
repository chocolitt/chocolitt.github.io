#!/usr/bin/env python3
"""Check internal links and required migration artifacts in an Astro build."""

from __future__ import annotations

import sys
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


# These links were already dead on the captured Squarespace site. They remain
# in the imported prose for historical fidelity, but they are not launch gaps.
KNOWN_LEGACY_DEAD_LINKS = {
    "/How-would-a-society-run-by-mathematicians-look-like",
    "/virtual-office-hours",
    "/virtual-tea",
}

VALIDATED_PAGES = [
    "index.html",
    "404.html",
    "artifacts/index.html",
    "blog/index.html",
    "blog/2026/2/20/mathematics-in-the-library-of-babel/index.html",
    "teaching/index.html",
    "mat1101.html",
    "mat1190hs.html",
    "mat445.html",
    "mat445_winter2026.html",
]

COURSE_LEGACY_PAGES = [
    "mat1101.html",
    "mat1190hs.html",
    "mat445.html",
    "mat445_winter2026.html",
]

COURSE_CONTENT_MARKERS = {
    "mat1101.html": [
        "Math 1101: Algebra II",
        "Matthew Bolan",
        "Unsolvability of the quintic",
        "April 2024",
    ],
    "mat1190hs.html": [
        "MAT1190HS: Algebraic Geometry",
        "Hartshorne III.7: The Serre Duality Theorem",
        "The final assessment will be held during the last week of class.",
    ],
    "mat445.html": [
        "Math 445: Representation Theory",
        "Austin Sun",
        "Representation theory of",
        "April 2024",
    ],
    "mat445_winter2026.html": [
        "MAT445H1: Representation Theory",
        "Alexander Mirabella",
        "Complete reducibility",
        "April 2026",
    ],
}

COURSE_LINK_MARKERS = {
    "mat1101.html": [
        "https://docs.google.com/document/d/1VqalmO2my3qDMDcL--DKraR3OxHp3xDW/edit",
        "mailto:daniel.litt@utoronto.ca",
        "mailto:matthew.bolan@mail.utoronto.ca",
    ],
    "mat1190hs.html": ["mailto:daniel.litt@utoronto.ca"],
    "mat445.html": [
        "https://docs.google.com/document/d/1sI4VzLsKw3JJ5EUgiFBbiCrnRnnGDN5X/edit",
        "mailto:daniel.litt@utoronto.ca",
        "mailto:austin.sun@mail.utoronto.ca",
        "https://www.overleaf.com/read/xcvknvrbmdbt#ad606c",
        "/jacob_mathilde_notes.pdf",
    ],
    "mat445_winter2026.html": [
        "/MAT445H1_%20Representation%20Theory%202026.docx%20-%20Google%20Docs%20%282%29.pdf",
        "mailto:daniel.litt@utoronto.ca",
        "mailto:alexander.mirabella@mail.utoronto.ca",
        "https://www.overleaf.com/read/xcvknvrbmdbt#ad606c",
    ],
}

PRESERVED_SHA256 = {
    "AG_notes_1.pdf": "812b57655a7e66fdd751285ad08b723412955f535d628ae3aa5b483a7804fd40",
    "AG_notes_1.tex": "7fb1665ddb8413fbbb1b8a17eaf3935297735be4736ef6f8b4fd21ea293d5a77",
    "Hartshorne III.png": "8268678a5236aabaed186e28e3cd9ca68ccedb475c62c8378faf6424f4227336",
    "MAT445H1_ Representation Theory 2026.docx - Google Docs (2).pdf":
        "e47ebcd2b3ea07754fade8337ebe3e8e448ed1f128a007607cbcb07fdec0e276",
    "grassmannian_frobenius_counterexample.pdf":
        "8b7d7fd450db762f246a38fab4a950561c690046e53c673bd628f986fe9d3f4e",
    "jacob_mathilde_notes.pdf": "57163cc8645611e42ec60889bfd65d847097c3b8c7843f06ceae385c3253c7f2",
    "fermat_fano_real_mesh_web.html":
        "dd870edce82a60ec9a36a8e3f380adcf6487dc3a1585df6d61dfdf4ff9dd50b0",
    "published-paper-reviews.html":
        "cef3cecdcb846c0027befaedb1abb8f48ed9f06f92bca7f865d7929079a7d1a6",
}

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
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self.headings.append(int(tag[1]))
        for key, value in attrs:
            if value and key == "id":
                self.ids.add(value)
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


def output_for_path(dist: Path, path: str) -> Path:
    if path == "/":
        return dist / "index.html"
    relative = unquote(path).lstrip("/")
    direct = dist / relative
    if direct.is_file():
        return direct
    return direct / "index.html"


def read_expected(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def detected_extension(path: Path) -> str:
    with path.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    if head.startswith(b"%PDF"):
        return ".pdf"
    return ""


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
    if not dist.is_dir():
        print(f"Missing build directory: {dist}", file=sys.stderr)
        return 2

    failures: list[tuple[Path, str]] = []
    known_dead_seen: set[str] = set()
    checked = 0
    for page in dist.rglob("*.html"):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for link in parser.links:
            if link.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "file:", "http://", "https://", "//")):
                continue
            checked += 1
            path = unquote(urlsplit(link).path)
            if path in KNOWN_LEGACY_DEAD_LINKS:
                known_dead_seen.add(path)
            elif not target_exists(dist, link):
                failures.append((page.relative_to(dist), link))

    validation_root = Path(__file__).resolve().parent
    expected_paths = read_expected(validation_root / "expected-squarespace-paths.txt")
    expected_comments = read_expected(validation_root / "expected-comment-paths.txt")
    expected_math = read_expected(validation_root / "expected-math-paths.txt")
    for path in sorted(expected_paths):
        output = output_for_path(dist, path)
        if not output.is_file():
            failures.append((Path("<expected-squarespace-path>"), path))
            continue
        text = output.read_text(encoding="utf-8", errors="replace")
        parser = LinkParser()
        parser.feed(text)
        if parser.headings.count(1) != 1:
            failures.append((output.relative_to(dist), f"expected exactly one h1; found {parser.headings.count(1)}"))
        for previous, current in zip(parser.headings, parser.headings[1:]):
            if current > previous + 1:
                failures.append((output.relative_to(dist), f"heading level skips from h{previous} to h{current}"))
        canonical = f'<link rel="canonical" href="https://www.daniellitt.com{path if path != "/" else "/"}">'
        if canonical not in text:
            failures.append((output.relative_to(dist), f"canonical URL does not preserve {path}"))
        if path in expected_comments and f'const urlId = "{path}";' not in text:
            failures.append((output.relative_to(dist), "FastComments urlId does not match the immutable post path"))
        has_mathjax = "tex-chtml.js" in text
        if path in expected_math and not has_mathjax:
            failures.append((output.relative_to(dist), "MathJax is missing from math-bearing imported content"))
        if path not in expected_math and has_mathjax:
            failures.append((output.relative_to(dist), "MathJax was loaded on a page without imported TeX"))

    asset_manifest = validation_root / "expected-squarespace-assets.sha256"
    asset_count = 0
    for line in asset_manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_sha, relative = line.split("  ", 1)
        asset_count += 1
        asset_path = dist / relative
        if not asset_path.is_file():
            failures.append((Path("<expected-squarespace-asset>"), f"/{relative}"))
        elif hashlib.sha256(asset_path.read_bytes()).hexdigest() != expected_sha:
            failures.append((Path(relative), "localized Squarespace asset checksum changed"))
        else:
            detected = detected_extension(asset_path)
            suffixes = {".jpg", ".jpeg"} if detected == ".jpg" else {detected}
            if detected and asset_path.suffix.lower() not in suffixes:
                failures.append((Path(relative), f"file extension does not match {detected} content"))

    required = [
        "index.html",
        "blog/2026/2/20/mathematics-in-the-library-of-babel/index.html",
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
        "images/site/portrait.webp",
        "images/site/publications.webp",
    ]
    for relative in required:
        if not (dist / relative).is_file():
            failures.append((Path("<required>"), f"/{relative}"))

    for relative in VALIDATED_PAGES:
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
        for link in parser.links:
            # Full post bodies on /blog rewrite fragment-only links to their
            # immutable post URLs in the page script, so they are not
            # same-document links at runtime.
            if relative != "blog/index.html" and link.startswith("#") and link[1:] not in parser.ids:
                failures.append((Path(relative), f"missing same-page fragment target: {link}"))

    for relative in [
        *COURSE_LEGACY_PAGES,
        "fermat_fano_real_mesh_web.html",
        "published-paper-reviews.html",
    ]:
        text = (dist / relative).read_text(encoding="utf-8", errors="replace").lower()
        if "http-equiv=\"refresh\"" in text or "http-equiv='refresh'" in text:
            failures.append((Path(relative), "preserved page must not be a redirect"))

    for relative in COURSE_LEGACY_PAGES:
        text = (dist / relative).read_text(encoding="utf-8", errors="replace")
        if 'class="course-shell shell page-content"' not in text:
            failures.append((Path(relative), "legacy course URL is not rendered by the shared Astro course layout"))
        for marker in COURSE_CONTENT_MARKERS[relative]:
            if marker not in text:
                failures.append((Path(relative), f"missing archived course content marker: {marker!r}"))
        for marker in COURSE_LINK_MARKERS[relative]:
            if marker not in text:
                failures.append((Path(relative), f"missing archived course link: {marker!r}"))
        canonical = f'<link rel="canonical" href="https://www.daniellitt.com/{relative}">'
        if canonical not in text:
            failures.append((Path(relative), "canonical URL does not preserve the legacy .html path"))

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8", errors="replace")
    for relative in COURSE_LEGACY_PAGES:
        url = f"https://www.daniellitt.com/{relative}"
        if f"<loc>{url}</loc>" not in sitemap:
            failures.append((Path("sitemap.xml"), f"missing legacy course URL: {url}"))

    for relative, expected in PRESERVED_SHA256.items():
        path = dist / relative
        if path.is_file():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                failures.append((Path(relative), f"checksum changed: {actual}"))

    css = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in (dist / "_astro").glob("*.css")
    ).lower()
    if "--muted:#707070" not in css:
        failures.append((Path("<styles>"), "expected accessible --muted color #707070"))
    for low_contrast_color in ["#777", "#888", "#7d7373"]:
        if low_contrast_color in css:
            failures.append((Path("<styles>"), f"low-contrast text color remains: {low_contrast_color}"))

    for page in dist.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        for hostname in ("images.squarespace-cdn.com", "static1.squarespace.com", "daniel-litt.squarespace.com"):
            if hostname in text:
                failures.append((page.relative_to(dist), f"unlocalized Squarespace dependency: {hostname}"))

    if failures:
        for page, link in failures:
            print(f"BROKEN {page}: {link}")
        print(f"FAILED: {len(failures)} broken or missing targets")
        return 1

    print(
        f"PASS: {len(expected_paths)} Squarespace paths, {asset_count} localized assets, "
        f"{len(expected_comments)} FastComments paths, {len(expected_math)} MathJax pages, "
        f"{checked} internal href/src references, and {len(PRESERVED_SHA256)} preserved checksums"
    )
    if known_dead_seen:
        print(
            "KNOWN LEGACY DEAD LINKS: "
            + ", ".join(sorted(known_dead_seen))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
