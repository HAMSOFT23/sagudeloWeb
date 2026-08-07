#!/usr/bin/env python3
"""Scaffold a new blog post.

Usage:
    python3 tools/new-post.py "My Post Title"
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

COT = ZoneInfo("America/Bogota")
ROOT = Path(__file__).parent.parent
POSTS_DIR = ROOT / "blog" / "posts"


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug.strip("-")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/new-post.py \"My Post Title\"")
        sys.exit(1)

    title = sys.argv[1]
    slug = slugify(title)
    path = POSTS_DIR / f"{slug}.md"

    if path.exists():
        print(f"Error: {path} already exists.")
        sys.exit(1)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    content = f"""---
title: "{title}"
description: ""
date: auto
tags: []
draft: true
---

Write your post here.
"""
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")
    print("Run 'python3 tools/build.py' when ready to publish.")


if __name__ == "__main__":
    main()
