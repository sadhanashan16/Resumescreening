"""Render poster/poster.html -> poster.png (4961x3508 px @300 dpi, A3 landscape) and poster.pdf (A3 landscape).

Also reports any panel whose content overflows (so text is never silently clipped).
"""
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
W, H = 2480, 1754  # CSS px canvas (A3 @150dpi); device scale factor 2 -> 4960 x 3508

CHECK_JS = """() => [...document.querySelectorAll('.panel')].map(p => {
  const b = p.querySelector('.pbody');
  const last = b.lastElementChild, used = last ? last.getBoundingClientRect().bottom - b.getBoundingClientRect().top : 0;
  return {title: p.querySelector('.pill').textContent, panel: p.clientHeight, content: Math.round(used), body: b.clientHeight,
          over: Math.round(used) - b.clientHeight, overW: b.scrollWidth - b.clientWidth}; })"""

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
    page.goto((HERE / "poster.html").as_uri())
    page.wait_for_timeout(500)
    bad = 0
    for r in page.evaluate(CHECK_JS):
        flag = "  <-- OVERFLOW" if r["over"] > 2 or r["overW"] > 2 else ""
        bad += bool(flag)
        print(f"{r['title']:<22} body={r['body']:>4} used={r['content']:>4} slack={-r['over']:>4} overW={r['overW']}{flag}")
    page.screenshot(path=str(HERE / "poster_raw.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
    page.pdf(path=str(HERE / "poster.pdf"), width="420mm", height="297mm", print_background=True, scale=420 / 25.4 * 96 / W,
             page_ranges="1")
    browser.close()

im = Image.open(HERE / "poster_raw.png").convert("RGB")
im = im.resize((4961, 3508), Image.LANCZOS)  # exact A3 @ 300 dpi
im.save(HERE / "poster.png", dpi=(300, 300), optimize=True)
(HERE / "poster_raw.png").unlink()
print("poster.png", im.size, "overflowing panels:", bad)
