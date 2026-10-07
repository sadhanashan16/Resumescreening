"""Sign up, log in/out, sessions, lockout, CSRF, rate limits and account management."""
import re
from datetime import timedelta

import pytest

from conftest import make_app, register
from webapp.extensions import db
from webapp.models import User, utcnow

EMAIL, PASSWORD = "alex@example.com", "Sup3rSecret99"


def login(client, email=EMAIL, password=PASSWORD, **kw):
    return client.post("/login", data={"email": email, "password": password, **kw})


def user(email=EMAIL):
    return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()


# ------------------------------------------------------------ registration
def test_register_logs_in_and_hashes_password(app, client):
    r = register(client)
    assert r.status_code == 200 and b"Welcome" in r.data
    with app.app_context():
        u = user()
        assert u and u.name == "Alex Morgan"
        assert PASSWORD not in u.password_hash and u.password_hash.startswith(("scrypt:", "pbkdf2:"))
        assert u.check_password(PASSWORD) and not u.check_password("wrong")
    assert client.get("/dashboard").status_code == 200


def test_email_is_normalised(app, client):
    register(client, email="  Alex.Case@Example.COM ")
    with app.app_context():
        assert user("alex.case@example.com") is not None


@pytest.mark.parametrize("password,fragment", [
    ("short1", "at least 8"), ("onlyletters", "letter and one number"), ("12345678", "letter and one number"),
    ("password123", "too common"), ("alex-Morgan-2024".replace("Morgan", "alex"), "e-mail name"),
])
def test_weak_passwords_rejected(app, client, password, fragment):
    r = register(client, password=password)
    assert r.status_code == 400 and fragment in r.get_data(as_text=True)
    with app.app_context():
        assert user() is None


def test_register_validation_messages(app, client):
    r = client.post("/register", data={"name": "A", "email": "not-an-email", "password": PASSWORD, "confirm": "different1"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "2–80 characters" in html and "valid email" in html and "do not match" in html


def test_duplicate_email_rejected_case_insensitively(app, client):
    register(client)
    other = app.test_client()
    r = register(other, email="ALEX@example.com", name="Someone Else")
    assert r.status_code == 400 and "already exists" in r.get_data(as_text=True)
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 1


def test_signup_can_be_disabled():
    app = make_app(ALLOW_SIGNUP=False)
    assert app.test_client().get("/register").status_code == 404


# ------------------------------------------------------------------ login
def test_login_and_logout_flow(client):
    register(client)
    client.post("/logout")
    assert client.get("/dashboard").status_code == 302
    r = login(client)
    assert r.status_code == 302 and r.headers["Location"].endswith("/dashboard")
    assert client.get("/dashboard").status_code == 200
    assert client.get("/logout").status_code == 405           # logging out needs POST (CSRF-protected)
    r = client.post("/logout")
    assert r.status_code == 302 and "/login" in r.headers["Location"]
    assert client.get("/dashboard").status_code == 302
    assert client.get("/api/candidates").status_code == 401


def test_wrong_password_and_unknown_user_look_identical(client):
    register(client)
    client.post("/logout")
    bad_pw = login(client, password="Wrong-pass-1")
    no_user = login(client, email="nobody@example.com")
    assert bad_pw.status_code == no_user.status_code == 401
    pick = lambda r: re.search(r'class="flash error"[^>]*>([^<]+)<', r.get_data(as_text=True)).group(1)  # noqa: E731
    assert pick(bad_pw) == pick(no_user) == "Invalid email or password."


def test_account_locks_after_repeated_failures(app, client):
    register(client)
    client.post("/logout")
    for _ in range(app.config["MAX_FAILED_LOGINS"]):
        assert login(client, password="Nope-nope-1").status_code == 401
    r = login(client)                                           # correct password, but locked
    assert r.status_code == 429 and "Too many failed attempts" in r.get_data(as_text=True)
    with app.app_context():
        u = user()
        u.locked_until = utcnow() - timedelta(minutes=1)         # lock expires
        db.session.commit()
    assert login(client).status_code == 302


def test_login_redirects_back_only_to_same_site_paths(client):
    register(client)
    client.post("/logout")
    r = client.get("/screenings")
    assert "/login?next=/screenings" in r.headers["Location"]
    assert login(client, next="/screenings").headers["Location"].endswith("/screenings")
    client.post("/logout")
    for evil in ("//evil.example", "https://evil.example/x", "/\\evil.example", "javascript:alert(1)"):
        r = login(client, next=evil)
        assert r.headers["Location"].endswith("/dashboard"), evil
        client.post("/logout")


def test_logged_in_users_skip_auth_pages(auth_client):
    assert auth_client.get("/login").status_code == 302
    assert auth_client.get("/register").status_code == 302


def test_protected_routes_require_login(client):
    for path in ("/dashboard", "/screenings", "/screenings/new", "/screenings/1", "/shortlist", "/match",
                 "/insights", "/account"):
        r = client.get(path)
        assert r.status_code == 302 and "/login" in r.headers["Location"], path
    for method, path in (("get", "/api/candidates"), ("get", "/api/screenings"), ("post", "/api/screen"),
                         ("post", "/api/match"), ("get", "/api/roles"), ("get", "/api/model"),
                         ("get", "/api/candidates/export.csv"), ("patch", "/api/candidates/1")):
        r = getattr(client, method)(path)
        assert r.status_code == 401 and r.get_json()["error"], path
    assert client.get("/health").status_code == 200


# --------------------------------------------------------------- password
def test_change_password_rotates_sessions(app, client):
    register(client)
    second = app.test_client()
    login(second)
    assert second.get("/dashboard").status_code == 200

    r = client.post("/account/password", data={"current_password": "wrong", "new_password": "New-Passw0rd!", "confirm": "New-Passw0rd!"})
    assert r.status_code == 400 and "incorrect" in r.get_data(as_text=True)
    r = client.post("/account/password", data={"current_password": PASSWORD, "new_password": PASSWORD, "confirm": PASSWORD})
    assert r.status_code == 400 and "different" in r.get_data(as_text=True)

    r = client.post("/account/password", data={"current_password": PASSWORD, "new_password": "New-Passw0rd!", "confirm": "New-Passw0rd!"})
    assert r.status_code == 302
    assert client.get("/dashboard").status_code == 200           # the session that changed it stays signed in
    assert second.get("/dashboard").status_code == 302           # every other session is signed out
    client.post("/logout")
    assert login(client).status_code == 401 and login(client, password="New-Passw0rd!").status_code == 302


def test_delete_account_requires_password_and_removes_data(app, auth_client):
    r = auth_client.post("/api/screen", data={"job_description": "We are hiring a Data Scientist who knows Python and SQL and statistics.",
                                              "use_samples": "1"}, content_type="multipart/form-data")
    assert r.status_code == 201
    assert auth_client.post("/account/delete", data={"password": "wrong"}).status_code == 400
    r = auth_client.post("/account/delete", data={"password": PASSWORD})
    assert r.status_code == 302
    with app.app_context():
        from webapp.models import Candidate, Screening
        assert user() is None
        assert db.session.scalar(db.select(db.func.count(Candidate.id))) == 0
        assert db.session.scalar(db.select(db.func.count(Screening.id))) == 0
    assert login(auth_client).status_code == 401


# ------------------------------------------------------- CSRF / rate limits
def _token(client, path="/login"):
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', client.get(path).get_data(as_text=True)).group(1)


def test_csrf_is_enforced_on_forms_and_api():
    app = make_app(WTF_CSRF_ENABLED=True)
    c = app.test_client()
    assert c.post("/register", data={"name": "Alex Morgan", "email": EMAIL, "password": PASSWORD, "confirm": PASSWORD}).status_code == 400
    tok = _token(c, "/register")
    r = c.post("/register", data={"name": "Alex Morgan", "email": EMAIL, "password": PASSWORD, "confirm": PASSWORD, "csrf_token": tok})
    assert r.status_code == 302
    assert c.post("/logout").status_code == 400                   # logout without a token is refused
    page_token = re.search(r'name="csrf-token" content="([^"]+)"', c.get("/dashboard").get_data(as_text=True)).group(1)
    assert c.post("/api/screen", data={}).get_json()["error"].startswith("Your session expired")
    r = c.post("/api/screen", data={"job_description": "short"}, headers={"X-CSRFToken": page_token})
    assert r.status_code == 400 and "job description" in r.get_json()["error"]
    assert c.post("/logout", data={"csrf_token": page_token}).status_code == 302


def test_login_is_rate_limited():
    app = make_app(RATELIMIT_ENABLED=True, RATELIMIT_STORAGE_URI="memory://")
    c = app.test_client()
    codes = [c.post("/login", data={"email": "x@example.com", "password": "Whatever-1"}).status_code for _ in range(18)]
    assert codes[0] == 401 and 429 in codes and codes.index(429) <= 15


def test_session_cookie_flags_in_production_mode():
    app = make_app(SESSION_COOKIE_SECURE=True, PRODUCTION=True)
    c = app.test_client()
    r = register(c, follow=False)
    cookie = [v for k, v in r.headers if k == "Set-Cookie" and v.startswith("resumeiq_session")][0]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=Lax" in cookie
    assert "Strict-Transport-Security" in r.headers
