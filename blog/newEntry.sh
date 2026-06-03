#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BLOG_DIR="$SCRIPT_DIR"
DATA_FILE="$BLOG_DIR/blogData.js"

echo "=== New Blog Entry ==="
read -p "Title: " TITLE

if [ -z "$TITLE" ]; then
    echo "Error: Title cannot be empty."
    exit 1
fi

SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')
FILENAME="${SLUG}.html"
FILEPATH="$BLOG_DIR/$FILENAME"

if [ -f "$FILEPATH" ]; then
    echo "Error: File $FILENAME already exists."
    exit 1
fi

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
DATE_DISPLAY=$(date +%d/%m/%y)

cat > "$FILEPATH" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${TITLE} - Samuel Andrés Agudelo</title>
    <meta name="description" content="${TITLE} — a blog post by Samuel Andrés Agudelo.">
    <meta property="og:title" content="${TITLE} - Samuel Andrés Agudelo">
    <meta property="og:description" content="${TITLE} — a blog post by Samuel Andrés Agudelo.">
    <meta property="og:image" content="https://sagudelo.com/images/PortraitFav.png">
    <meta property="og:url" content="https://sagudelo.com/blog/${FILENAME}">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="${TITLE} - Samuel Andrés Agudelo">
    <meta name="twitter:description" content="${TITLE} — a blog post by Samuel Andrés Agudelo.">
    <meta name="twitter:image" content="https://sagudelo.com/images/PortraitFav.png">
    <link rel="canonical" href="https://sagudelo.com/blog/${FILENAME}">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@100;200;300&display=swap" rel="stylesheet">

    <link rel="preload" as="image" href="/images/wide_img.jpg">

    <link rel="stylesheet" href="/css/main.css">
    <link rel="stylesheet" href="/css/blog.css">

    <link rel="preload" as="font" href="/minimal/Fonts/DepartureMono-1.500/DepartureMono-Regular.woff2" type="font/woff2" crossorigin>

    <link rel="icon" href="../images/Hamsioft.jpg">
</head>
<body>
    <a href="/blog/blogIndex.html" class="back-link">← Back</a>

    <main class="blog-post">
        <h1>${TITLE}</h1>

        <section class="blog-list">
            <article class="blog-entry">
                <time datetime="${DATE}">${DATE_DISPLAY} ${TIME}</time>
                <h2></h2>
                <p></p>
            </article>
        </section>
    </main>

    <script src="../js/scramble.js" defer></script>
</body>
</html>
EOF

NEW_ENTRY="    {
        date: \"${DATE}\",
        time: \"${TIME}\",
        title: \"${TITLE}\",
        description: \"\",
        url: \"${FILENAME}\"
    },"

sed -i "s|    //New Entries Go Here|    //New Entries Go Here\n\n${NEW_ENTRY}|" "$DATA_FILE"

echo ""
echo "Created: $FILEPATH"
echo "Added entry to: $DATA_FILE"
echo "Date: $DATE_DISPLAY $TIME"
