"""Capture the UI screenshots used as figures in the report (needs the app on :8765).

NOTE: written for the pre-accounts UI. The app now requires a login, so re-running this needs a sign-in step first;
the committed report figures are unaffected.
"""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

B = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "figures"
W = 900


def shrink(path, width=1100):
    im = Image.open(path).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, optimize=True)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": W, "height": 900}, device_scale_factor=2, bypass_csp=True)
    pg = ctx.new_page()
    # 5.1 home
    pg.goto(B + "/"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "ui_home.png"), clip={"x": 0, "y": 0, "width": W, "height": 640})
    # 5.2 screening form (filled)
    pg.goto(B + "/screen"); pg.select_option("#example", "data-scientist"); pg.check("#use_samples")
    pg.set_input_files("#files", ["/home/user/Resumescreening/samples/Lina_Reddy_qa_engineer.doc"])
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "ui_screen_form.png"), clip={"x": 0, "y": 0, "width": W, "height": 640})
    # 5.3 results
    pg.click("#submit-btn"); pg.wait_for_selector(".cand"); pg.wait_for_timeout(1200)
    pg.add_style_tag(content=".site-header{position:static!important}")
    box = pg.locator("#results").bounding_box()
    pg.locator("#results").screenshot(path=str(OUT / "ui_screen_results_full.png"))
    # 5.4 match
    pg.goto(B + "/match"); pg.select_option("#sample", "Chen_Lewis_devops_engineer.pdf"); pg.click("#submit-btn")
    pg.wait_for_selector(".cand"); pg.wait_for_timeout(1200)
    pg.locator("#results").screenshot(path=str(OUT / "ui_match_results_full.png"))
    # 5.5 insights
    pg.goto(B + "/insights"); pg.wait_for_selector("#cm td"); pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "ui_insights.png"), clip={"x": 0, "y": 0, "width": W, "height": 700})
    b.close()

for name, h in (("ui_screen_results_full", 1380), ("ui_match_results_full", 1250)):
    im = Image.open(OUT / f"{name}.png")
    im.crop((0, 0, im.width, min(h * 2 // 2, im.height))).save(OUT / name.replace("_full", ".png"))
    (OUT / f"{name}.png").unlink()
for n in ("ui_home", "ui_screen_form", "ui_screen_results", "ui_match_results", "ui_insights"):
    shrink(OUT / f"{n}.png")
print(sorted(x.name for x in OUT.iterdir()))
