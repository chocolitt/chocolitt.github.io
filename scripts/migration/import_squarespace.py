#!/usr/bin/env python3
"""Convert the public Squarespace WXR export into Astro content.

The generated Markdown deliberately keeps the imported body as small,
semantic HTML. This preserves MathJax delimiters, embeds, captions, lists, and
links without retaining Squarespace's layout wrappers or inline styling.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit


NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "wp": "http://wordpress.org/export/1.2/",
}

SQUARESPACE_HOSTS = {
    "daniellitt.com",
    "www.daniellitt.com",
    "daniel-litt.squarespace.com",
    "images.squarespace-cdn.com",
    "static1.squarespace.com",
}

SITE_HOSTS = {
    "daniellitt.com",
    "www.daniellitt.com",
    "daniel-litt.squarespace.com",
    "chocolitt.github.io",
}

VOID_TAGS = {"br", "hr", "img", "source", "track", "wbr"}
PRESERVED_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "iframe",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
}
EDITORIAL_ALT_TEXT: dict[str, str] = json.loads(
    Path(__file__).with_name("editorial-image-alts.json").read_text(encoding="utf-8")
)

# Squarespace's WordPress export keeps media order but drops grid, crop,
# alignment, and intrinsic-size data. These small, named roles restore the
# visual treatment of affected images without retaining Squarespace's runtime.
CONTENT_MEDIA_ROLES: dict[str, list[str]] = {
    "publications and preprints": ["media-banner media-publications"],
    "teaching and service": ["media-ornament media-teaching-portrait", "media-banner media-teaching-divider"],
    "about": ["media-panel media-about"],
    "contact": ["media-banner media-contact"],
    "talk notes and slides": ["media-banner media-talks-primary", "media-banner media-talks-secondary"],
    "expository notes": ["media-banner media-expository-primary", "media-banner media-expository-secondary"],
    "non-mathematical writing": ["media-banner media-prose-primary", "media-banner media-prose-secondary"],
    "open questions": ["media-ornament media-open-questions"],
    "mat138h1": ["media-banner media-mat138"],
    "agonize": ["media-poster"],
    "adding": ["media-ornament", "media-poster"],
    "the end of mathematics": ["media-slide"] * 16,
}

# These pages were disabled in Squarespace when the initial public crawl was
# captured, but their complete bodies remain in the owner's WXR export. They
# are intentionally restored at their original URLs as historical archives.
RECOVERED_ARCHIVE_PATHS = {
    "/adding",
    "/biopsy",
    "/ccam",
    "/commutative-algebra",
    "/math-2250",
    "/rational-points",
    "/zazoom",
}


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def text_from_html(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_space(html.unescape(value).replace("\xa0", " "))


def description_for(item: ET.Element, body: str) -> str:
    excerpt = item.findtext("excerpt:encoded", namespaces=NAMESPACES) or ""
    description = text_from_html(excerpt) or text_from_html(body)
    if len(description) > 240:
        description = description[:237].rstrip(" ,;:-") + "…"
    return description or (item.findtext("title") or "Daniel Litt")


def published_iso(item: ET.Element) -> str:
    raw = item.findtext("pubDate") or ""
    if raw:
        value = parsedate_to_datetime(raw).astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    raw = item.findtext("wp:post_date", namespaces=NAMESPACES) or "1970-01-01 00:00:00"
    return raw.replace(" ", "T") + "Z"


def contains_math(body: str) -> bool:
    return bool(
        re.search(r"\\\(|\\\[|\$\$|\\begin\{|(?<!\\)\$(?!\s)[^$\n]+?(?<!\s)\$", body)
    )


ABSTRACT_HEADING_PATTERN = re.compile(
    r'<h3(?:\s+[^>]*)?>\s*\\\(\\qquad\\\)\+\s*Abstract\s*</h3>',
    flags=re.IGNORECASE,
)


def publication_abstracts(value: str, title: str) -> str:
    """Restore the publications page's collapsed abstract controls.

    Squarespace used an ``+ Abstract`` heading followed by either a blockquote
    or plain text. Wrapping the abstract body in a raw HTML container both
    restores the disclosure interaction and prevents Markdown from consuming
    TeX backslashes inside the body.
    """
    if title != "Publications and Preprints":
        return value

    def compact(body: str) -> str:
        body = re.sub(r"^(?:<p>\s*</p>\s*)+", "", body.strip(), flags=re.IGNORECASE)
        body = re.sub(r"(?:\s*<p>\s*</p>)+$", "", body, flags=re.IGNORECASE)
        return normalize_space(body)

    def quoted(match: re.Match[str]) -> str:
        body = compact(match.group(1))
        return (
            '<details class="publication-abstract"><summary>Abstract</summary>'
            f'<blockquote><div class="publication-abstract-body">{body}</div></blockquote></details>'
        )

    quoted_pattern = re.compile(
        ABSTRACT_HEADING_PATTERN.pattern + r"\s*<blockquote>(.*?)</blockquote>",
        flags=re.DOTALL | re.IGNORECASE,
    )
    value, quoted_count = quoted_pattern.subn(quoted, value)

    def unquoted(match: re.Match[str]) -> str:
        body = compact(match.group(1))
        return (
            '<details class="publication-abstract"><summary>Abstract</summary>'
            f'<div class="publication-abstract-body">{body}</div></details>'
        )

    unquoted_pattern = re.compile(
        ABSTRACT_HEADING_PATTERN.pattern + r"\s*(.*?)(?=\s*<p>•|\s*<h2>|\Z)",
        flags=re.DOTALL | re.IGNORECASE,
    )
    value, unquoted_count = unquoted_pattern.subn(unquoted, value)
    if quoted_count + unquoted_count != 32:
        raise SystemExit(
            "Expected 32 collapsible publication abstracts, found "
            f"{quoted_count + unquoted_count}"
        )
    return value


H2_PATTERN = re.compile(r"<h2(?:\s+[^>]*)?>.*?</h2>", flags=re.DOTALL | re.IGNORECASE)


def page_h2_sections(value: str) -> tuple[str, list[tuple[str, str]]]:
    """Split rendered page HTML into its prefix and intact h2-led sections."""
    matches = list(H2_PATTERN.finditer(value))
    if not matches:
        return value, []
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(value)
        name = text_from_html(match.group(0)).casefold()
        sections.append((name, value[match.start() : end].strip()))
    return value[: matches[0].start()].strip(), sections


def fidelity_grid(blocks: list[str], modifier: str) -> str:
    sections = "".join(f'<section class="fidelity-section">{block}</section>' for block in blocks)
    return f'<div class="fidelity-grid fidelity-grid--{modifier}">{sections}</div>'


def detach_media(block: str, media_class: str) -> tuple[str, str]:
    pattern = re.compile(
        rf'\s*(<img\b[^>]*\b{re.escape(media_class)}\b[^>]*/>)\s*$',
        flags=re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(block)
    if not match:
        raise SystemExit(f"Could not find {media_class!r} at the expected page-section boundary")
    return block[: match.start()].strip(), match.group(1)


def permanent_page_layout(value: str, title: str) -> str:
    """Rebuild the few permanent-page grids omitted by the WXR export."""
    key = normalize_space(title).casefold()
    if key not in {"teaching and service", "talk notes and slides", "publications and preprints"}:
        return value

    prefix, named_sections = page_h2_sections(value)
    section_names = [name for name, _ in named_sections]
    blocks = {name: block for name, block in named_sections}

    if key == "teaching and service":
        expected = ["teaching", "mentorship, etc.", "seminars", "conferences"]
        if section_names != expected:
            raise SystemExit(f"Unexpected Teaching section order: {section_names}")
        mentorship, divider = detach_media(blocks["mentorship, etc."], "media-teaching-divider")
        return "\n\n".join(
            [
                prefix,
                fidelity_grid([blocks["teaching"], mentorship], "two"),
                divider,
                fidelity_grid([blocks["seminars"], blocks["conferences"]], "two"),
            ]
        )

    if key == "talk notes and slides":
        expected = ["selected notes for talks", "for general audiences", "selected older notes", "miscellaneous"]
        if section_names != expected:
            raise SystemExit(f"Unexpected Talks section order: {section_names}")
        general, divider = detach_media(blocks["for general audiences"], "media-talks-secondary")
        return "\n\n".join(
            [
                prefix,
                fidelity_grid([blocks["selected notes for talks"], general], "two"),
                divider,
                fidelity_grid([blocks["selected older notes"], blocks["miscellaneous"]], "two"),
            ]
        )

    expected = [
        "my current research program",
        "papers on arithmetic and topology of algebraic varieties",
        "writing on ai",
        "classical algebraic geometry",
        "miscellaneous",
        "vanishing and positivity",
        "dynamics",
        "the grothendieck ring of varieties",
    ]
    if section_names != expected:
        raise SystemExit(f"Unexpected Publications section order: {section_names}")
    return "\n\n".join(
        [
            prefix,
            fidelity_grid(
                [
                    blocks["my current research program"],
                    blocks["papers on arithmetic and topology of algebraic varieties"] + blocks["writing on ai"],
                ],
                "sidebar",
            ),
            fidelity_grid(
                [
                    blocks["classical algebraic geometry"],
                    "".join(
                        blocks[name]
                        for name in [
                            "miscellaneous",
                            "vanishing and positivity",
                            "dynamics",
                            "the grothendieck ring of varieties",
                        ]
                    ),
                ],
                "sidebar",
            ),
        ]
    )


def display_title_for(body: str, fallback: str) -> str:
    match = re.search(r"<h1(?:\s+[^>]*)?>(.*?)</h1>", body, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return fallback
    # Inline emphasis spans often split a single word (for example the
    # AGONIZE acrostic), so strip tags without inserting artificial spaces.
    return normalize_space(html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).replace("\xa0", " "))


def safe_filename(value: str) -> str:
    value = unquote(value).replace("\x00", "")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value or "asset"


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
    return path.suffix.lower()


def normalized_asset_key(url: str) -> tuple[str, str]:
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        url = "https://www.daniellitt.com" + url
    parsed = urlsplit(html.unescape(url))
    return parsed.netloc.lower(), unquote(parsed.path)


@dataclass(frozen=True)
class Asset:
    url: str
    sha256: str
    source: Path
    size: int


class AssetCatalog:
    def __init__(self, csv_path: Path, workspace_root: Path, public_root: Path) -> None:
        self.public_root = public_root
        self.by_url: dict[str, Asset] = {}
        self.by_key: dict[tuple[str, str], list[Asset]] = {}
        self.used: dict[str, Asset] = {}
        self.unresolved: set[str] = set()
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row["status"] != "200" or not row["local_path"]:
                    continue
                source = workspace_root / row["local_path"]
                asset = Asset(
                    url=row["asset_url"],
                    sha256=row["sha256"],
                    source=source,
                    size=int(row["size_bytes"] or 0),
                )
                self.by_url[html.unescape(asset.url)] = asset
                self.by_key.setdefault(normalized_asset_key(asset.url), []).append(asset)

    def find(self, url: str) -> Asset | None:
        clean = html.unescape(url)
        if clean in self.by_url:
            return self.by_url[clean]
        candidates = self.by_key.get(normalized_asset_key(clean), [])
        return max(candidates, key=lambda candidate: candidate.size, default=None)

    def localize(self, url: str) -> str:
        if not url or url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
            return url
        if url.startswith("//"):
            url = "https:" + url
        parsed = urlsplit(html.unescape(url))
        host = parsed.netloc.lower()
        if not host and parsed.path.startswith("/s/"):
            absolute = "https://www.daniellitt.com" + url
            asset = self.find(absolute)
            if not asset:
                self.unresolved.add(url)
                return url
            public_path = quote(unquote(parsed.path), safe="/-._~")
            self.used[unquote(parsed.path).lstrip("/")] = asset
            return urlunsplit(("", "", public_path, "", parsed.fragment))
        if host in SITE_HOSTS and not parsed.path.startswith("/s/"):
            if (parsed.path or "/") == "/" and parsed.fragment.startswith("/"):
                return parsed.fragment
            path = parsed.path or "/"
            return urlunsplit(("", "", path, parsed.query, parsed.fragment))
        if host not in SQUARESPACE_HOSTS:
            return url
        asset = self.find(url)
        if not asset:
            self.unresolved.add(url)
            return url
        if parsed.path.startswith("/s/"):
            public_path = quote(unquote(parsed.path), safe="/-._~")
            destination = unquote(parsed.path).lstrip("/")
        else:
            original = Path(unquote(parsed.path)).name
            stem = safe_filename(Path(original).stem)
            basename = stem + detected_extension(asset.source)
            destination = f"assets/squarespace/{asset.sha256[:12]}-{basename}"
            public_path = "/" + quote(destination, safe="/-._~")
        self.used[destination] = asset
        return urlunsplit(("", "", public_path, "", parsed.fragment))

    def copy_used(self) -> tuple[int, int]:
        bytes_copied = 0
        for relative, asset in sorted(self.used.items()):
            if not asset.source.is_file():
                raise SystemExit(f"Missing inventoried asset: {asset.source}")
            destination = self.public_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_file():
                current = hashlib.sha256(destination.read_bytes()).hexdigest()
                if current == asset.sha256:
                    continue
            shutil.copy2(asset.source, destination)
            copied = hashlib.sha256(destination.read_bytes()).hexdigest()
            if copied != asset.sha256:
                raise SystemExit(f"Checksum mismatch after copying {destination}")
            bytes_copied += destination.stat().st_size
        return len(self.used), bytes_copied


@dataclass
class Node:
    tag: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)


class TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        node = Node(tag=tag, attrs={key.lower(): value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag=tag.lower(), attrs={key.lower(): value or "" for key, value in attrs})
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def caption_markup(match: re.Match[str]) -> str:
    shortcode_attrs = match.group(1)
    inner = match.group(2)
    image_match = re.search(r"<img\b[^>]*>", inner, flags=re.DOTALL | re.IGNORECASE)
    if not image_match:
        return inner
    caption = text_from_html(inner[image_match.end() :])
    visible = html.escape(caption)
    width_match = re.search(r'\bwidth=["\']?(\d+)', shortcode_attrs, flags=re.IGNORECASE)
    width = int(width_match.group(1)) if width_match else 0
    width_attr = f' data-imported-width="{min(width, 4000)}"' if width > 0 else ""
    return f"<figure{width_attr}>{image_match.group(0)}<figcaption>{visible}</figcaption></figure>"


class SemanticRenderer:
    def __init__(self, assets: AssetCatalog, title: str) -> None:
        self.assets = assets
        self.title = normalize_space(title).casefold()
        self.seen_h1 = False
        self.used_ids: set[str] = set()
        self.image_index = 0
        self.media_roles = CONTENT_MEDIA_ROLES.get(self.title, [])

    def unique_id(self, value: str) -> str:
        """Keep imported fragment targets valid while preventing duplicate IDs."""
        base = value.lstrip("#")
        candidate = base
        suffix = 2
        while candidate in self.used_ids:
            candidate = f"{base}-{suffix}"
            suffix += 1
        self.used_ids.add(candidate)
        return candidate

    def node_text(self, node: Node) -> str:
        values: list[str] = []
        for child in node.children:
            values.append(child if isinstance(child, str) else self.node_text(child))
        return normalize_space("".join(values))

    def chart(self, node: Node) -> str:
        raw = html.unescape(node.attrs.get("data-settings", ""))
        try:
            settings = json.loads(raw)
            table = settings["dataTable"]
            values = [float(row[0]) for row in table["data"]]
            labels = [str(label) for label in table["sampleLabels"]]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return self.children(node)
        maximum = max(values) or 1
        width, height, pad = 760, 330, 36
        plot_width, plot_height = width - 2 * pad, height - 2 * pad
        points = []
        for index, value in enumerate(values):
            x = pad + (plot_width * index / max(len(values) - 1, 1))
            y = pad + plot_height * (1 - value / maximum)
            points.append(f"{x:.1f},{y:.1f}")
        title = html.escape(str(settings.get("title") or "Chart"))
        caption = html.escape(str(settings.get("caption") or ""))
        label_rows = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{value:g}</td></tr>"
            for label, value in zip(labels, values)
        )
        return (
            f'<figure class="imported-chart"><h2>{title}</h2>'
            f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
            f'<polyline points="{" ".join(points)}" fill="none" stroke="currentColor" stroke-width="3" />'
            "</svg>"
            f'<details><summary>Chart data</summary><table><thead><tr><th>Edges</th><th>Graphs</th></tr></thead>'
            f"<tbody>{label_rows}</tbody></table></details><figcaption>{caption}</figcaption></figure>"
        )

    def children(self, node: Node) -> str:
        return "".join(self.render(child) for child in node.children)

    def render(self, child: Node | str) -> str:
        if isinstance(child, str):
            return html.escape(child, quote=False).replace("\xa0", " ")
        tag = child.tag or ""
        classes = set(child.attrs.get("class", "").split())
        if tag in {"script", "canvas"}:
            return ""
        if tag == "div" and "chart-block-container" in classes:
            return self.chart(child)
        if tag in {"div", "span"}:
            content = self.children(child)
            if any("gallery" in value for value in classes):
                return f'<div class="imported-gallery">{content}</div>'
            return content
        if tag not in PRESERVED_TAGS:
            return self.children(child)
        if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            if tag == "h1" and not self.seen_h1:
                self.seen_h1 = True
                return ""
            level = int(tag[1])
            level = 2 if level <= 3 else min(level - 1, 6)
            tag = f"h{level}"
        attrs: dict[str, str] = {}
        if tag == "a":
            href = child.attrs.get("href", "")
            if href:
                attrs["href"] = self.assets.localize(href)
            anchor_id = child.attrs.get("id") or child.attrs.get("name")
            if anchor_id:
                attrs["id"] = self.unique_id(anchor_id)
        elif tag == "img":
            attrs["src"] = self.assets.localize(child.attrs.get("src", ""))
            attrs["alt"] = EDITORIAL_ALT_TEXT.get(
                attrs["src"], normalize_space(child.attrs.get("alt", ""))
            )
            attrs["loading"] = "lazy"
            role = self.media_roles[self.image_index] if self.image_index < len(self.media_roles) else ""
            attrs["class"] = normalize_space(f"imported-media {role}")
            self.image_index += 1
        elif tag == "iframe":
            source = child.attrs.get("src", "")
            if source.startswith("//"):
                source = "https:" + source
            attrs = {
                "src": source,
                "title": normalize_space(child.attrs.get("title", "")) or "Embedded media",
                "loading": "lazy",
            }
            for key in ("width", "height", "allow", "allowfullscreen"):
                if key in child.attrs:
                    attrs[key] = child.attrs[key] or key
            if attrs.get("width", "").isdigit() and attrs.get("height", "").isdigit():
                attrs["style"] = f"aspect-ratio: {attrs['width']} / {attrs['height']}"
        elif tag == "figure" and child.attrs.get("data-imported-width", "").isdigit():
            width = min(int(child.attrs["data-imported-width"]), 4000)
            attrs["class"] = "imported-figure"
            attrs["style"] = f"--media-width: {width}px"
        else:
            for key in ("id", "colspan", "rowspan"):
                if child.attrs.get(key):
                    attrs[key] = self.unique_id(child.attrs[key]) if key == "id" else child.attrs[key]
        encoded_attrs = "".join(
            f' {key}="{html.escape(value, quote=True)}"'
            for key, value in attrs.items()
            if value or (tag == "img" and key == "alt")
        )
        if tag in VOID_TAGS:
            return f"<{tag}{encoded_attrs} />"
        content = self.children(child)
        if tag == "a" and attrs.get("href") and not re.sub(r"<[^>]+>", "", content).strip() and "<img" not in content:
            return ""
        return f"<{tag}{encoded_attrs}>{content}</{tag}>"


def clean_body(body: str, assets: AssetCatalog, title: str) -> str:
    body = re.sub(
        r"\[caption([^\]]*)\](.*?)\[/caption\]",
        caption_markup,
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    parser = TreeParser()
    parser.feed(body)
    parser.close()
    renderer = SemanticRenderer(assets, title)
    cleaned = renderer.children(parser.root)
    if renderer.media_roles and renderer.image_index != len(renderer.media_roles):
        raise SystemExit(
            f"Expected {len(renderer.media_roles)} visual-fidelity images on {title!r}, "
            f"found {renderer.image_index}"
        )
    cleaned = publication_abstracts(cleaned, title)
    cleaned = permanent_page_layout(cleaned, title)
    if title == "Math 2250":
        # Squarespace's separate calendar collection was not included in the
        # export. Remove the otherwise empty heading instead of shipping a
        # known-dead internal link.
        cleaned = re.sub(
            r'<h2><a href="/math-2250-schedule">Calendar</a></h2>',
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
    # Markdown interprets four-space-indented HTML as a code block. Squarespace
    # emits presentation indentation between blocks, so remove it only when a
    # line begins with an HTML tag; indentation inside textual <pre> content is
    # left untouched.
    cleaned = re.sub(r"(?m)^[ \t]+(?=<)", "", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def taxonomy_paths(url_inventory: Path) -> dict[tuple[str, str], str]:
    paths: dict[tuple[str, str], str] = {}
    with url_inventory.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["source_site"] != "squarespace" or row["status"] != "200":
                continue
            if row["page_type"] == "category_index":
                paths[("category", unquote(row["path"].split("/")[-1]).replace("+", " "))] = row["path"]
            elif row["page_type"] == "tag_index":
                paths[("post_tag", unquote(row["path"].split("/")[-1]).replace("+", " "))] = row["path"]
    return paths


def active_squarespace_paths(url_inventory: Path) -> set[str]:
    paths: set[str] = set()
    with url_inventory.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["source_site"] != "squarespace" or row["status"] != "200":
                continue
            paths.add(urlsplit(row["path"]).path.rstrip("/") or "/")
    paths.update(RECOVERED_ARCHIVE_PATHS)
    return paths


def taxonomies_for(item: ET.Element, path_map: dict[tuple[str, str], str], domain: str) -> list[dict[str, str]]:
    result = []
    for node in item.findall("category"):
        if node.attrib.get("domain") != domain or not node.text:
            continue
        name = normalize_space(node.text)
        key = (domain, name.casefold())
        path = path_map.get(key)
        if not path:
            nicename = node.attrib.get("nicename", "")
            path = path_map.get((domain, nicename.casefold().replace("-", " ")))
        if not path:
            raise SystemExit(f"Missing live taxonomy path for {domain} {name!r}")
        result.append({"name": name, "path": path})
    return result


def write_markdown(path: Path, data: list[tuple[str, object]], body: str) -> None:
    lines = ["---"]
    for key, value in data:
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (list, dict)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = yaml_string(str(value))
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", "", body, ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def output_name(legacy_path: str) -> str:
    return legacy_path.rstrip("/").split("/")[-1] + ".md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wxr", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--urls", type=Path, required=True)
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    site_root = args.site.resolve()
    workspace_root = args.assets.resolve().parent.parent
    catalog = AssetCatalog(args.assets.resolve(), workspace_root, site_root / "public")
    path_map = taxonomy_paths(args.urls.resolve())
    active_paths = active_squarespace_paths(args.urls.resolve())
    root = ET.parse(args.wxr).getroot()
    generated: list[Path] = []
    public_paths = {"/", "/blog", "/search", "/work"}
    comment_paths: set[str] = set()
    math_paths: set[str] = set()
    counts = {"post": 0, "page": 0}

    for item in root.findall("./channel/item"):
        post_type = item.findtext("wp:post_type", namespaces=NAMESPACES)
        status = item.findtext("wp:status", namespaces=NAMESPACES)
        if status != "publish" or post_type not in {"post", "page"}:
            continue
        legacy_path = (item.findtext("link") or "").rstrip("/") or "/"
        if legacy_path not in active_paths:
            continue
        title = item.findtext("title") or "Untitled"
        body = item.findtext("content:encoded", namespaces=NAMESPACES) or ""
        cleaned = clean_body(body, catalog, title)
        excerpt = item.findtext("excerpt:encoded", namespaces=NAMESPACES) or ""
        cleaned_excerpt = clean_body(excerpt, catalog, title) if text_from_html(excerpt) else ""
        body_has_math = contains_math(body)
        if body_has_math:
            math_paths.add(legacy_path)
        if post_type == "page" and legacy_path == "/publications-and-preprints":
            # This imported page has been promoted to a hand-editable structured
            # collection. Still parse its source above so its media dependency
            # and MathJax route remain part of deterministic migration output,
            # but never overwrite the curated Markdown metadata or YAML records.
            output = site_root / "src/data/pages/publications-and-preprints.md"
            if not output.is_file() or not (site_root / "src/data/publications.yaml").is_file():
                raise SystemExit("Missing curated structured publications source")
            generated.append(output.relative_to(site_root))
            public_paths.add(legacy_path)
            counts[post_type] += 1
            continue
        if post_type == "post":
            tags = taxonomies_for(item, path_map, "post_tag")
            categories = taxonomies_for(item, path_map, "category")
            if body_has_math:
                math_paths.add("/blog")
                math_paths.update(item["path"] for item in [*tags, *categories])
            output = site_root / "src/data/blog" / output_name(legacy_path)
            data = [
                ("title", title),
                ("description", description_for(item, body)),
                *([("indexExcerpt", cleaned_excerpt)] if cleaned_excerpt else []),
                ("published", published_iso(item)),
                ("draft", False),
                ("tags", tags),
                ("categories", categories),
                ("comments", item.findtext("wp:comment_status", namespaces=NAMESPACES) == "open"),
                ("math", body_has_math),
                ("legacyPath", legacy_path),
                ("imported", True),
            ]
            if item.findtext("wp:comment_status", namespaces=NAMESPACES) == "open":
                comment_paths.add(legacy_path)
        else:
            output = site_root / "src/data/pages" / output_name(legacy_path)
            data = [
                ("title", title),
                ("displayTitle", display_title_for(body, title)),
                ("description", description_for(item, body)),
                ("legacyPath", legacy_path),
                ("math", body_has_math),
                ("imported", True),
            ]
        write_markdown(output, data, cleaned)
        generated.append(output.relative_to(site_root))
        public_paths.add(legacy_path)
        counts[post_type] += 1

    public_paths.update(value for value in path_map.values())
    expected = site_root / "scripts/validation/expected-squarespace-paths.txt"
    expected.write_text("\n".join(sorted(public_paths)) + "\n", encoding="utf-8")
    (site_root / "scripts/validation/expected-comment-paths.txt").write_text(
        "\n".join(sorted(comment_paths)) + "\n", encoding="utf-8"
    )
    (site_root / "scripts/validation/expected-math-paths.txt").write_text(
        "\n".join(sorted(math_paths)) + "\n", encoding="utf-8"
    )
    generated_manifest = site_root / "scripts/migration/generated-content.json"
    previous_files: set[Path] = set()
    if generated_manifest.is_file():
        previous = json.loads(generated_manifest.read_text(encoding="utf-8"))
        previous_files = {Path(value) for value in previous.get("files", [])}
    generated_files = set(generated)
    for stale in sorted(previous_files - generated_files):
        stale_path = site_root / stale
        if stale_path.is_file() and stale_path.suffix in {".md", ".mdx"}:
            stale_path.unlink()
    generated_manifest.write_text(
        json.dumps({"files": [str(path) for path in sorted(generated)]}, indent=2) + "\n",
        encoding="utf-8",
    )
    asset_manifest = site_root / "scripts/validation/expected-squarespace-assets.sha256"
    previous_assets: set[str] = set()
    if asset_manifest.is_file():
        previous_assets = {
            line.split("  ", 1)[1]
            for line in asset_manifest.read_text(encoding="utf-8").splitlines()
            if "  " in line
        }
    asset_count, copied_bytes = catalog.copy_used()
    current_assets = set(catalog.used)
    for stale in sorted(previous_assets - current_assets):
        if not stale.startswith("assets/squarespace/"):
            continue
        stale_path = site_root / "public" / stale
        if stale_path.is_file():
            stale_path.unlink()
    asset_manifest.write_text(
        "".join(f"{asset.sha256}  {relative}\n" for relative, asset in sorted(catalog.used.items())),
        encoding="utf-8",
    )
    if catalog.unresolved:
        for url in sorted(catalog.unresolved):
            print(f"UNRESOLVED ASSET {url}")
        raise SystemExit(f"Failed to localize {len(catalog.unresolved)} Squarespace asset URLs")
    print(
        f"Generated {counts['post']} posts and {counts['page']} pages; "
        f"localized {asset_count} assets ({copied_bytes:,} bytes copied this run); "
        f"recorded {len(public_paths)} exact public paths."
    )


if __name__ == "__main__":
    main()
