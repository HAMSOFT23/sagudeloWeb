#!/usr/bin/env python3
"""Build static blog pages from Markdown sources.

Run after editing or adding a post:
    python3 tools/build.py
"""

import json
import re
import textwrap
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent
POSTS_DIR = ROOT / "blog" / "posts"
BLOG_DIR = ROOT / "blog"

COT = ZoneInfo("America/Bogota")

SITE_URL = "https://sagudelo.com"
AUTHOR_NAME = "Samuel Andrés Agudelo"
AUTHOR_URL = "https://sagudelo.com/"


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug.strip("-")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    body = parts[2].strip()
    fm = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        elif value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "[]":
            value = []
        elif value.startswith("[") and value.endswith("]"):
            value = [
                v.strip().strip('"\'')
                for v in value[1:-1].split(",")
                if v.strip()
            ]
        fm[key] = value
    return fm, body


def resolve_date(value):
    if value == "auto" or value is None:
        return datetime.now(COT).replace(microsecond=0)
    if isinstance(value, datetime):
        return value.replace(microsecond=0)
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=COT)
        return dt.replace(microsecond=0)
    except ValueError:
        return datetime.now(COT).replace(microsecond=0)


def format_display_date(dt):
    hour = dt.hour % 12 or 12
    minute = dt.minute
    ampm = "a.m." if dt.hour < 12 else "p.m."
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year % 100:02d} {hour}:{minute:02d} {ampm}"


def format_iso(dt):
    return dt.isoformat()


def format_rfc2822(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def estimate_read_time(text):
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return minutes


def parse_inline(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text
    )
    return text


def markdown_to_html(text):
    blocks = re.split(r"\n\s*\n", text.strip())
    html = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        first = lines[0].strip()
        if first.startswith("# "):
            html.append(f"<h2>{parse_inline(first[2:])}</h2>")
        elif first.startswith("## "):
            html.append(f"<h3>{parse_inline(first[3:])}</h3>")
        elif first.startswith("### "):
            html.append(f"<h4>{parse_inline(first[4:])}</h4>")
        elif all(line.strip().startswith("- ") for line in lines if line.strip()):
            items = "".join(
                f"<li>{parse_inline(line.strip()[2:])}</li>"
                for line in lines
                if line.strip()
            )
            html.append(f"<ul>{items}</ul>")
        else:
            content = " ".join(line.strip() for line in lines)
            content = parse_inline(content)
            html.append(f"<p>{content}</p>")
    return "\n".join(html)


def escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if not fm.get("title"):
            continue
        dt = resolve_date(fm.get("date"))
        slug = slugify(fm.get("title"))
        url = f"blog/{slug}.html"
        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        posts.append(
            {
                "source": path.name,
                "slug": slug,
                "url": url,
                "title": fm.get("title"),
                "description": fm.get("description", ""),
                "date": dt,
                "tags": tags,
                "draft": bool(fm.get("draft", False)),
                "body": body,
                "readTime": estimate_read_time(body),
                "displayDate": format_display_date(dt),
                "isoDateTime": format_iso(dt),
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_tags(tags):
    if not tags:
        return ""
    items = "".join(
        f"<li>#{tag}</li>"
        for tag in tags
    )
    return f'<ul class="post-tags" aria-label="Tags">{items}</ul>'


def render_related_posts(current, all_posts):
    others = [
        p for p in all_posts
        if not p["draft"] and p["slug"] != current["slug"]
    ]
    if not others:
        return ""
    related = others[:3]
    items = "".join(
        f'<li><a href="/{p["url"]}">{escape_html(p["title"])}</a></li>'
        for p in related
    )
    return (
        '<aside class="related-posts">'
        '<h2>More posts</h2>'
        f'<ul>{items}</ul>'
        '</aside>'
    )


def build_json_ld(post):
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post["description"] or post["title"],
        "author": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": AUTHOR_URL
        },
        "publisher": {
            "@type": "Person",
            "name": AUTHOR_NAME
        },
        "datePublished": post["isoDateTime"],
        "dateModified": post["isoDateTime"],
        "url": f"{SITE_URL}/{post['url']}"
    }
    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": SITE_URL + "/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Blog",
                "item": SITE_URL + "/blog/blogIndex.html"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": post["title"],
                "item": f"{SITE_URL}/{post['url']}"
            }
        ]
    }
    return json.dumps([article, breadcrumbs], indent=4, ensure_ascii=False)


POST_TEMPLATE = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Samuel Andrés Agudelo</title>
        <meta name="description" content="{description}">
        <meta name="robots" content="{robots}">
        <meta property="og:title" content="{title} - Samuel Andrés Agudelo">
        <meta property="og:description" content="{description}">
        <meta property="og:image" content="https://sagudelo.com/images/PortraitFav.png">
        <meta property="og:url" content="https://sagudelo.com/{url}">
        <meta property="og:type" content="article">
        <meta property="article:published_time" content="{isoDateTime}">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{title} - Samuel Andrés Agudelo">
        <meta name="twitter:description" content="{description}">
        <meta name="twitter:image" content="https://sagudelo.com/images/PortraitFav.png">
        <link rel="canonical" href="https://sagudelo.com/{url}">

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@100;200;300&display=swap" rel="stylesheet">

        <link rel="preload" as="image" href="/images/wide_img.jpg">

        <link rel="stylesheet" href="/css/main.css">
        <link rel="stylesheet" href="/css/blog.css">

        <link rel="preload" as="font" href="/minimal/Fonts/DepartureMono-1.500/DepartureMono-Regular.woff2" type="font/woff2" crossorigin>

        <link rel="icon" href="../images/Hamsioft.jpg">

    <script type="application/ld+json">
{json_ld}
    </script>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <a href="/blog/blogIndex.html" class="back-link">← Back</a>

    <main id="main-content" class="blog-post">
            <article>
                <header class="post-header">
                    <h1>{title}</h1>
                    <div class="post-meta">
                        <time datetime="{isoDateTime}">{displayDate}</time>
                        <span class="read-time">{readTime} min read</span>
                    </div>
                    {tagsHtml}
                </header>

                <div class="post-content">
                    {content}
                </div>
            </article>

            {relatedPosts}
        </main>

        <script src="../js/scramble.js" defer></script>
    </body>
    </html>
""")


def render_post(post, all_posts):
    robots = "noindex, nofollow" if post["draft"] else "index, follow"
    content = markdown_to_html(post["body"])
    html = POST_TEMPLATE.format(
        title=escape_html(post["title"]),
        description=escape_html(post["description"] or post["title"]),
        robots=robots,
        url=post["url"],
        isoDateTime=post["isoDateTime"],
        displayDate=post["displayDate"],
        readTime=post["readTime"],
        tagsHtml=render_tags(post["tags"]),
        content=content,
        relatedPosts=render_related_posts(post, all_posts),
        json_ld=textwrap.indent(build_json_ld(post), "    ")
    )
    return html


def render_blog_data_js(posts):
    public = [p for p in posts if not p["draft"]]
    entries = []
    for p in public:
        entry = {
            "date": p["date"].strftime("%Y-%m-%d"),
            "time": p["date"].strftime("%H:%M"),
            "displayDate": p["displayDate"],
            "isoDateTime": p["isoDateTime"],
            "title": p["title"],
            "description": p["description"],
            "url": p["url"],
            "tags": p["tags"],
            "readTime": p["readTime"]
        }
        entries.append(entry)
    js = "const blogEntries =\n"
    js += json.dumps(entries, indent=4, ensure_ascii=False)
    js += ";\n"
    return js


def render_feed_xml(posts):
    public = [p for p in posts if not p["draft"]]
    items = []
    for p in public:
        items.append(
            "    <item>\n"
            f"      <title>{escape_html(p['title'])}</title>\n"
            f"      <link>{SITE_URL}/{p['url']}</link>\n"
            f"      <description>{escape_html(p['description'] or p['title'])}</description>\n"
            f"      <pubDate>{format_rfc2822(p['date'])}</pubDate>\n"
            f"      <guid>{SITE_URL}/{p['url']}</guid>\n"
            "    </item>"
        )
    return textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Samuel Andrés Agudelo - Blog</title>
            <link>{site_url}/blog/blogIndex.html</link>
            <description>Game design, development, electronics, and photography.</description>
            <language>en</language>
            <lastBuildDate>{build_date}</lastBuildDate>
        {items}
          </channel>
        </rss>
    """).format(
        site_url=SITE_URL,
        build_date=format_rfc2822(datetime.now(COT)),
        items="\n".join(items)
    )


def update_sitemap(posts):
    sitemap_path = ROOT / "sitemap.xml"
    if not sitemap_path.exists():
        return

    text = sitemap_path.read_text(encoding="utf-8")
    existing_locs = set(re.findall(r"<loc>([^<]+)</loc>", text))

    post_map = {
        f"{SITE_URL}/{p['url']}": p["date"].strftime("%Y-%m-%d")
        for p in posts
        if not p["draft"]
    }

    # Remove stale /blog/*.html entries that no longer correspond to a post.
    stale_locs = {
        loc for loc in existing_locs
        if loc.startswith(f"{SITE_URL}/blog/") and loc.endswith(".html")
        and loc not in post_map
        and loc != f"{SITE_URL}/blog/blogIndex.html"
    }

    def remove_stale(match):
        loc = match.group(1)
        if loc in stale_locs:
            return ""
        return match.group(0)

    text = re.sub(
        r"\s*<url>\s*<loc>([^<]+)</loc>\s*<lastmod>[^<]+</lastmod>\s*<priority>[^<]+</priority>\s*</url>",
        remove_stale,
        text
    )

    def replace_lastmod(match):
        loc = match.group(1)
        if loc in post_map:
            return (
                f"<loc>{loc}</loc>\n"
                f"    <lastmod>{post_map[loc]}</lastmod>"
            )
        return match.group(0)

    text = re.sub(
        r"<loc>([^<]+)</loc>\s*\n\s*<lastmod>[^<]+</lastmod>",
        replace_lastmod,
        text
    )

    new_entries = []
    for loc, lastmod in post_map.items():
        if loc not in existing_locs and loc not in stale_locs:
            new_entries.append(
                f"  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n"
                f"    <priority>0.6</priority>\n"
                f"  </url>"
            )

    if new_entries:
        text = text.replace("</urlset>", "\n".join(new_entries) + "\n</urlset>")

    sitemap_path.write_text(text, encoding="utf-8")


def write_redirect(old_path, new_url):
    old_path.parent.mkdir(parents=True, exist_ok=True)
    html = textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="refresh" content="0; url={new_url}">
            <title>Redirecting...</title>
            <link rel="canonical" href="{SITE_URL}{new_url}">
        </head>
        <body>
            <a href="{new_url}">Redirecting...</a>
        </body>
        </html>
    """)
    old_path.write_text(html, encoding="utf-8")


def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    posts = load_posts()

    for post in posts:
        html = render_post(post, posts)
        out_path = ROOT / post["url"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        status = "draft" if post["draft"] else "published"
        print(f"[{status}] {out_path}")

    blog_data_path = BLOG_DIR / "blogData.js"
    blog_data_path.write_text(render_blog_data_js(posts), encoding="utf-8")
    print(f"[data] {blog_data_path}")

    feed_path = BLOG_DIR / "feed.xml"
    feed_path.write_text(render_feed_xml(posts), encoding="utf-8")
    print(f"[feed] {feed_path}")

    update_sitemap(posts)
    print("[sitemap] updated")

    redirects = {
        BLOG_DIR / "doom_console_blog.html": "/blog/doom-console.html"
    }
    for old_path, new_url in redirects.items():
        write_redirect(old_path, new_url)
        print(f"[redirect] {old_path} -> {new_url}")


if __name__ == "__main__":
    main()
