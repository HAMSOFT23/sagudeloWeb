(function()
{
    var baseImages =
    [
        { src: "images/DSCN3863.jpg",  description: "Take me back to that day" },
        { src: "images/DSCN4315.JPG" },
        { src: "images/DSCN4518.JPG" },
        { src: "images/DSCN4532.JPG" },
        { src: "images/DSCN4533.JPG" },
        { src: "images/DSCN4534.JPG" },
        { src: "images/DSCN4535.JPG" },
        { src: "images/DSCN4561.JPG" },
        { src: "images/DSCN4631.JPG" },
        { src: "images/DSCN4651.JPG" },
        { src: "images/DSCN4659.JPG" },
        { src: "images/DSCN4794.JPG" },
        { src: "images/DSCN4833.JPG" },
        { src: "images/DSCN4835.JPG" },
        { src: "images/DSCN5095.jpg" },
        { src: "images/DSCN5554.JPG" },
        { src: "images/DSCN5559.JPG" },
        { src: "images/DSCN5562.jpg" },
        { src: "images/DSCN6031.jpg" },
        { src: "images/DSCN6041.jpg" },
        { src: "images/DSCN6046.jpg" },
        { src: "images/DSCN6048.jpg" },
        { src: "images/DSCN6059.jpg" },
        { src: "images/DSCN6060.jpg" },
        { src: "images/DSCN6067.jpg" },
        { src: "images/DSCN6071.jpg" },
        { src: "images/DSCN6088.jpg" },
        { src: "images/DSCN6097.jpg" },
        { src: "images/DSCN6110.jpg" },
        { src: "images/DSCN6114.jpg" },
        { src: "images/DSCN6132.JPG",  description: "I often think about her" },
        { src: "images/DSCN6135.JPG" },
        { src: "images/DSCN6138.JPG" },
        { src: "images/DSCN6284.JPG" },
        { src: "images/DSCN6288.png" },
        { src: "images/DSCN6290.JPG" },
        { src: "images/DSCN6296.JPG" },
        { src: "images/DSCN6312.JPG" },
        { src: "images/DSCN6313.JPG",  description: "A truly beautiful city" },
        { src: "images/DSCN6317.JPG" }
    ];

    var canvas = document.getElementById("photo-canvas");
    if (!canvas) return;

    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", function(e)
    {
        reducedMotion = e.matches;
        for (var i = 0; i < items.length; i++)
        {
            items[i].sleeping = false;
        }
    });

    var expandedItem = null;
    var overlay = null;
    var overlayOpacity = 0;
    var targetOverlayOpacity = 0;
    var tooltipEl = null;

    var items = [];
    var mouse = { x: -9999, y: -9999 };

    var REPULSION_RADIUS = 150;
    var REPULSION_RADIUS_SQ = REPULSION_RADIUS * REPULSION_RADIUS;
    var REPULSION_STRENGTH = 0.25;
    var SPRING_K = 0.005;
    var DAMPING = 0.92;
    var SLEEP_VELOCITY_SQ = 0.0001;
    var HOME_EPSILON = 0.5;

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
        var tx = item.x;
        var ty = item.y;
        var rot = item.rotation;
        if (tx !== item._lastTx || ty !== item._lastTy || scale !== item._lastScale || rot !== item._lastRot)
        {
            item.el.style.transform = "translate3d(" + tx + "px," + ty + "px,0) scale(" + scale + ") rotate(" + rot + "deg)";
            item._lastTx = tx;
            item._lastTy = ty;
            item._lastScale = scale;
            item._lastRot = rot;
        }
    }

    function createOverlay()
    {
        overlay = document.createElement("div");
        overlay.className = "photo-overlay";
        canvas.appendChild(overlay);

        overlay.addEventListener("click", function()
        {
            if (expandedItem !== null)
            {
                collapsePhoto();
            }
        });
    }

    function createTooltip(text)
    {
        if (tooltipEl)
        {
            tooltipEl.remove();
        }
        tooltipEl = document.createElement("div");
        tooltipEl.className = "photo-tooltip";
        tooltipEl.textContent = text;
        tooltipEl.style.opacity = "0";
        document.body.appendChild(tooltipEl);
    }

    function destroyTooltip()
    {
        if (tooltipEl)
        {
            tooltipEl.remove();
            tooltipEl = null;
        }
    }

    function moveTooltip(e)
    {
        if (!tooltipEl) return;
        tooltipEl.style.left = (e.clientX + 12) + "px";
        tooltipEl.style.top = (e.clientY + 12) + "px";
    }

    function showTooltip()
    {
        if (tooltipEl) tooltipEl.style.opacity = "1";
    }

    function hideTooltip()
    {
        if (tooltipEl) tooltipEl.style.opacity = "0";
    }

    function expandPhoto(item)
    {
        if (expandedItem && expandedItem !== item)
        {
            collapsePhoto();
        }

        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var imgW = item.width || 240;
        var imgH = item.height || 240;
        var targetScale = Math.min((0.9 * vw) / imgW, (0.9 * vh) / imgH, 5);

        item.preExpandX = item.x;
        item.preExpandY = item.y;
        item.preExpandRotation = item.rotation;

        item.targetScale = targetScale;
        item.targetX = (vw - imgW) / 2;
        item.targetY = (vh - imgH) / 2;
        item.targetRotation = 0;
        item.phase = "expanding";
        item.sleeping = false;
        item.el.style.zIndex = "11";
        item.el.setAttribute("aria-expanded", "true");

        targetOverlayOpacity = 1;
        overlay.classList.add("active");
        expandedItem = item;

        if (item.description)
        {
            createTooltip(item.description);
            item.el.addEventListener("mousemove", moveTooltip);
            item.el.addEventListener("mouseenter", showTooltip);
            item.el.addEventListener("mouseleave", hideTooltip);
        }
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
        item.sleeping = false;
        item.el.setAttribute("aria-expanded", "false");

        targetOverlayOpacity = 0;
        overlay.classList.remove("active");
        expandedItem = null;

        if (item.description)
        {
            item.el.removeEventListener("mousemove", moveTooltip);
            item.el.removeEventListener("mouseenter", showTooltip);
            item.el.removeEventListener("mouseleave", hideTooltip);
            destroyTooltip();
        }
    }

    function onPhotoActivate(item)
    {
        if (item.phase === "normal")
        {
            expandPhoto(item);
        }
        else if (item.phase === "expanded")
        {
            window.open("https://www.instagram.com/sagudelophoto/", "_blank", "noopener,noreferrer");
        }
    }

    function createPhotoElements()
    {
        createOverlay();

        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var headerOffset = 210;
        var padding = 40;

        var cols = Math.ceil(Math.sqrt(baseImages.length * (vw / vh)));
        var rows = Math.ceil(baseImages.length / cols);
        var cellW = (vw - padding * 2) / cols;
        var cellH = (vh - headerOffset - padding) / rows;

        for (var i = 0; i < baseImages.length; i++)
        {
            var photo = baseImages[i];

            var div = document.createElement("div");
            div.className = "floating-photo";
            div.setAttribute("role", "listitem");
            div.setAttribute("tabindex", "0");
            div.setAttribute("aria-label", photo.description || "Photo " + (i + 1));
            div.setAttribute("aria-expanded", "false");

            var img = document.createElement("img");
            img.src = photo.src;
            img.alt = photo.description || "";
            img.loading = "lazy";
            img.decoding = "async";
            div.appendChild(img);

            canvas.appendChild(div);

            var col = i % cols;
            var row = Math.floor(i / cols);
            var homeX = padding + col * cellW + (cellW / 2) - 90;
            var homeY = headerOffset + row * cellH + (cellH / 2) - 90;
            var rot = (Math.random() - 0.5) * 6;

            var item =
            {
                el: div,
                img: img,
                x: homeX,
                y: homeY,
                homeX: homeX,
                homeY: homeY,
                vx: 0,
                vy: 0,
                rotation: rot,
                originalRotation: rot,
                width: 240,
                height: 240,
                phase: "normal",
                currentScale: 1,
                targetScale: 1,
                targetX: homeX,
                targetY: homeY,
                targetRotation: rot,
                sleeping: false,
                description: photo.description || null,
                preExpandX: homeX,
                preExpandY: homeY,
                preExpandRotation: rot,
                _lastTx: null,
                _lastTy: null,
                _lastScale: null,
                _lastRot: null
            };

            items.push(item);

            (function(idx)
            {
                img.onload = function()
                {
                    items[idx].width = Math.min(img.naturalWidth || 240, 240);
                    items[idx].height = Math.min(img.naturalHeight || 240, 240);
                };
            })(i);

            (function(idx)
            {
                var photoItem = items[idx];

                div.addEventListener("click", function(e)
                {
                    e.stopPropagation();
                    onPhotoActivate(photoItem);
                });

                div.addEventListener("keydown", function(e)
                {
                    if (e.key === "Enter" || e.key === " ")
                    {
                        e.preventDefault();
                        onPhotoActivate(photoItem);
                    }
                    else if (e.key === "Escape" && expandedItem)
                    {
                        e.preventDefault();
                        collapsePhoto();
                    }
                });
            })(i);
        }
    }

    document.addEventListener("mousemove", function(e)
    {
        if (reducedMotion) return;
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    document.addEventListener("mouseleave", function()
    {
        mouse.x = -9999;
        mouse.y = -9999;
    });

    document.addEventListener("keydown", function(e)
    {
        if (e.key === "Escape" && expandedItem)
        {
            e.preventDefault();
            collapsePhoto();
        }
    });

    function animate()
    {
        overlayOpacity = lerp(overlayOpacity, targetOverlayOpacity, 0.15);
        overlay.style.opacity = overlayOpacity;

        if (overlayOpacity < 0.005)
        {
            overlay.classList.remove("active");
        }

        for (var i = 0; i < items.length; i++)
        {
            var item = items[i];

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
            }
            else if (item.phase === "expanded")
            {
                applyTransform(item, item.currentScale);
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
            }
            else
            {
                if (reducedMotion)
                {
                    item.x = item.homeX;
                    item.y = item.homeY;
                    item.vx = 0;
                    item.vy = 0;
                    applyTransform(item, 1);
                    continue;
                }

                if (item.sleeping)
                {
                    var cdx = item.x + item.width * 0.5 - mouse.x;
                    var cdy = item.y + item.height * 0.5 - mouse.y;
                    var cSqDist = cdx * cdx + cdy * cdy;
                    if (cSqDist > REPULSION_RADIUS_SQ)
                    {
                        continue;
                    }
                    item.sleeping = false;
                }

                var centerX = item.x + item.width * 0.5;
                var centerY = item.y + item.height * 0.5;
                var dx = centerX - mouse.x;
                var dy = centerY - mouse.y;
                var sqDist = dx * dx + dy * dy;

                if (sqDist < REPULSION_RADIUS_SQ && sqDist > 0)
                {
                    var dist = Math.sqrt(sqDist);
                    var t = 1 - dist / REPULSION_RADIUS;
                    var force = t * t * REPULSION_STRENGTH;
                    item.vx += (dx / dist) * force;
                    item.vy += (dy / dist) * force;
                }

                var dispX = item.x - item.homeX;
                var dispY = item.y - item.homeY;
                item.vx -= dispX * SPRING_K;
                item.vy -= dispY * SPRING_K;

                item.vx *= DAMPING;
                item.vy *= DAMPING;

                item.x += item.vx;
                item.y += item.vy;

                applyTransform(item, 1);

                var velSq = item.vx * item.vx + item.vy * item.vy;
                var atHome = Math.abs(dispX) < HOME_EPSILON && Math.abs(dispY) < HOME_EPSILON;
                if (velSq < SLEEP_VELOCITY_SQ && atHome && sqDist > REPULSION_RADIUS_SQ)
                {
                    item.sleeping = true;
                    item.x = item.homeX;
                    item.y = item.homeY;
                    item.vx = 0;
                    item.vy = 0;
                }
            }
        }

        requestAnimationFrame(animate);
    }

    createPhotoElements();
    animate();
})();
