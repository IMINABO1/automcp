document.getElementById('copyBtn').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const url = new URL(tab.url);
    const cookies = await chrome.cookies.getAll({ domain: url.hostname });

    // Filter keys to match Playwright expectations (mostly)
    const simplifiedCookies = cookies.map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        expires: c.expirationDate,
        httpOnly: c.httpOnly,
        secure: c.secure,
        sameSite: c.sameSite
    }));

    const jsonStr = JSON.stringify(simplifiedCookies, null, 2);

    navigator.clipboard.writeText(jsonStr).then(() => {
        document.getElementById('status').innerText = "Copied! Paste into cookies.json";
    });
});
