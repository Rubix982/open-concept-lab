// Holding page for advisoratlas.fyi while the server is switched off.
//
// Deployed as a Cloudflare Worker on the route *advisoratlas.fyi/* (see README.md).
// A route runs before Cloudflare tries the origin, so this answers every request
// even with the tunnel down. Remove the route to send traffic back to the app.

const WRITE_UP = "https://rubix982.github.io/open-concept-lab/shipped/advisor-atlas/";

// The backdrop echoes the app's map: universities as dots sized by faculty, a few
// with the heavy ring the app used for R1s. Seeded, so every visitor sees the same one.
function backdrop() {
  let seed = 1011;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  // Loose clusters, roughly where the app's dots were densest.
  const clusters = [
    [180, 210, 120], [300, 260, 90], [620, 190, 110], [700, 260, 70],
    [880, 300, 80], [1010, 230, 90], [1080, 420, 60], [460, 470, 70],
  ];
  let dots = "";
  for (const [cx, cy, spread] of clusters) {
    for (let i = 0; i < 16; i++) {
      const a = rand() * Math.PI * 2;
      const d = Math.pow(rand(), 0.7) * spread;
      const x = (cx + Math.cos(a) * d).toFixed(1);
      const y = (cy + Math.sin(a) * d * 0.7).toFixed(1);
      const r = (2 + Math.pow(rand(), 2.2) * 13).toFixed(1);
      dots += rand() < 0.09
        ? `<circle cx="${x}" cy="${y}" r="${r}" class="ring"/>`
        : `<circle cx="${x}" cy="${y}" r="${r}" class="dot"/>`;
    }
  }
  return `<svg class="map" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${dots}</svg>`;
}

const PAGE = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Advisor Atlas is paused</title>
<style>
  :root {
    --bg: #eef1f4; --panel: #ffffff; --ink: #16283c; --muted: #4f5f70; --faint: #7d8b99;
    --bar: #1c2b3c; --bar-ink: #ffffff; --accent: #2f6fd6; --accent-ink: #ffffff;
    --dot: #1c2b3c; --rule: #dde2e7; --pill: #f3e6c4; --pill-ink: #6b4e0e;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f141a; --panel: #161d25; --ink: #e6ebf0; --muted: #a9b6c3; --faint: #7d8b99;
      --bar: #0b1016; --bar-ink: #e6ebf0; --accent: #6aa0f0; --accent-ink: #0b1016;
      --dot: #8fa6be; --rule: #26303b; --pill: #3a2f14; --pill-ink: #f0d58a;
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; }
  body {
    min-height: 100vh; display: flex; flex-direction: column;
    background: var(--bg); color: var(--ink);
    font: 17px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  .bar {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.85rem 20px; background: var(--bar); color: var(--bar-ink);
  }
  .brand { font-weight: 700; letter-spacing: 0.01em; }
  .pill {
    display: inline-flex; align-items: center; gap: 0.45rem;
    padding: 0.15rem 0.65rem; border-radius: 999px;
    background: var(--pill); color: var(--pill-ink); font-size: 0.78rem; font-weight: 600;
  }
  .pill::before {
    content: ""; width: 0.5rem; height: 0.5rem; border-radius: 50%;
    border: 2px solid currentColor; box-sizing: border-box;
  }
  .stage { position: relative; flex: 1; display: grid; place-items: center; padding: 3rem 16px; overflow: hidden; }
  .map {
    position: absolute; inset: 0; width: 100%; height: 100%;
    -webkit-mask-image: radial-gradient(ellipse at center, transparent 22%, #000 75%);
            mask-image: radial-gradient(ellipse at center, transparent 22%, #000 75%);
  }
  .map .dot { fill: var(--dot); opacity: 0.16; }
  .map .ring { fill: none; stroke: var(--dot); stroke-width: 3; opacity: 0.28; }
  @media (prefers-reduced-motion: no-preference) {
    .map { animation: drift 40s ease-in-out infinite alternate; }
    @keyframes drift { to { transform: scale(1.06) translate(-1%, 1%); } }
  }
  main {
    position: relative; width: 100%; max-width: 36rem;
    background: var(--panel); border: 1px solid var(--rule); border-radius: 14px;
    padding: 2.2rem 2rem 1.6rem; box-shadow: 0 18px 50px -24px rgba(16, 32, 52, 0.35);
  }
  h1 {
    font: 500 clamp(1.9rem, 1.4rem + 2vw, 2.5rem)/1.15 Georgia, "Times New Roman", serif;
    margin: 0 0 1rem;
  }
  p { margin: 0 0 1rem; color: var(--muted); }
  .tally {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;
    margin: 1.4rem 0; padding: 1rem 0; border-block: 1px solid var(--rule);
  }
  .tally b { display: block; font: 600 1.35rem/1.2 Georgia, serif; color: var(--ink); }
  .tally span { font-size: 0.78rem; color: var(--faint); }
  .go {
    display: inline-block; padding: 0.7rem 1.2rem; border-radius: 8px;
    background: var(--accent); color: var(--accent-ink); font-weight: 600; text-decoration: none;
  }
  .go:hover { filter: brightness(1.08); }
  .go:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  .url { display: block; margin-top: 0.55rem; font-size: 0.8rem; color: var(--faint); word-break: break-all; }
  .url a { color: inherit; }
  .contact { margin-top: 1.5rem; font-size: 0.95rem; }
  .contact a { color: var(--accent); }
  .foot { margin: 1.4rem 0 0; padding-top: 1rem; border-top: 1px solid var(--rule); font-size: 0.85rem; color: var(--faint); }
  @media (max-width: 480px) { main { padding: 1.6rem 1.25rem 1.2rem; } }
</style>
</head>
<body>
<header class="bar"><span class="brand">Advisor Atlas</span><span class="pill">Paused</span></header>
<div class="stage">
  ${backdrop()}
  <main>
    <h1>Advisor Atlas is paused</h1>
    <p>
      Advisor Atlas was a map for finding a PhD advisor and a way to pay for the
      degree, made first for students in Pakistan applying abroad. It ran from
      11 to 20 October 2026 and is switched off for now.
    </p>
    <div class="tally">
      <div><b>198,570</b><span>researchers</span></div>
      <div><b>700</b><span>universities</span></div>
      <div><b>1.1M</b><span>research grants</span></div>
    </div>
    <p>What it did, what it held and what it was missing are written up, with screenshots.</p>
    <a class="go" href="${WRITE_UP}">Read the write-up →</a>
    <span class="url"><a href="${WRITE_UP}">${WRITE_UP.replace("https://", "")}</a></span>
    <p class="contact">
      Please reach out to Saif Ul Islam
      (<a href="mailto:saifulislam84210@gmail.com">saifulislam84210@gmail.com</a>)
      so he can re-enable it. Thank you.
    </p>
    <p class="foot">Thank you to everyone who tried it.</p>
  </main>
</div>
</body>
</html>`;

export default {
  async fetch(request) {
    const { pathname } = new URL(request.url);
    // 503 with Retry-After tells crawlers and API clients this is temporary,
    // so the holding text is not indexed as the site's content.
    const headers = { "Retry-After": "86400", "Cache-Control": "public, max-age=300" };
    if (pathname.startsWith("/api/")) {
      return Response.json({ error: "Advisor Atlas is paused." }, { status: 503, headers });
    }
    return new Response(PAGE, {
      status: 503,
      headers: { ...headers, "Content-Type": "text/html; charset=utf-8" },
    });
  },
};
