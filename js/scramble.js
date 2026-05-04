(function()
{
    const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*^';
    const INTERVAL = 40;

    function randomChar()
    {
        return CHARS[Math.floor(Math.random() * CHARS.length)];
    }

    document.addEventListener('mouseover', function(e)
    {
        const link = e.target.closest('a');
        if (!link || link.dataset.scrambleBound) return;
        if (!link.textContent.trim()) return;

        link.dataset.scrambleBound = 'true';

        link.addEventListener('mouseenter', function()
        {
            if (!this.dataset.original)
            {
                this.dataset.original = this.textContent;
            }

            const text = this.dataset.original;
            var step = 0;
            var lastTick = 0;

            cancelAnimationFrame(this._scrambleRaf);

            function tick(timestamp)
            {
                if (!lastTick)
                {
                    lastTick = timestamp;
                }

                var elapsed = timestamp - lastTick;

                if (elapsed >= INTERVAL)
                {
                    var result = '';
                    for (var i = 0; i < text.length; i++)
                    {
                        if (i < step)
                        {
                            result += text[i];
                        }
                        else
                        {
                            result += randomChar();
                        }
                    }
                    link.textContent = result;
                    step++;
                    lastTick = timestamp;
                }

                if (step > text.length)
                {
                    link.textContent = text;
                    return;
                }

                link._scrambleRaf = requestAnimationFrame(tick);
            }

            link._scrambleRaf = requestAnimationFrame(tick);
        });

        link.addEventListener('mouseleave', function()
        {
            cancelAnimationFrame(this._scrambleRaf);
            if (this.dataset.original)
            {
                this.textContent = this.dataset.original;
            }
        });
    });
})();
