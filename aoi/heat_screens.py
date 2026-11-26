"""Base screenshots for the click heatmaps: 6 modules of the local Feb-2026 build (no Supabase, no DB writes) at the
reference viewport 1440 x 1050, page coordinates 0..1050. Requires the vite dev server on 127.0.0.1:3010.
Run: python -X utf8 aoi/heat_screens.py"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "figures/interface/heat"; OUT.mkdir(parents=True, exist_ok=True)
MODS = [("coin-flipper", "The Coin Flipper"), ("sample-pumper", "The Sample Size Pumper"), ("galton-board", "The Galton Board"),
        ("god-mode", "The God Mode Switch"), ("summation-machine", "The Summation Machine"), ("rank-line", "The Rank Line")]
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1050})
    for pid, title in MODS:
        pg.goto("http://127.0.0.1:3010/", wait_until="networkidle")
        pg.get_by_text(title, exact=True).first.click()
        pg.wait_for_timeout(2500)
        if pid == "god-mode":  # experimental state shows the sunlight slider that most god-mode clicks used
            pg.get_by_role("button", name="God Mode").first.click(); pg.wait_for_timeout(1200)
        pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(300)
        # hide the local test-account badge (top right) so no account text appears in the figure
        pg.evaluate("""() => { for (const e of document.querySelectorAll('*')) { if (e.childElementCount === 0 && /@localhost/.test(e.textContent)) {
            let b = e; while (b.parentElement && b.parentElement.getBoundingClientRect().width < 400) b = b.parentElement;
            b.style.visibility = 'hidden'; } } }""")
        pg.screenshot(path=str(OUT / f"{pid}.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 1050})
        print(pid, "ok")
    b.close()
