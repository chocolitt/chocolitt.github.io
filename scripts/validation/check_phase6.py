#!/usr/bin/env python3
"""Expanded pre-launch QA for the generated static site."""

from __future__ import annotations

import argparse
from collections import defaultdict
import email.utils
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


SITE = "https://www.daniellitt.com"
PRESERVED_STANDALONE = {
    "/fermat_fano_real_mesh_web.html",
    "/published-paper-reviews.html",
}
EXTRA_SITEMAP_PATHS = {
    "/artifacts",
    "/fermat_fano_real_mesh_web.html",
    "/published-paper-reviews.html",
    "/mat1101.html",
    "/mat1190hs.html",
    "/mat445.html",
    "/mat445_winter2026.html",
}
KNOWN_LEGACY_DEAD_LINKS = {
    "/How-would-a-society-run-by-mathematicians-look-like",
    "/virtual-office-hours",
    "/virtual-tea",
}
EXPECTED_DECORATIVE_IMAGES = {
    ("/contact", "/assets/squarespace/40d07a82fa49-image-asset.webp"),
    ("/expository-notes", "/assets/squarespace/edeaca155c8f-image-asset.webp"),
    ("/expository-notes", "/assets/squarespace/bf12674a0d68-image-asset.webp"),
    ("/nonmathematical-writing", "/assets/squarespace/5965c094d8d5-cosmas.webp"),
    ("/nonmathematical-writing", "/assets/squarespace/2f5c2c8cbfbd-aristotlespheres.webp"),
    ("/open-questions", "/assets/squarespace/0d03d3058320-keplermusic.webp"),
    ("/talks-and-expository-work", "/assets/squarespace/8d1aab1c96b5-Z3.webp"),
    ("/talks-and-expository-work", "/assets/squarespace/c8c71c92862d-image-asset.webp"),
    ("/teaching", "/assets/squarespace/c04fb0bb8140-image-asset.webp"),
    ("/teaching", "/assets/squarespace/52d8beda1b95-image-asset.webp"),
}
EXPECTED_VISUAL_FIDELITY = {
    "/blog": {"feed-item": 20, "blog-sidebar": 1, "media-slide": 16},
    "/blog/2026/8/11/the-end-of-mathematics": {"blog-sidebar": 1, "media-slide": 16},
    "/blog/2026/2/20/mathematics-in-the-library-of-babel": {"blog-sidebar": 1},
    "/publications-and-preprints": {
        "media-publications": 1,
        "fidelity-grid--sidebar": 2,
        "publication-citation": 32,
    },
    "/teaching": {"media-teaching-portrait": 1, "media-teaching-divider": 1, "fidelity-grid--two": 2},
    "/about": {"media-about": 1},
    "/contact": {"media-contact": 1},
    "/talks-and-expository-work": {"media-talks-primary": 1, "media-talks-secondary": 1, "fidelity-grid--two": 2},
    "/expository-notes": {"media-expository-primary": 1, "media-expository-secondary": 1},
    "/nonmathematical-writing": {"media-prose-primary": 1, "media-prose-secondary": 1},
    "/open-questions": {"media-open-questions": 1},
    "/mat138h1": {"media-mat138": 1},
    "/agonize": {"media-poster": 1},
}
DOWNLOAD_EXTENSIONS = {
    ".blend", ".doc", ".docx", ".gif", ".jpg", ".jpeg", ".obj", ".pdf",
    ".png", ".tex", ".webp", ".xls", ".xlsx", ".zip",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.ids: list[str] = []
        self.headings: list[int] = []
        self.title_depth = 0
        self.title_text = ""
        self.main_count = 0
        self.html_lang = ""
        self.canonicals: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, object]] = []
        self.link_stack: list[dict[str, object]] = []
        self.images: list[dict[str, str]] = []
        self.iframes: list[dict[str, str]] = []
        self.buttons: list[dict[str, object]] = []
        self.button_stack: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.attrs.append((tag, values))
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.html_lang = values.get("lang", "")
        elif tag == "main":
            self.main_count += 1
        elif tag == "title":
            self.title_depth += 1
        elif len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
            self.headings.append(int(tag[1]))
        elif tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "a":
            link: dict[str, object] = {"attrs": values, "name": ""}
            self.links.append(link)
            self.link_stack.append(link)
        elif tag == "img":
            self.images.append(values)
            for link in self.link_stack:
                link["name"] = str(link["name"]) + " " + values.get("alt", "")
        elif tag == "iframe":
            self.iframes.append(values)
        elif tag == "button":
            button: dict[str, object] = {"attrs": values, "name": ""}
            self.buttons.append(button)
            self.button_stack.append(button)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        elif tag == "a" and self.link_stack:
            self.link_stack.pop()
        elif tag == "button" and self.button_stack:
            self.button_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_text += data
        for link in self.link_stack:
            link["name"] = str(link["name"]) + data
        for button in self.button_stack:
            button["name"] = str(button["name"]) + data


def expected_lines(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def output_for_path(dist: Path, path: str) -> Path:
    if path == "/":
        return dist / "index.html"
    relative = unquote(urlsplit(path).path).lstrip("/")
    direct = dist / relative
    return direct if direct.is_file() else direct / "index.html"


def page_path(dist: Path, page: Path) -> str:
    relative = page.relative_to(dist).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative.removesuffix("/index.html")
    return "/" + relative


def local_target(dist: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    return output_for_path(dist, parsed.path)


def meta_value(parser: PageParser, *, name: str = "", prop: str = "") -> list[str]:
    result = []
    for item in parser.meta:
        if name and item.get("name", "").casefold() == name.casefold():
            result.append(item.get("content", ""))
        if prop and item.get("property", "").casefold() == prop.casefold():
            result.append(item.get("content", ""))
    return result


def check_magic(path: Path) -> str | None:
    head = path.read_bytes()[:16]
    suffix = path.suffix.casefold()
    if suffix == ".pdf" and not head.startswith(b"%PDF"):
        return "PDF extension does not contain PDF data"
    if suffix == ".png" and not head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG extension does not contain PNG data"
    if suffix in {".jpg", ".jpeg"} and not head.startswith(b"\xff\xd8\xff"):
        return "JPEG extension does not contain JPEG data"
    if suffix == ".gif" and not head.startswith((b"GIF87a", b"GIF89a")):
        return "GIF extension does not contain GIF data"
    if suffix == ".webp" and not (head.startswith(b"RIFF") and head[8:12] == b"WEBP"):
        return "WebP extension does not contain WebP data"
    if suffix == ".woff2" and not head.startswith(b"wOF2"):
        return "WOFF2 extension does not contain WOFF2 data"
    if suffix == ".xls" and not head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "XLS extension does not contain an OLE workbook"
    if suffix == ".blend" and not head.startswith(b"BLENDER"):
        return "BLEND extension does not contain Blender data"
    if suffix in {".tex", ".obj"}:
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"{suffix} download is not valid UTF-8 text"
    return None


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("dist", type=Path, nargs="?", default=Path("dist"))
    argument_parser.add_argument("--report", type=Path)
    args = argument_parser.parse_args()
    dist = args.dist.resolve()
    validation = Path(__file__).resolve().parent
    failures: list[str] = []
    warnings: list[str] = []

    if not dist.is_dir():
        print(f"Missing build directory: {dist}", file=sys.stderr)
        return 2

    content_root = Path(__file__).resolve().parents[2] / "src/data"
    editorial_alt_text: dict[str, str] = json.loads(
        (Path(__file__).resolve().parents[1] / "migration/editorial-image-alts.json").read_text(encoding="utf-8")
    )
    if len(editorial_alt_text) != 49 or any(not value.strip() for value in editorial_alt_text.values()):
        failures.append("editorial alt-text inventory must contain exactly 49 non-empty alternatives")
    content_paths: dict[str, list[str]] = defaultdict(list)
    for collection in ("blog", "pages", "courses"):
        for source in (content_root / collection).glob("*.md"):
            source_text = source.read_text(encoding="utf-8")
            match = re.search(r"^legacyPath:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", source_text, flags=re.MULTILINE)
            if match:
                content_paths[match.group(1)].append(str(source.relative_to(content_root)))
    for legacy_path, sources in sorted(content_paths.items()):
        if len(sources) > 1:
            failures.append(f"duplicate content legacyPath {legacy_path}: {', '.join(sources)}")

    publications_source = (content_root / "publications.yaml").read_text(encoding="utf-8")
    if publications_source.count("            - title: |-") != 32:
        failures.append("structured publications source must contain exactly 32 records")
    for field in ("citation: |-", "abstract: |-"):
        if publications_source.count(field) != 32:
            failures.append(f"structured publications source must contain 32 {field[:-3]} fields")

    expected_squarespace = expected_lines(validation / "expected-squarespace-paths.txt")
    expected_sitemap = expected_squarespace | EXTRA_SITEMAP_PATHS
    sitemap_root = ET.parse(dist / "sitemap.xml").getroot()
    sitemap_namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = [node.text or "" for node in sitemap_root.findall("s:url/s:loc", sitemap_namespace)]
    sitemap_paths = {urlsplit(value).path.rstrip("/") or "/" for value in sitemap_urls}
    if len(sitemap_urls) != len(set(sitemap_urls)):
        failures.append("sitemap contains duplicate URLs")
    if sitemap_paths != expected_sitemap:
        failures.append(
            f"sitemap path mismatch: missing={sorted(expected_sitemap - sitemap_paths)} "
            f"extra={sorted(sitemap_paths - expected_sitemap)}"
        )
    for value in sitemap_urls:
        if not value.startswith(SITE + "/"):
            failures.append(f"sitemap URL is not canonical HTTPS: {value}")
        if not output_for_path(dist, urlsplit(value).path).is_file():
            failures.append(f"sitemap URL has no output: {value}")

    rss_root = ET.parse(dist / "rss.xml").getroot()
    rss_items = rss_root.findall("./channel/item")
    rss_links = [item.findtext("link", "") for item in rss_items]
    blog_paths = set()
    for source in (content_root / "blog").glob("*.md"):
        source_text = source.read_text(encoding="utf-8")
        match = re.search(r'^legacyPath:\s*"([^"]+)"', source_text, flags=re.MULTILINE)
        is_draft = bool(re.search(r"^draft:\s*true\s*$", source_text, flags=re.MULTILINE))
        if match and not is_draft:
            blog_paths.add(match.group(1))
    if {urlsplit(value).path for value in rss_links} != blog_paths:
        failures.append("RSS post paths do not exactly match the published Markdown posts")
    if len(rss_links) != len(set(rss_links)):
        failures.append("RSS contains duplicate post links")
    rss_dates = []
    for item in rss_items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        description = (item.findtext("description") or "").strip()
        if not title or not description or link != guid or not link.startswith(SITE + "/"):
            failures.append(f"invalid RSS item metadata: {link or title or '<empty>'}")
        try:
            rss_dates.append(email.utils.parsedate_to_datetime(item.findtext("pubDate") or ""))
        except (TypeError, ValueError):
            failures.append(f"invalid RSS publication date: {link}")
    if rss_dates != sorted(rss_dates, reverse=True):
        failures.append("RSS items are not reverse chronological")

    robots = (dist / "robots.txt").read_text(encoding="utf-8")
    if "Allow: /" not in robots or f"Sitemap: {SITE}/sitemap.xml" not in robots:
        failures.append("robots.txt does not allow crawling and advertise the canonical sitemap")

    html_pages = sorted(dist.rglob("*.html"))
    parsed_pages: dict[Path, PageParser] = {}
    internal_references = 0
    download_references: set[str] = set()
    empty_alt_images = 0
    seen_decorative_images: set[tuple[str, str]] = set()
    seen_editorial_alt_text: set[str] = set()
    for page in html_pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        parser = PageParser()
        parser.feed(text)
        parser.close()
        parsed_pages[page] = parser
        path = page_path(dist, page)

        if len(parser.ids) != len(set(parser.ids)):
            duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
            failures.append(f"{path}: duplicate IDs {duplicates}")
        for previous, current in zip(parser.headings, parser.headings[1:]):
            if path not in PRESERVED_STANDALONE and current > previous + 1:
                failures.append(f"{path}: heading level skips from h{previous} to h{current}")

        for tag, attrs in parser.attrs:
            for key in ("href", "src", "poster"):
                value = attrs.get(key, "")
                if not value:
                    continue
                if "http://www.daniellitt.com" in value or "http://daniellitt.com" in value:
                    failures.append(f"{path}: old insecure internal URL remains: {value}")
                if key in {"src", "poster"} and value.startswith("http://"):
                    failures.append(f"{path}: mixed-content resource: {value}")
                target = local_target(dist, value)
                if target is not None:
                    internal_references += 1
                    parsed = urlsplit(value)
                    if parsed.path not in KNOWN_LEGACY_DEAD_LINKS and not target.is_file():
                        failures.append(f"{path}: missing internal target {value}")
                    if parsed.fragment and target.suffix == ".html" and target.is_file():
                        target_parser = parsed_pages.get(target)
                        if target_parser is None:
                            target_parser = PageParser()
                            target_parser.feed(target.read_text(encoding="utf-8", errors="replace"))
                            target_parser.close()
                        if unquote(parsed.fragment) not in target_parser.ids:
                            failures.append(f"{path}: missing fragment target {value}")
                if target is not None and urlsplit(value).path.casefold().endswith(tuple(DOWNLOAD_EXTENSIONS)):
                    download_references.add(unquote(urlsplit(value).path).lstrip("/"))

        for image in parser.images:
            image_src = image.get("src", "")
            if "alt" not in image:
                failures.append(f"{path}: image is missing an alt attribute: {image_src}")
            elif not image.get("alt", "").strip():
                empty_alt_images += 1
                image_key = (path, image_src)
                if image_key in EXPECTED_DECORATIVE_IMAGES:
                    seen_decorative_images.add(image_key)
                else:
                    failures.append(f"{path}: image has an unapproved empty alt attribute: {image_src}")
            if image_src in editorial_alt_text:
                seen_editorial_alt_text.add(image_src)
                if image.get("alt", "") != editorial_alt_text[image_src]:
                    failures.append(f"{path}: editorial alt text changed for {image_src}")
        for iframe in parser.iframes:
            if not iframe.get("title", "").strip():
                failures.append(f"{path}: iframe is missing a title: {iframe.get('src', '')}")
        for link in parser.links:
            attrs = link["attrs"]
            assert isinstance(attrs, dict)
            if attrs.get("href") and not (
                str(link["name"]).strip() or attrs.get("aria-label", "").strip() or attrs.get("title", "").strip()
            ):
                failures.append(f"{path}: link has no accessible name: {attrs.get('href')}")
        for button in parser.buttons:
            attrs = button["attrs"]
            assert isinstance(attrs, dict)
            if not (str(button["name"]).strip() or attrs.get("aria-label", "").strip() or attrs.get("title", "").strip()):
                failures.append(f"{path}: button has no accessible name")

        if path not in PRESERVED_STANDALONE:
            if path in expected_squarespace and 'class="astro-code' in text:
                failures.append(f"{path}: imported HTML was rendered as an accidental Markdown code block")
            if parser.html_lang != "en":
                failures.append(f"{path}: missing html lang=en")
            if not parser.title_text.strip():
                failures.append(f"{path}: empty title")
            if parser.main_count != 1:
                failures.append(f"{path}: expected one main landmark, found {parser.main_count}")
            if parser.headings.count(1) != 1:
                failures.append(f"{path}: expected one h1, found {parser.headings.count(1)}")
            if path != "/404" and len(parser.canonicals) != 1:
                failures.append(f"{path}: expected one canonical URL, found {len(parser.canonicals)}")
            expected_canonical_path = "/404" if path == "/404.html" else (path if path != "/" else "/")
            if parser.canonicals and parser.canonicals[0] != SITE + expected_canonical_path:
                failures.append(f"{path}: incorrect canonical URL {parser.canonicals[0]}")
            if len(meta_value(parser, name="description")) != 1 or not meta_value(parser, name="description")[0].strip():
                failures.append(f"{path}: missing meta description")
            if meta_value(parser, name="robots"):
                failures.append(f"{path}: production page unexpectedly contains robots noindex metadata")
            for prop in ("og:title", "og:description", "og:url", "og:image"):
                values = meta_value(parser, prop=prop)
                if len(values) != 1 or not values[0].strip():
                    failures.append(f"{path}: missing {prop} metadata")
            if meta_value(parser, name="twitter:card") != ["summary_large_image"]:
                failures.append(f"{path}: missing Twitter summary-card metadata")
            if not meta_value(parser, name="viewport"):
                failures.append(f"{path}: missing viewport metadata")

        if path == "/publications-and-preprints":
            if text.count('class="publication-abstract"') != 32 or text.count("<summary>Abstract</summary>") != 32:
                failures.append(f"{path}: expected 32 native collapsible abstract controls")
            for delimiter in (r"\(", r"\)", r"\[", r"\]", "$"):
                expected_count = publications_source.count(delimiter)
                actual_count = text.split("<article", 1)[-1].split("</article>", 1)[0].count(delimiter)
                if actual_count != expected_count:
                    failures.append(
                        f"{path}: TeX delimiter {delimiter!r} count changed "
                        f"from {expected_count} in source to {actual_count} in output"
                    )

        for marker, expected_count in EXPECTED_VISUAL_FIDELITY.get(path, {}).items():
            actual_count = sum(
                marker in attrs.get("class", "").split()
                for _, attrs in parser.attrs
            )
            if actual_count != expected_count:
                failures.append(
                    f"{path}: expected visual-fidelity marker {marker!r} "
                    f"{expected_count} time(s), found {actual_count}"
                )

    public_files = [path for path in dist.rglob("*") if path.is_file()]
    oversized = [path for path in public_files if path.stat().st_size >= 100_000_000]
    if oversized:
        failures.append("files exceed GitHub's 100 MB limit: " + ", ".join(str(path.relative_to(dist)) for path in oversized))
    checked_binary_files = 0
    for path in public_files:
        if path.stat().st_size == 0:
            failures.append(f"empty output file: {path.relative_to(dist)}")
        if path.suffix.casefold() in DOWNLOAD_EXTENSIONS | {".woff2"}:
            checked_binary_files += 1
            issue = check_magic(path)
            if issue:
                failures.append(f"{path.relative_to(dist)}: {issue}")
    for relative in sorted(download_references):
        target = dist / relative
        if not target.is_file():
            failures.append(f"download reference has no file: /{relative}")

    missing_decorative_images = EXPECTED_DECORATIVE_IMAGES - seen_decorative_images
    if missing_decorative_images:
        failures.append(
            "approved decorative-image inventory is incomplete: "
            + ", ".join(f"{path} {src}" for path, src in sorted(missing_decorative_images))
        )
    missing_editorial_alt_text = set(editorial_alt_text) - seen_editorial_alt_text
    if missing_editorial_alt_text:
        failures.append(
            "editorial alt-text inventory is incomplete: " + ", ".join(sorted(missing_editorial_alt_text))
        )
    if empty_alt_images:
        warnings.append(
            f"{empty_alt_images} images intentionally retain empty alt attributes after editorial sign-off"
        )
    warnings.append(
        "The three documented dead/private Squarespace links and one historic file:/// course link are preserved source artifacts"
    )
    warnings.append(
        "GitHub Pages cannot return RSS XML specifically for the legacy /blog?format=rss query; /rss.xml is canonical"
    )

    result = {
        "passed": not failures,
        "content_legacy_paths": len(content_paths),
        "squarespace_paths": len(expected_squarespace),
        "sitemap_urls": len(sitemap_urls),
        "rss_items": len(rss_items),
        "html_pages": len(html_pages),
        "internal_references": internal_references,
        "download_references": len(download_references),
        "checked_download_and_media_files": checked_binary_files,
        "empty_alt_images": empty_alt_images,
        "editorial_alt_images": len(seen_editorial_alt_text),
        "failures": failures,
        "warnings": warnings,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"FAILED: {len(failures)} Phase 6 issue(s)")
        return 1
    print(
        f"PASS: {len(html_pages)} HTML pages, {len(sitemap_urls)} sitemap URLs, {len(rss_items)} RSS items, "
        f"{internal_references} internal references, {len(download_references)} linked downloads, "
        f"and {checked_binary_files} download/media files"
    )
    for warning in warnings:
        print(f"KNOWN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
