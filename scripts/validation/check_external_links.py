#!/usr/bin/env python3
"""Check external links in a built site and write machine- and human-readable reports."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import fnmatch
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (compatible; daniellitt.com external-link-checker/1.0; +https://www.daniellitt.com/)"
SELF_HOSTS = {"daniellitt.com", "www.daniellitt.com", "127.0.0.1", "localhost"}
BROKEN_STATUSES = {404, 410}
BLOCKED_STATUSES = {401, 403, 429}
HEAD_FALLBACK_STATUSES = {400, 401, 403, 404, 405, 410, 429, 500, 501, 502, 503, 504}


class ExternalLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"action", "href", "poster", "src"} and value:
                self.values.append(value)


@dataclass(frozen=True)
class LinkResult:
    url: str
    outcome: str
    http_status: int | None
    final_url: str | None
    detail: str
    sources: tuple[str, ...]


def normalize_url(value: str) -> str | None:
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if (parsed.hostname or "").casefold() in SELF_HOSTS:
        return None
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc, path, parsed.query, ""))


def load_ignore_patterns(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def matches_pattern(url: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(url, pattern) for pattern in patterns)


def discover_links(dist: Path, ignore_patterns: list[str]) -> dict[str, tuple[str, ...]]:
    discovered: dict[str, set[str]] = {}
    for page in sorted(dist.rglob("*.html")):
        parser = ExternalLinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        source = page.relative_to(dist).as_posix()
        for value in parser.values:
            url = normalize_url(value)
            if url is None or matches_pattern(url, ignore_patterns):
                continue
            discovered.setdefault(url, set()).add(source)
    return {url: tuple(sorted(sources)) for url, sources in sorted(discovered.items())}


def request_url(url: str, method: str, timeout: float) -> tuple[int, str]:
    headers = {"Accept": "*/*", "User-Agent": USER_AGENT}
    if method == "GET":
        headers["Range"] = "bytes=0-0"
    request = Request(url, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        if method == "GET":
            response.read(1)
        return response.status, response.geturl()


def classify_http_error(url: str, error: HTTPError, sources: tuple[str, ...]) -> LinkResult:
    status = error.code
    if status in BROKEN_STATUSES:
        outcome = "broken"
        detail = f"HTTP {status}"
    elif status in BLOCKED_STATUSES:
        outcome = "warning"
        detail = f"HTTP {status}; the remote site may block automated checks"
    else:
        outcome = "warning"
        detail = f"HTTP {status}"
    return LinkResult(url, outcome, status, error.geturl(), detail, sources)


def check_link(
    url: str,
    sources: tuple[str, ...],
    timeout: float,
    retries: int,
) -> LinkResult:
    head_error: HTTPError | None = None
    try:
        status, final_url = request_url(url, "HEAD", timeout)
        return LinkResult(url, "ok", status, final_url, "", sources)
    except HTTPError as error:
        head_error = error
        if error.code not in HEAD_FALLBACK_STATUSES:
            return classify_http_error(url, error, sources)
    except (TimeoutError, URLError, OSError):
        pass

    last_error: Exception | None = head_error
    for attempt in range(retries + 1):
        if attempt:
            time.sleep(min(0.5 * attempt, 1.5))
        try:
            status, final_url = request_url(url, "GET", timeout)
            return LinkResult(url, "ok", status, final_url, "", sources)
        except HTTPError as error:
            last_error = error
            if error.code in BROKEN_STATUSES | BLOCKED_STATUSES or 400 <= error.code < 500:
                break
        except (TimeoutError, URLError, OSError) as error:
            last_error = error

    if isinstance(last_error, HTTPError):
        return classify_http_error(url, last_error, sources)
    detail = str(getattr(last_error, "reason", last_error)) if last_error else "request failed"
    return LinkResult(url, "warning", None, None, detail, sources)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_markdown_report(path: Path, results: list[LinkResult], baseline_patterns: list[str]) -> None:
    healthy = [result for result in results if result.outcome == "ok"]
    broken = [result for result in results if result.outcome == "broken"]
    known_broken = [result for result in broken if matches_pattern(result.url, baseline_patterns)]
    new_broken = [result for result in broken if not matches_pattern(result.url, baseline_patterns)]
    warnings = [result for result in results if result.outcome == "warning"]
    lines = [
        "# External link check",
        "",
        f"Checked **{len(results)}** unique external URLs: "
        f"**{len(healthy)} healthy**, **{len(new_broken)} newly broken**, "
        f"**{len(known_broken)} known broken**, and **{len(warnings)} warnings**.",
        "",
    ]
    sections = (
        (new_broken, "Newly broken links"),
        (known_broken, "Known broken links (baseline)"),
        (warnings, "Warnings"),
    )
    for selected, heading in sections:
        if not selected:
            continue
        lines.extend([f"## {heading}", "", "| URL | Result | Referenced by |", "| --- | --- | --- |"])
        for result in selected:
            sources = ", ".join(f"`{source}`" for source in result.sources[:5])
            if len(result.sources) > 5:
                sources += f", and {len(result.sources) - 5} more"
            lines.append(
                f"| `{markdown_escape(result.url)}` | {markdown_escape(result.detail)} | {sources} |"
            )
        lines.append("")
    lines.extend([
        "Warnings do not fail the scheduled job because authentication, rate limits, bot protection, and transient server errors can make a healthy page unverifiable.",
        "Known broken links remain visible in the report but do not fail the job. Only newly confirmed HTTP 404 and 410 responses fail the check.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    parser.add_argument("--baseline-file", type=Path)
    parser.add_argument("--ignore-file", type=Path)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--markdown-report", type=Path)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    dist = args.dist.resolve()
    if not dist.is_dir():
        print(f"Missing build directory: {dist}", file=sys.stderr)
        return 2

    ignore_patterns = load_ignore_patterns(args.ignore_file)
    baseline_patterns = load_ignore_patterns(args.baseline_file)
    discovered = discover_links(dist, ignore_patterns)
    results: list[LinkResult] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(check_link, url, sources, args.timeout, max(0, args.retries)): url
            for url, sources in discovered.items()
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda result: (result.outcome != "broken", result.outcome != "warning", result.url))

    if args.json_report:
        args.json_report.write_text(
            json.dumps(
                [
                    {**asdict(result), "baselined": matches_pattern(result.url, baseline_patterns)}
                    for result in results
                ],
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    if args.markdown_report:
        write_markdown_report(args.markdown_report, results, baseline_patterns)

    broken = [result for result in results if result.outcome == "broken"]
    known_broken = [result for result in broken if matches_pattern(result.url, baseline_patterns)]
    new_broken = [result for result in broken if not matches_pattern(result.url, baseline_patterns)]
    warnings = [result for result in results if result.outcome == "warning"]
    print(
        f"Checked {len(results)} external URLs: {len(new_broken)} newly broken, "
        f"{len(known_broken)} known broken, {len(warnings)} warnings"
    )
    for result in new_broken:
        print(f"BROKEN {result.url}: {result.detail}")
    for result in known_broken:
        print(f"KNOWN {result.url}: {result.detail}")
    for result in warnings[:25]:
        print(f"WARNING {result.url}: {result.detail}")
    if len(warnings) > 25:
        print(f"WARNING: {len(warnings) - 25} additional warnings are available in the report")
    return 1 if new_broken else 0


if __name__ == "__main__":
    sys.exit(main())
