(function()
{
    function formatDate(entry)
    {
        if (entry.displayDate)
        {
            return entry.displayDate;
        }
        var parts = entry.date.split("-");
        var yy = parts[0].slice(-2);
        var mm = parts[1];
        var dd = parts[2];
        var result = dd + "/" + mm + "/" + yy;
        if (entry.time)
        {
            result += " " + entry.time;
        }
        return result;
    }

    function renderTags(tags)
    {
        if (!tags || tags.length === 0)
        {
            return "";
        }
        var items = "";
        for (var i = 0; i < tags.length; i++)
        {
            items += "<li>#" + tags[i] + "</li>";
        }
        return '<ul class="entry-tags" aria-label="Tags">' + items + '</ul>';
    }

    function renderBlogList(containerId, entries)
    {
        var container = document.getElementById(containerId);
        if (!container) return;

        if (entries.length === 0)
        {
            container.innerHTML = '<p class="empty-blog">No posts yet. Check back soon.</p>';
            return;
        }

        var sorted = entries.slice().sort(function(a, b)
        {
            return new Date(b.isoDateTime || b.date) - new Date(a.isoDateTime || a.date);
        });

        sorted.forEach(function(entry)
        {
            var article = document.createElement("article");
            article.className = "blog-entry";

            var meta = document.createElement("div");
            meta.className = "entry-meta";

            var time = document.createElement("time");
            time.setAttribute("datetime", entry.isoDateTime || entry.date);
            time.textContent = formatDate(entry);
            meta.appendChild(time);

            if (entry.readTime)
            {
                var readTime = document.createElement("span");
                readTime.className = "read-time";
                readTime.textContent = entry.readTime + " min read";
                meta.appendChild(readTime);
            }

            var h2 = document.createElement("h2");
            var a = document.createElement("a");
            a.href = entry.url;
            a.textContent = entry.title;
            h2.appendChild(a);

            var p = document.createElement("p");
            p.textContent = entry.description;

            article.appendChild(meta);
            article.appendChild(h2);

            if (entry.tags && entry.tags.length > 0)
            {
                article.insertAdjacentHTML("beforeend", renderTags(entry.tags));
            }

            article.appendChild(p);
            container.appendChild(article);
        });
    }

    document.addEventListener("DOMContentLoaded", function()
    {
        if (typeof blogEntries !== "undefined")
        {
            renderBlogList("blog-list", blogEntries);
        }
    });
})();
