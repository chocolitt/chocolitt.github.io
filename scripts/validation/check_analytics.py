#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


MEASUREMENT_ID = "G-SQPKVD92TL"
LOADER = f"https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"
CONFIG = f"gtag('config', '{MEASUREMENT_ID}')"


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    production = os.environ.get("PUBLIC_SITE_ENV") == "production"
    failures: list[str] = []

    for page in sorted(dist.rglob("*.html")):
        source = page.read_text(encoding="utf-8", errors="replace")
        loader_count = source.count(LOADER)
        config_count = source.count(CONFIG)
        expected = 1 if production else 0

        if loader_count != expected or config_count != expected:
            failures.append(
                f"{page.relative_to(dist)}: expected {expected} Google tag, "
                f"found {loader_count} loader(s) and {config_count} config call(s)"
            )

    if failures:
        print("Google Analytics validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    mode = "production" if production else "non-production"
    print(f"PASS: Google Analytics configuration is correct for {mode} output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
