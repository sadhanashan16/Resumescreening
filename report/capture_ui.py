"""Capture the (logged-in) UI screenshots used as figures in the report.

Needs the app running on :8765 with an empty database, e.g.

    APP_DATA_DIR=/tmp/cap SECRET_KEY=x SESSION_COOKIE_SECURE=0 RATELIMIT_ENABLED=0 \
        flask --app app:create_app db upgrade
    APP_DATA_DIR=/tmp/cap SECRET_KEY=x SESSION_COOKIE_SECURE=0 RATELIMIT_ENABLED=0 \
        flask --app app:create_app run --port 8765
    python report/capture_ui.py

The script registers a demo user, screens the built-in sample resumes against three real example job descriptions
through the normal UI/API, shortlists the AI-recommended candidates of one run and then takes the screenshots.
"""
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

B = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "figures"
W = 1100


def shrink(path, width=1100):
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, optimize=True)


def screen(pg, role, title, top_n="5"):
    pg.goto(B + "/screenings/new")
    pg.select_option("#example", role)
    pg.wait_for_timeout(500)
    pg.check("#use_samples")
    pg.fill("#top_n", top_n)
    pg.click("#submit-btn")
    pg.wait_for_url("**/screenings/*", timeout=60000)
    pg.wait_for_selector("#cb-list tr, #cb-list article", timeout=20000)
    return pg.url


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": W, "height": 900}, device_scale_factor=2, bypass_csp=True)
    pg = ctx.new_page()

    # login / registration page (before any account exists)
    pg.goto(B + "/register"); pg.wait_for_timeout(400)
    pg.fill("input[name=name]", "Priya Raman")
    pg.fill("input[name=email]", "priya.raman@example.com")
    pg.fill("input[name=password]", "Sup3rSecret99")
    pg.fill("input[name=confirm]", "Sup3rSecret99")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "ui_register.png"), clip={"x": 0, "y": 0, "width": W, "height": 760})
    pg.click("button[type=submit]"); pg.wait_for_url("**/dashboard**", timeout=15000)

    # three screening runs (the samples are screened against real example job descriptions)
    screen(pg, "devops-engineer", "DevOps Engineer")
    screen(pg, "backend-developer", "Backend Developer")

    # the main run: data scientist - fill the form for the screenshot first
    pg.goto(B + "/screenings/new")
    pg.select_option("#example", "data-scientist"); pg.wait_for_timeout(500)
    pg.check("#use_samples")
    pg.set_input_files("#files", ["/home/user/Resumescreening/samples/Lina_Reddy_qa_engineer.doc"])
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "ui_screen_form.png"), clip={"x": 0, "y": 0, "width": W, "height": 900})
    pg.click("#submit-btn"); pg.wait_for_url("**/screenings/*", timeout=60000)
    pg.wait_for_selector("#cb-list tr, #cb-list article", timeout=20000); pg.wait_for_timeout(900)
    run_url = pg.url

    # shortlist the AI recommendation, reject the weakest, then screenshot the detail page
    pg.click("#shortlist-recommended"); pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "ui_screening_detail.png"), clip={"x": 0, "y": 0, "width": W, "height": 1000})

    # one candidate drawer (score breakdown)
    rows = pg.locator("#cb-list tr.clickable")
    if rows.count():
        rows.nth(0).click(); pg.wait_for_timeout(900)
        pg.screenshot(path=str(OUT / "ui_candidate_drawer.png"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

    # shortlist page
    pg.goto(B + "/shortlist"); pg.wait_for_selector("#cb-list tr, #cb-list article", timeout=15000); pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "ui_shortlist.png"), clip={"x": 0, "y": 0, "width": W, "height": 800})

    # dashboard
    pg.goto(B + "/dashboard"); pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "ui_dashboard.png"), clip={"x": 0, "y": 0, "width": W, "height": 900})

    # job match
    pg.goto(B + "/match"); pg.select_option("#sample", "Chen_Lewis_devops_engineer.pdf"); pg.click("#submit-btn")
    pg.wait_for_selector(".cand"); pg.wait_for_timeout(1200)
    pg.locator("#results").screenshot(path=str(OUT / "ui_match_results.png"))

    # model insights
    pg.goto(B + "/insights"); pg.wait_for_selector("#cm td"); pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "ui_insights.png"), clip={"x": 0, "y": 0, "width": W, "height": 800})
    b.close()

for n in ("ui_register", "ui_screen_form", "ui_screening_detail", "ui_candidate_drawer", "ui_shortlist", "ui_dashboard",
          "ui_match_results", "ui_insights"):
    if (OUT / f"{n}.png").exists():
        shrink(OUT / f"{n}.png")
print(sorted(x.name for x in OUT.iterdir()))
