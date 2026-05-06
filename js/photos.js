(function()
{
    const baseImages =
    [
        { src: "images/DSCN3863.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4315.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4518.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4532.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4533.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4534.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4535.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4561.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4631.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4651.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4659.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4794.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4833.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN4835.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN5095.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN5554.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN5559.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN5562.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6031.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6041.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6046.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6048.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6059.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6060.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6067.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6071.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6088.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6097.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6110.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6114.jpg",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6132.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6135.JPG",  url: "https://www.instagram.com/vab_.14" },
        { src: "images/DSCN6138.JPG",  url: "https://www.instagram.com/vab_.14" },
        { src: "images/DSCN6284.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6288.png",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6290.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6296.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6312.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6313.JPG",  url: "https://www.instagram.com/sagudelophoto/" },
        { src: "images/DSCN6317.JPG",  url: "https://www.instagram.com/sagudelophoto/" }
    ];

    const photos = [];
    for (let i = 0; i < baseImages.length; i++)
    {
        photos.push(
        {
            src: baseImages[i].src,
            url: baseImages[i].url
        });
    }

    const canvas = document.getElementById("photo-canvas");
    if (!canvas) return;

    var expandedItem = null;
    var overlay = null;
    var overlayOpacity = 0;
    var targetOverlayOpacity = 0;

    const items = [];
    const mouse = { x: -9999, y: -9999 };
    const REPULSION_RADIUS = 150;
    const REPULSION_STRENGTH = 0.25;
    const DAMPING = 0.92;

    function lerp(a, b, t)
    {
        return a + (b - a) * t;
    }

    function lerpItem(item)
    {
        item.x = lerp(item.x, item.targetX, 0.15);
        item.y = lerp(item.y, item.targetY, 0.15);
        item.currentScale = lerp(item.currentScale, item.targetScale, 0.15);
        item.rotation = lerp(item.rotation, item.targetRotation, 0.15);
    }

    function applyTransform(item, scale)
    {
        item.el.style.transform = "translate(" + item.x + "px, " + item.y + "px) scale(" + scale + ") rotate(" + item.rotation + "deg)";
    }

    function createOverlay()
    {
        overlay = document.createElement("div");
        overlay.className = "photo-overlay";
        canvas.appendChild(overlay);

        overlay.addEventListener("click", function(e)
        {
            if (expandedItem !== null)
            {
                e.stopPropagation();
                collapsePhoto();
            }
        });
    }

    function expandPhoto(item)
    {
        if (expandedItem && expandedItem !== item)
        {
            collapsePhoto();
        }

        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const imgW = item.width || 240;
        const imgH = item.height || 240;
        const targetScale = Math.min((0.9 * vw) / imgW, (0.9 * vh) / imgH, 5);

        item.targetScale = targetScale;
        item.targetX = (vw - imgW) / 2;
        item.targetY = (vh - imgH) / 2;
        item.targetRotation = 0;
        item.phase = "expanding";
        item.el.style.zIndex = "11";

        targetOverlayOpacity = 1;
        overlay.classList.add("active");
        expandedItem = item;
    }

    function collapsePhoto()
    {
        if (!expandedItem) return;

        var item = expandedItem;
        item.targetScale = 1;
        item.targetX = item.homeX;
        item.targetY = item.homeY;
        item.targetRotation = item.originalRotation;
        item.phase = "collapsing";

        targetOverlayOpacity = 0;
        overlay.classList.remove("active");
        expandedItem = null;
    }

    function createPhotoElements()
    {
        createOverlay();

        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const headerOffset = 120;
        const padding = 40;

        const cols = Math.ceil(Math.sqrt(photos.length * (vw / vh)));
        const rows = Math.ceil(photos.length / cols);
        const cellW = (vw - padding * 2) / cols;
        const cellH = (vh - headerOffset - padding) / rows;

        photos.forEach(function(photo, i)
        {
            const link = document.createElement("a");
            link.href = photo.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.className = "floating-photo";

            const img = document.createElement("img");
            img.src = photo.src;
            img.alt = photo.src.split("/").pop().split(".")[0];
            img.loading = "lazy";
            link.appendChild(img);

            canvas.appendChild(link);

            const col = i % cols;
            const row = Math.floor(i / cols);
            const homeX = padding + col * cellW + (cellW / 2) - 90;
            const homeY = headerOffset + row * cellH + (cellH / 2) - 90;
            const rot = (Math.random() - 0.5) * 6;

            items.push(
            {
                el: link,
                img: img,
                x: homeX,
                y: homeY,
                vx: 0,
                vy: 0,
                homeX: homeX,
                homeY: homeY,
                rotation: rot,
                originalRotation: rot,
                driftOffset: Math.random() * Math.PI * 2,
                width: 240,
                height: 240,
                phase: "normal",
                currentScale: 1,
                targetScale: 1,
                targetX: homeX,
                targetY: homeY,
                targetRotation: rot
            });

            img.onload = function()
            {
                const rect = img.getBoundingClientRect();
                items[i].width = rect.width || 180;
                items[i].height = rect.height || 180;
            };

            link.addEventListener("click", function(e)
            {
                var item = items[i];
                if (item.phase === "normal")
                {
                    e.preventDefault();
                    expandPhoto(item);
                }
                else if (item.phase === "expanded")
                {
                    window.open(item.el.href, "_blank");
                    e.preventDefault();
                }
            });
        });
    }

    document.addEventListener("mousemove", function(e)
    {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    document.addEventListener("mouseleave", function()
    {
        mouse.x = -9999;
        mouse.y = -9999;
    });

    function animate()
    {
        overlayOpacity = lerp(overlayOpacity, targetOverlayOpacity, 0.15);
        overlay.style.opacity = overlayOpacity;

        if (overlayOpacity < 0.005)
        {
            overlay.classList.remove("active");
        }

        const time = Date.now() * 0.001;

        items.forEach(function(item)
        {
            if (item.phase === "expanding")
            {
                lerpItem(item);

                var dX = Math.abs(item.x - item.targetX);
                var dY = Math.abs(item.y - item.targetY);
                var dS = Math.abs(item.currentScale - item.targetScale);
                if (dX < 0.5 && dY < 0.5 && dS < 0.005)
                {
                    item.x = item.targetX;
                    item.y = item.targetY;
                    item.currentScale = item.targetScale;
                    item.rotation = item.targetRotation;
                    item.phase = "expanded";
                }

                applyTransform(item, item.currentScale);
                item.img.style.filter = "brightness(1)";
            }
            else if (item.phase === "expanded")
            {
                applyTransform(item, item.currentScale);
                item.img.style.filter = "brightness(1)";
            }
            else if (item.phase === "collapsing")
            {
                lerpItem(item);

                var dX = Math.abs(item.x - item.targetX);
                var dY = Math.abs(item.y - item.targetY);
                var dS = Math.abs(item.currentScale - item.targetScale);
                if (dX < 0.5 && dY < 0.5 && dS < 0.005)
                {
                    item.x = item.targetX;
                    item.y = item.targetY;
                    item.currentScale = item.targetScale;
                    item.rotation = item.targetRotation;
                    item.phase = "normal";
                    item.el.style.zIndex = "";
                }

                applyTransform(item, item.currentScale);
                item.img.style.filter = "brightness(1)";
            }
            else
            {
                const centerX = item.x + item.width / 2;
                const centerY = item.y + item.height / 2;

                const dx = centerX - mouse.x;
                const dy = centerY - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < REPULSION_RADIUS && dist > 0)
                {
                    const force = Math.pow(1 - dist / REPULSION_RADIUS, 2) * REPULSION_STRENGTH;
                item.vx += (dx / dist) * force;
                item.vy += (dy / dist) * force;
            }

            item.vx += Math.sin(time + item.driftOffset) * 0.008;
            item.vy += Math.cos(time + item.driftOffset) * 0.008;

                item.vx *= DAMPING;
                item.vy *= DAMPING;

                item.x += item.vx;
                item.y += item.vy;

                const vw = window.innerWidth;
                const vh = window.innerHeight;

                if (item.y < 140) item.y = 140;
                if (item.x < 10) item.x = 10;
                if (item.x > vw - item.width - 10) item.x = vw - item.width - 10;
                if (item.y > vh - item.height - 10) item.y = vh - item.height - 10;

                var rotation = item.originalRotation + (item.vx * 0.5);
                const hoverDist = 60;
                const isHovered = dist < hoverDist;
                const brightness = isHovered ? 1.15 : 0.9;

                applyTransform(item, 1);
                item.img.style.filter = "brightness(" + brightness + ")";
            }
        });

        requestAnimationFrame(animate);
    }

    createPhotoElements();
    animate();
})();
