(function()
{
    function formatDate(dateStr, timeStr)
    {
        var parts = dateStr.split("-");
        var yy = parts[0].slice(-2);
        var mm = parts[1];
        var dd = parts[2];
        var result = dd + "/" + mm + "/" + yy;
        if (timeStr)
        {
            result += " " + timeStr;
        }
        return result;
    }

    function renderBlogList(containerId, entries)
    {
        var container = document.getElementById(containerId);
        if (!container) return;

        var sorted = entries.slice().sort(function(a, b)
        {
            return new Date(b.date) - new Date(a.date);
        });

        sorted.forEach(function(entry)
        {
            var article = document.createElement("article");
            article.className = "blog-entry";

            var time = document.createElement("time");
            time.setAttribute("datetime", entry.date);
            time.textContent = formatDate(entry.date, entry.time || null);

            var h2 = document.createElement("h2");
            var a = document.createElement("a");
            a.href = entry.url;
            a.textContent = entry.title;
            h2.appendChild(a);

            var p = document.createElement("p");
            p.textContent = entry.description;

            article.appendChild(time);
            article.appendChild(h2);
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
