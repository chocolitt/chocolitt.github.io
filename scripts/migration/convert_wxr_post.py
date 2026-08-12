#!/usr/bin/env python3
"""Convert one Squarespace WordPress-export post to Astro Markdown.

This deliberately handles one post at a time so each generated file can be
reviewed before the full archive is converted.
"""

from __future__ import annotations

import argparse
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path


NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
}

ASSET_PATHS = {
    "ai_dungeon.jpeg": "/images/blog/library-of-babel/ai-dungeon.jpeg",
    "gpt3.jpeg": "/images/blog/library-of-babel/gpt3.jpeg",
}


def yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def localize_asset_url(url: str) -> str:
    for filename, local_path in ASSET_PATHS.items():
        if f"/{filename}" in url:
            return local_path
    return url


def convert_captions(body: str) -> str:
    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        image_match = re.search(r'<img\b.*?src="([^"]+)".*?/\s*>', inner, flags=re.DOTALL | re.IGNORECASE)
        if not image_match:
            return inner
        source = localize_asset_url(image_match.group(1))
        caption = strip_tags(inner[image_match.end() :])
        alt = html.escape(caption, quote=True)
        visible_caption = html.escape(caption)
        return f'<figure><img src="{source}" alt="{alt}" loading="lazy" /><figcaption>{visible_caption}</figcaption></figure>'

    return re.sub(r"\[caption[^\]]*\](.*?)\[/caption\]", replace, body, flags=re.DOTALL | re.IGNORECASE)


def clean_body(body: str) -> str:
    body = convert_captions(body)
    for filename, local_path in ASSET_PATHS.items():
        pattern = rf"https://images\.squarespace-cdn\.com/[^\"'\s<>]+/{re.escape(filename)}(?:\?format=[^\"'\s<>]+)?"
        body = re.sub(pattern, local_path, body)
    body = re.sub(r'\s+data-preserve-html-node="true"', "", body)
    body = re.sub(r'\s+name="#?([^\"]+)"', r' id="\1"', body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def find_post(root: ET.Element, legacy_path: str) -> ET.Element:
    for item in root.findall("./channel/item"):
        if (item.findtext("link") or "").rstrip("/") == legacy_path.rstrip("/"):
            return item
    raise SystemExit(f"No post found for {legacy_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wxr", type=Path)
    parser.add_argument("legacy_path")
    parser.add_argument("output", type=Path)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    root = ET.parse(args.wxr).getroot()
    item = find_post(root, args.legacy_path)
    title = item.findtext("title") or "Untitled"
    published = item.findtext("wp:post_date", namespaces=NAMESPACES) or item.findtext("pubDate") or ""
    published = published.replace(" ", "T")
    if "T" in published and not published.endswith("Z"):
        published += "Z"
    body = item.findtext("content:encoded", namespaces=NAMESPACES) or ""
    tags = [
        node.text.strip()
        for node in item.findall("category")
        if node.attrib.get("domain") == "post_tag" and node.text and node.text.strip()
    ]
    tags_yaml = "[" + ", ".join(yaml_string(tag) for tag in tags) + "]"
    frontmatter = "\n".join(
        [
            "---",
            f"title: {yaml_string(title)}",
            f"description: {yaml_string(args.description)}",
            f"published: {yaml_string(published)}",
            "draft: false",
            f"tags: {tags_yaml}",
            "comments: true",
            f"legacyPath: {yaml_string(args.legacy_path)}",
            "---",
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(frontmatter + clean_body(body) + "\n", encoding="utf-8")
    print(f"Converted {title!r} to {args.output} ({len(body)} source characters)")


if __name__ == "__main__":
    main()
