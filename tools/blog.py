#!/usr/bin/env python3
"""One-command blog workflow.

Usage:
    python3 tools/blog.py new "Post Title"   scaffold a draft post
    python3 tools/blog.py build              build posts, index, feed, sitemap
    python3 tools/blog.py watch              rebuild automatically when posts change
    python3 tools/blog.py dev                watch + local server + open browser
"""

import functools
import http.server
import json
import re
import sys
import textwrap
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent
POSTS_DIR = ROOT / "blog" / "posts"
BLOG_DIR = ROOT / "blog"
MEDIA_DIR = BLOG_DIR / "media"

COT = ZoneInfo("America/Bogota")

SITE_URL = "https://sagudelo.com"
AUTHOR_NAME = "Samuel Andrés Agudelo"
AUTHOR_URL = "https://sagudelo.com/"

WATCH_INTERVAL = 1.0


# ---------------------------------------------------------------- helpers

def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug.strip("-")


def sanitize_slug(value):
    slug = re.sub(r"[^a-z0-9-]", "", value.lower())
    return slug.strip("-")


def escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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


def resolve_date(value, path):
    if value == "auto" or value is None:
        return datetime.fromtimestamp(path.stat().st_mtime, COT).replace(microsecond=0)
    if isinstance(value, datetime):
        return value.replace(microsecond=0)
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=COT)
        return dt.replace(microsecond=0)
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime, COT).replace(microsecond=0)


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


# ---------------------------------------------------------------- markdown

def parse_inline(text):
    protected = []

    def stash(value):
        protected.append(value)
        return "\x00%d\x00" % (len(protected) - 1)

    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{escape_html(m.group(1))}</code>"), text)
    text = re.sub(r"<[^>]+>", lambda m: stash(m.group(0)), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    for i, value in enumerate(protected):
        text = text.replace("\x00%d\x00" % i, value)
    return text


FENCE_RE = re.compile(r"^```(\w*)\s*$")
MEDIA_RE = re.compile(r'^!\[([^\]]*)\]\(([^)]+?)(?:\s+"([^"]*)")?\)$')


def markdown_to_html(text):
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if m:
            lang = m.group(1)
            i += 1
            code = []
            while i < len(lines) and not FENCE_RE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{escape_html(lang)}"' if lang else ""
            out.append(f'<pre><code{cls}>{escape_html(chr(10).join(code))}</code></pre>')
        else:
            buf = []
            while i < len(lines) and not FENCE_RE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            block = "\n".join(buf).strip()
            if block:
                out.append(render_block(block))
    return "\n".join(out)


def render_block(block):
    html = []
    for chunk in re.split(r"\n\s*\n", block):
        chunk = chunk.strip()
        if not chunk:
            continue
        html.append(render_chunk(chunk))
    return "\n".join(html)


def render_chunk(chunk):
    lines = chunk.splitlines()
    first = lines[0].strip()
    if first.startswith("<"):
        return chunk
    if first.startswith("# "):
        return f"<h2>{parse_inline(first[2:])}</h2>"
    if first.startswith("## "):
        return f"<h3>{parse_inline(first[3:])}</h3>"
    if first.startswith("### "):
        return f"<h4>{parse_inline(first[4:])}</h4>"
    if all(l.strip().startswith("- ") for l in lines if l.strip()):
        items = "".join(f"<li>{parse_inline(l.strip()[2:])}</li>" for l in lines if l.strip())
        return f"<ul>{items}</ul>"
    if all(re.match(r"^\s*\d+[.)]\s+", l) for l in lines if l.strip()):
        items = "".join(
            f"<li>{parse_inline(re.sub(r'^\s*\d+[.)]\s+', '', l))}</li>"
            for l in lines if l.strip()
        )
        return f"<ol>{items}</ol>"
    if all(l.strip().startswith(">") for l in lines if l.strip()):
        body = " ".join(l.strip()[1:].strip() for l in lines if l.strip())
        return f"<blockquote>{parse_inline(body)}</blockquote>"
    if len(lines) == 1:
        mm = MEDIA_RE.match(first)
        if mm:
            return render_media(mm)
    content = " ".join(l.strip() for l in lines)
    return f"<p>{parse_inline(content)}</p>"


def youtube_id(src):
    m = re.search(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([\w-]{6,})", src)
    return m.group(1) if m else None


def render_media(m):
    alt = m.group(1) or ""
    src = m.group(2).strip()
    caption = m.group(3)
    vid = youtube_id(src)
    if vid:
        title = escape_html(alt or "YouTube video")
        inner = (
            '<div class="embed-video">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{title}" '
            'loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            'gyroscope; picture-in-picture" allowfullscreen></iframe>'
            "</div>"
        )
    elif re.search(r"\.(mp4|webm|ogg)(?:[?#]|$)", src, re.I):
        ext = re.search(r"\.(mp4|webm|ogg)(?:[?#]|$)", src, re.I).group(1).lower()
        mime = {"mp4": "video/mp4", "webm": "video/webm", "ogg": "video/ogg"}[ext]
        inner = (
            '<video controls playsinline preload="metadata">'
            f'<source src="{escape_html(src)}" type="{mime}">'
            "Your browser does not support video playback."
            "</video>"
        )
    else:
        inner = (
            f'<img src="{escape_html(src)}" alt="{escape_html(alt)}" '
            'loading="lazy" decoding="async">'
        )
    if caption:
        return (
            "<figure>\n"
            f"{inner}\n"
            f"<figcaption>{escape_html(caption)}</figcaption>\n"
            "</figure>"
        )
    return inner


# ---------------------------------------------------------------- data

def load_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if not fm.get("title"):
            continue
        dt = resolve_date(fm.get("date"), path)
        slug = sanitize_slug(fm["slug"]) if fm.get("slug") else slugify(fm.get("title"))
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
                "background": fm.get("background", ""),
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


# ---------------------------------------------------------------- pages

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

        <link rel="preload" as="image" href="{bgPreload}">

        <link rel="stylesheet" href="/css/main.css">
        <link rel="stylesheet" href="/css/blog.css">

        <link rel="preload" as="font" href="/minimal/Fonts/DepartureMono-1.500/DepartureMono-Regular.woff2" type="font/woff2" crossorigin>

        <link rel="icon" href="../images/PortraitFav.png">

    {bgStyle}
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
    bg = post.get("background")
    if bg:
        bg_style = (
            "    <style>\n"
            f"        body {{ background-image: url('{bg}'); background-blend-mode: soft-light; }}\n"
            "    </style>"
        )
        bg_preload = bg
    else:
        bg_style = ""
        bg_preload = "/images/DSCN6874.jpg"
    return POST_TEMPLATE.format(
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
        json_ld=textwrap.indent(build_json_ld(post), "    "),
        bgStyle=bg_style,
        bgPreload=bg_preload,
    )


INDEX_TEMPLATE = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blog - Samuel Andrés Agudelo</title>
        <meta name="description" content="Blog by Samuel Andrés Agudelo.">
        <meta name="robots" content="index, follow">
        <meta property="og:title" content="Blog - Samuel Andrés Agudelo">
        <meta property="og:description" content="Blog by Samuel Andrés Agudelo.">
        <meta property="og:image" content="https://sagudelo.com/images/PortraitFav.png">
        <meta property="og:url" content="https://sagudelo.com/blog/blogIndex.html">
        <meta property="og:type" content="website">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Blog - Samuel Andrés Agudelo">
        <meta name="twitter:description" content="Blog by Samuel Andrés Agudelo.">
        <meta name="twitter:image" content="https://sagudelo.com/images/PortraitFav.png">
        <link rel="canonical" href="https://sagudelo.com/blog/blogIndex.html">
        <link rel="alternate" type="application/rss+xml" title="Samuel Andrés Agudelo - Blog" href="/blog/feed.xml">

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@100;200;300&display=swap" rel="stylesheet">

        <link rel="preload" as="image" href="/images/DSCN6874.jpg">

        <link rel="stylesheet" href="/css/main.css">
        <link rel="stylesheet" href="/css/blog.css">

        <style>
            body {{ background-image: url('/images/DSCN6874.jpg'); background-blend-mode: soft-light; }}
        </style>

        <link rel="preload" as="font" href="/minimal/Fonts/DepartureMono-1.500/DepartureMono-Regular.woff2" type="font/woff2" crossorigin>

        <link rel="icon" href="../images/PortraitFav.png">
    </head>
    <body>
        <a href="/index.html" class="back-link">← Back</a>

        <main>
            <h1>Blog</h1>
            <p>My personal entries</p>

            <section class="blog-list" id="blog-list">
                {articles}
            </section>
        </main>

        <script src="../js/scramble.js" defer></script>
        <script src="../js/parallax.js" defer></script>
    </body>
    </html>
""")


def render_index_article(p):
    lines = [
        '<article class="blog-entry">',
        '    <div class="entry-meta">',
        f'        <time datetime="{p["isoDateTime"]}">{escape_html(p["displayDate"])}</time>',
        f'        <span class="read-time">{p["readTime"]} min read</span>',
        "    </div>",
        f'    <h2><a href="/{p["url"]}">{escape_html(p["title"])}</a></h2>',
    ]
    if p["tags"]:
        items = "".join(f"<li>#{escape_html(t)}</li>" for t in p["tags"])
        lines.append(f'    <ul class="entry-tags" aria-label="Tags">{items}</ul>')
    if p["description"]:
        lines.append(f"    <p>{escape_html(p['description'])}</p>")
    lines.append("</article>")
    return "\n".join(lines)


def render_index(posts):
    public = [p for p in posts if not p["draft"]]
    if not public:
        articles = '<p class="empty-blog">No posts yet. Check back soon.</p>'
    else:
        articles = "\n".join(render_index_article(p) for p in public)
    return INDEX_TEMPLATE.format(articles=articles)


# ---------------------------------------------------------------- feed / sitemap / redirects

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


def cleanup_stale(posts):
    protected = {"blogIndex.html", "doom_console_blog.html"}
    post_files = {f"{p['slug']}.html" for p in posts}
    for path in sorted(BLOG_DIR.glob("*.html")):
        if path.name in protected or path.name in post_files:
            continue
        path.unlink()
        print(f"[cleanup] removed {path.name}")


# ---------------------------------------------------------------- commands

def build_all():
    posts = load_posts()

    for post in posts:
        html = render_post(post, posts)
        out_path = ROOT / post["url"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        status = "draft" if post["draft"] else "published"
        print(f"[{status}] {out_path.name}")

    index_path = BLOG_DIR / "blogIndex.html"
    index_path.write_text(render_index(posts), encoding="utf-8")
    print(f"[index] {index_path.name}")

    feed_path = BLOG_DIR / "feed.xml"
    feed_path.write_text(render_feed_xml(posts), encoding="utf-8")
    print(f"[feed] {feed_path.name}")

    update_sitemap(posts)
    print("[sitemap] updated")

    redirects = {
        BLOG_DIR / "doom_console_blog.html": "/blog/doom-console.html"
    }
    for old_path, new_url in redirects.items():
        write_redirect(old_path, new_url)
        print(f"[redirect] {old_path.name} -> {new_url}")

    cleanup_stale(posts)


def snapshot():
    if not POSTS_DIR.exists():
        return {}
    return {str(p): p.stat().st_mtime_ns for p in POSTS_DIR.glob("*.md")}


def start_server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    port = 8000
    while port < 8010:
        try:
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            port += 1
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://localhost:{port}/blog/blogIndex.html"
    print(f"[dev] serving at http://localhost:{port}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"[dev] open {url} in your browser if it did not open automatically")


def watch(serve=False):
    build_all()
    if serve:
        start_server()
    snap = snapshot()
    print("[watch] watching blog/posts/*.md (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(WATCH_INTERVAL)
            current = snapshot()
            if current != snap:
                all_keys = sorted(set(current) | set(snap))
                changed = [Path(k).name for k in all_keys if current.get(k) != snap.get(k)]
                print(f"[watch] changed: {changed}")
                snap = current
                build_all()
    except KeyboardInterrupt:
        print("\n[watch] stopped")


def cmd_new(title):
    slug = slugify(title)
    path = POSTS_DIR / f"{slug}.md"
    if path.exists():
        print(f"Error: {path} already exists.")
        sys.exit(1)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    content = f"""---
title: "{title}"
description: ""
date: auto
tags: []
draft: true
---

Write your post here.

<!-- Media examples (delete these):
![Alt text](media/image.jpg "Caption")
![Alt text](media/video.mp4)
![Alt text](https://www.youtube.com/watch?v=VIDEO_ID)
-->
"""
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")
    print(f"Put post images/videos in {MEDIA_DIR}")
    print("Run 'python3 tools/blog.py dev' to preview.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "new":
        if len(sys.argv) < 3:
            print("Usage: python3 tools/blog.py new \"Post Title\"")
            sys.exit(1)
        cmd_new(sys.argv[2])
    elif cmd == "build":
        build_all()
    elif cmd == "watch":
        watch()
    elif cmd == "dev":
        watch(serve=True)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
