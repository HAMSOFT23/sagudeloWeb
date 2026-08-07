const email = "samuel.agudelo534@gmail.com";
let currentState = 0;

function toggleEmail()
{
    const state0 = document.getElementById("email-state-0");
    const state1 = document.getElementById("email-state-1");
    const state2 = document.getElementById("email-state-2");
    const button = document.getElementById("email-button");

    if (!state0 || !state1 || !state2 || !button) return;

    if (currentState === 0)
    {
        state0.style.display = "none";
        state1.style.display = "inline";
        state1.style.backgroundColor = "var(--foreground)";
        state1.style.color = "var(--background)";
        state1.style.padding = "0 4px";
        button.setAttribute("aria-label", "Copy email address to clipboard");
        currentState = 1;
    }
    else if (currentState === 1)
    {
        state1.style.display = "none";
        state2.style.display = "inline";
        state2.style.backgroundColor = "var(--foreground)";
        state2.style.color = "var(--background)";
        state2.style.padding = "0 4px";
        button.setAttribute("aria-label", "Email copied to clipboard");
        currentState = 2;

        navigator.clipboard.writeText(email).catch(function()
        {
            // Fallback for browsers that block clipboard access.
            var ta = document.createElement("textarea");
            ta.value = email;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            try
            {
                document.execCommand("copy");
            }
            catch (e)
            {
            }
            document.body.removeChild(ta);
        });

        setTimeout(function()
        {
            state2.style.display = "none";
            state0.style.display = "block";
            button.style.backgroundColor = "transparent";
            button.style.color = "";
            button.style.padding = "0";
            button.setAttribute("aria-label", "Show email address");
            currentState = 0;
        }, 3000);
    }
}

(function()
{
    document.addEventListener("DOMContentLoaded", function()
    {
        const button = document.getElementById("email-button");
        if (button)
        {
            button.addEventListener("click", toggleEmail);
        }
    });
})();
