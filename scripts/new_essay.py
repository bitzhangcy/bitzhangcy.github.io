#!/usr/bin/env python3
"""Create a private essay draft; publishing is an explicit front-matter edit."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re


def create_essay(source: Path, slug: str, title: str, description: str, published_on: date) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must use lowercase letters, numbers, and single hyphens")
    if not title.strip():
        raise ValueError("title must not be empty")
    folder = source / "blogs"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{slug}.md"
    # JSON strings are valid YAML scalars, including quotes and multiline titles.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    content = f'''---
layout: essay
title: {quote(title.strip())}
description: {quote(description.strip())}
date: {published_on.isoformat()}
permalink: /blogs/{slug}/
lang: zh-CN
locale: zh_CN
published: false
status: writing
# last_modified_at: {published_on.isoformat()}
---

## 开篇

'''
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="URL slug, e.g. reading-history")
    parser.add_argument("title", help="Essay title; quote it if it contains spaces")
    parser.add_argument("--description", default="", help="Required before making the essay public")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Publication date YYYY-MM-DD (default: local today)")
    args = parser.parse_args()
    try:
        path = create_essay(Path(__file__).resolve().parent.parent, args.slug, args.title, args.description, args.date)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Created private draft: {path}")
    print("Before publishing, fill description and set published: true. Keep status: writing while it is in progress.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
