"""Pages, health check and the tools that predate accounts (job match, samples, validation)."""
import io

from resume_screening.catalog import ROLE_BY_ID, role_job_description

JD = role_job_description(ROLE_BY_ID["data-scientist"])
RESUME = ("Jane Doe\njane@example.com\nData Scientist with 3 years of experience.\nExperience\nData Scientist, Acme 2021 - 2024\n"
          "Built machine learning models in Python with scikit-learn, pandas and SQL.\nEducation\nBSc Statistics\n")


def post(client, url, **data):
    return client.post(url, data=data, content_type="multipart/form-data")


def test_public_pages_render(client):
    for path in ("/", "/login", "/register"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "Content-Security-Policy" in r.headers
    assert client.get("/missing").status_code == 404


def test_landing_page_offers_signup_and_login(client):
    html = client.get("/").get_data(as_text=True)
    assert "/register" in html and "/login" in html


def test_app_pages_render_when_logged_in(auth_client):
    for path in ("/dashboard", "/screenings/new", "/screenings", "/shortlist", "/match", "/insights", "/account"):
        r = auth_client.get(path)
        assert r.status_code == 200, path
        assert b"ResumeIQ" in r.data


def test_legacy_screen_url_redirects(auth_client):
    r = auth_client.get("/screen")
    assert r.status_code == 301 and r.headers["Location"].endswith("/screenings/new")


def test_health_reports_database(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok" and body["database"] == "ok" and body["model_loaded"] is True


def test_responses_are_not_cached_and_have_security_headers(auth_client):
    r = auth_client.get("/dashboard")
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["X-Frame-Options"] == "DENY" and r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Referrer-Policy"] == "same-origin"
    assert "script-src 'self'" in r.headers["Content-Security-Policy"]


def test_no_inline_scripts_or_styles_in_pages(auth_client):
    """The strict CSP blocks them, so templates must never emit them."""
    import re
    for path in ("/dashboard", "/screenings/new", "/screenings", "/shortlist", "/match", "/insights", "/account", "/"):
        html = auth_client.get(path).get_data(as_text=True)
        executable = [m for m in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html) if "application/json" not in m]
        assert not executable, (path, executable)
        assert not re.search(r"\sstyle=\"", html), path


def test_job_match_endpoint(auth_client):
    r = post(auth_client, "/api/match", resume_text=RESUME)
    d = r.get_json()
    assert r.status_code == 200 and d["roles"][0]["title"] == "Data Scientist"
    assert post(auth_client, "/api/match", sample="../app.py").status_code == 404
    assert post(auth_client, "/api/match").status_code == 400


def test_samples_download_is_restricted(auth_client):
    assert auth_client.get("/api/samples").get_json()
    assert auth_client.get("/samples/../app.py").status_code == 404
    assert auth_client.get("/samples/app.py").status_code == 404
    assert auth_client.get("/samples/Lina_Reddy_qa_engineer.doc").status_code == 200


def test_screen_validation(auth_client):
    assert post(auth_client, "/api/screen", job_description="short").status_code == 400
    assert post(auth_client, "/api/screen", job_description=JD).status_code == 400  # no resumes
    r = auth_client.post("/api/screen", data={"job_description": JD, "resumes": (io.BytesIO(b"x"), "evil.exe")},
                         content_type="multipart/form-data")
    assert r.status_code == 400 and "Unsupported" in r.get_json()["error"]
    files = [(io.BytesIO(RESUME.encode()), f"r{i}.txt") for i in range(31)]
    r = auth_client.post("/api/screen", data={"job_description": JD, "resumes": files}, content_type="multipart/form-data")
    assert r.status_code == 400 and "Too many" in r.get_json()["error"]


def test_error_pages_do_not_leak_internals():
    from conftest import make_app, register
    app = make_app(TESTING=False, PROPAGATE_EXCEPTIONS=False)

    @app.get("/boom")
    def boom():  # raises on purpose
        raise RuntimeError("secret internal detail")

    @app.get("/api/boom")
    def api_boom():
        raise RuntimeError("secret internal detail")

    c = app.test_client()
    register(c)
    r = c.get("/boom")
    assert r.status_code == 500 and b"secret internal detail" not in r.data and b"Something went wrong" in r.data
    r = c.get("/api/boom")
    assert r.status_code == 500 and r.get_json()["error"].startswith("Something went wrong")
    assert c.get("/dashboard").status_code == 200       # the app keeps serving after an error
