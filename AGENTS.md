# sagudeloWeb

> This branch contains the **minimal interactive** version of the site.  
> A separate version (on another branch) also includes `myGames.html`, `contact.html`, and a Cloudflare Worker email backend (`functions/sendMail.js`).

## Quick Start
1. Edit HTML files directly — no build step needed for site pages
2. Blog posts live in `blog/posts/*.md`; after editing, run `python3 tools/build.py` to regenerate post pages, `blogData.js`, `feed.xml`, and `sitemap.xml`
3. Deploy static files to any host (Netlify, Vercel, GitHub Pages, etc.)

## Architecture
| Page | Purpose |
|------|---------|
| `index.html` | Home / bio — split-layout, interactive elements |
| `photos.html` | Photo portfolio — physics-based floating canvas |
| `blog/blogIndex.html` | Blog listing rendered from `blogData.js` |
| `blog/*.html` | Individual blog posts (generated from Markdown by `tools/build.py`) |

## a. Minimalism
- **No build tools** — plain HTML, CSS, and vanilla JS
- **Single-file pages** — each route is a self-contained HTML file
- **Typography-first** — DepartureMono (custom WOFF2) + Roboto Mono fallback, uppercase, `font-weight: 300`
- **Split-layout homepage** — left column (bio + links) and right column (electronics + blog) on desktop; stacks vertically on mobile
- **Full-bleed background** — single background image (`wide_img.png`) with `soft-light` blend mode, covering `100vh`

## b. Color Palette
| Token | Value | Usage |
|-------|-------|-------|
| `--foreground` | `#ffffff` | Text, icons, highlighted spans |
| `--background` | `#2e2d2d` | Page background |
| Hover inversion | `#000000` on `#ffffff` | Link hover state |
| Overlay | `rgba(0,0,0,0.85)` | Photo expansion backdrop |

- High-contrast monochrome scheme
- `::selection` inverts to background-on-foreground
- Text shadow `0px 0px 8px #00000050` for legibility over the background image

## c. Interactive
1. **Mouse Parallax** (`js/parallax.js`)  
   Background image subtly follows cursor with smooth lerp interpolation.
2. **Scramble Text** (`js/scramble.js`)  
   All anchor tags reveal their text through a random-character decode effect on hover.
3. **Email Toggle** (`js/email.js`)  
   Three-state inline widget: envelope icon → revealed address → "COPIED!" (auto-copies to clipboard via `navigator.clipboard`).
4. **Floating Photo Canvas** (`js/photos.js`)  
   - Physics simulation: spring forces, damping, mouse repulsion, gentle drift
   - Click to expand a photo with a dark overlay; click again to open Instagram
   - Sleep/wake optimization for off-screen and idle items

## d. Blog
- Posts are written as Markdown in `blog/posts/*.md` (frontmatter: `title`, `description`, `date` or `auto`, `tags`, `draft`)
- `python3 tools/build.py` generates post pages, `blogData.js`, `feed.xml`, updates `sitemap.xml`, and writes a redirect for `doom_console_blog.html` → `doom-console.html`
- `tools/new-post.py "Title"` scaffolds a new draft post
- Data-driven index: `blog/blogData.js` exports an array of entries
- `js/blog.js` sorts by date (newest first) and injects `<article>` elements into `blog/blogIndex.html` (date + read time → title → plain-text tags → description)
- Individual posts are static HTML pages styled with `css/blog.css`
- Drafts: rendered to HTML with `noindex` but excluded from `blogData.js`, `feed.xml`, and `sitemap.xml`
- No persistent nav bar across pages — each page is standalone (only a `← Back` link on subpages)

## Key Files
| Path | Purpose |
|------|---------|
| `css/main.css` | Global styles, typography, layout, mobile breakpoint |
| `css/photos.css` | Photo canvas layout and floating-photo styling |
| `css/blog.css` | Blog list and entry styling |
| `js/email.js` | Email toggle + clipboard copy |
| `js/scramble.js` | Hover scramble effect for all links |
| `js/parallax.js` | Mouse-driven background parallax |
| `js/photos.js` | Physics-based photo canvas |
| `js/blog.js` | Blog index renderer |
| `blog/blogData.js` | Blog entry data source |
| `blog/posts/*.md` | Blog post sources (Markdown) |
| `tools/build.py` | Build: post pages, blogData.js, feed.xml, sitemap |
| `tools/new-post.py` | Scaffold a new draft post |
| `minimal/Fonts/DepartureMono-1.500/` | Custom font files (OTF, WOFF, WOFF2) |

## Development
- No npm scripts — open `index.html` directly in a browser
- No tests, linting, or typecheck configured
- Every code block should have the brackets on a separate line:

{

}