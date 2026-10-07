"""Screening persistence, shortlist management, filtering, export and per-user isolation."""
import io

import pytest

from resume_screening.catalog import ROLE_BY_ID, role_job_description
from resume_screening.extractor import extract_text
from webapp.api import list_samples

JD = role_job_description(ROLE_BY_ID["data-scientist"])
RESUME = ("Jane Doe\njane@example.com\nData Scientist with 3 years of experience.\nExperience\nData Scientist, Acme 2021 - 2024\n"
          "Built machine learning models in Python with scikit-learn, pandas and SQL.\nEducation\nBSc Statistics\n")


def screen(client, **extra):
    data = {"job_description": JD, "use_samples": "1", "top_n": "3", **extra}
    return client.post("/api/screen", data=data, content_type="multipart/form-data")


def patch(client, cid, **body):
    return client.patch(f"/api/candidates/{cid}", json=body)


@pytest.fixture()
def run(auth_client):
    r = screen(auth_client)
    assert r.status_code == 201
    return r.get_json()


# ----------------------------------------------------- ML output integrity
def test_stored_results_are_exactly_the_ml_engine_output(auth_client, engine, run):
    resumes = [{"filename": p.name, "text": extract_text(p.name, p.read_bytes())} for p in list_samples()]
    direct = engine.screen(resumes, JD, "", top_n=3)
    expected = {c["filename"]: c for c in direct["candidates"]}
    got = {c["filename"]: c for c in run["candidates"]}
    assert set(got) == set(expected) and len(got) == len(list_samples())
    for name, c in got.items():
        e = expected[name]
        assert c["score"] == e["score"] and c["grade"] == e["grade"] and c["rank"] == e["rank"]
        assert c["matched_skills"] == e["matched_skills"] and c["missing_skills"] == e["missing_skills"]
        assert c["components"] == e["components"] and c["experience_years"] == e["experience_years"]
        assert c["recommended"] == e["shortlisted"]
    assert run["job"]["skills"] == direct["job"]["skills"]
    assert sum(c["recommended"] for c in run["candidates"]) == 3


def test_screening_is_saved_and_listed(auth_client, run):
    assert run["id"] and run["url"].endswith(f"/screenings/{run['id']}") and run["total"] == len(list_samples())
    ranks = [c["rank"] for c in run["candidates"]]
    assert ranks == sorted(ranks) and ranks[0] == 1
    assert all(c["status"] == "pending" for c in run["candidates"])

    lst = auth_client.get("/api/screenings").get_json()
    assert lst["total"] == 1 and lst["items"][0]["id"] == run["id"] and lst["items"][0]["pending"] == run["total"]
    detail = auth_client.get(f"/api/screenings/{run['id']}").get_json()
    assert detail["job_title"] == run["job_title"] and len(detail["candidates"]) == run["total"]
    page = auth_client.get(f"/screenings/{run['id']}")
    assert page.status_code == 200 and run["job_title"].encode() in page.data


def test_upload_and_unreadable_files(auth_client):
    files = [(io.BytesIO(RESUME.encode()), "jane.txt"), (io.BytesIO(b"not a pdf"), "bad.pdf")]
    r = auth_client.post("/api/screen", data={"job_description": JD, "resumes": files, "job_title": "Data Scientist"},
                         content_type="multipart/form-data")
    d = r.get_json()
    assert r.status_code == 201 and d["total"] == 1 and d["candidates"][0]["name"] == "Jane Doe"
    assert d["errors"][0]["filename"] == "bad.pdf"
    saved = auth_client.get(f"/api/screenings/{d['id']}").get_json()
    assert saved["errors"][0]["filename"] == "bad.pdf"            # failures are kept for the results page


# ------------------------------------------------------- shortlist workflow
def test_shortlist_reject_reset_and_notes(auth_client, run):
    cid = run["candidates"][0]["id"]
    r = patch(auth_client, cid, status="shortlisted", notes="  Strong on ML, call back  ")
    d = r.get_json()
    assert r.status_code == 200 and d["status"] == "shortlisted" and d["notes"] == "Strong on ML, call back" and d["shortlisted_at"]
    assert patch(auth_client, cid, status="rejected").get_json()["shortlisted_at"] is None
    assert patch(auth_client, cid, status="pending").get_json()["status"] == "pending"
    assert patch(auth_client, cid, status="hired").status_code == 400
    assert patch(auth_client, cid, notes="x" * 5001).status_code == 400
    assert patch(auth_client, cid, notes=123).status_code == 400
    assert auth_client.patch(f"/api/candidates/{cid}", data="nope", content_type="text/plain").status_code == 400


def test_bulk_status_by_ids_and_by_recommendation(auth_client, run):
    r = auth_client.post("/api/candidates/bulk", json={"screening_id": run["id"], "scope": "recommended", "status": "shortlisted"})
    assert r.get_json()["updated"] == 3
    counts = auth_client.get("/api/candidates", query_string={"screening_id": run["id"]}).get_json()["counts"]
    assert counts["shortlisted"] == 3 and counts["pending"] == run["total"] - 3
    shortlisted = auth_client.get("/api/candidates", query_string={"status": "shortlisted"}).get_json()["items"]
    assert {c["rank"] for c in shortlisted} == {1, 2, 3}
    ids = [c["id"] for c in run["candidates"][5:8]]
    assert auth_client.post("/api/candidates/bulk", json={"ids": ids, "status": "rejected"}).get_json()["updated"] == 3
    assert auth_client.post("/api/candidates/bulk", json={"ids": ids, "status": "bogus"}).status_code == 400
    assert auth_client.post("/api/candidates/bulk", json={"ids": [], "status": "rejected"}).status_code == 400
    assert auth_client.post("/api/candidates/bulk", json={"screening_id": run["id"], "scope": "x", "status": "rejected"}).status_code == 400
    assert auth_client.post("/api/candidates/bulk", json={"status": "rejected"}).status_code == 400


# -------------------------------------------------- search, filter and sort
def test_search_filter_sort_and_pagination(auth_client, run):
    def get(**q):
        return auth_client.get("/api/candidates", query_string={"screening_id": run["id"], **q}).get_json()

    scores = [c["score"] for c in get(sort="score", order="desc")["items"]]
    assert scores == sorted(scores, reverse=True)
    assert [c["rank"] for c in get(sort="rank")["items"]] == sorted(c["rank"] for c in run["candidates"])
    names = [c["name"].lower() for c in get(sort="name")["items"]]
    assert names == sorted(names)

    k8s = get(q="kubernetes")
    assert 0 < k8s["total"] < run["total"] and all("Kubernetes" in c["skills"] for c in k8s["items"])
    assert get(q="kubernetes docker")["total"] <= k8s["total"]       # every word must match
    assert get(q="zzzznomatch")["total"] == 0
    assert get(q="100%")["total"] == 0                               # LIKE wildcards are escaped

    strong = get(grade="strong")
    assert all(c["grade"] == "Strong match" for c in strong["items"]) and strong["total"] >= 1
    assert get(grade="all")["total"] == run["total"]
    assert get(min_score=50)["total"] == sum(1 for c in run["candidates"] if c["score"] >= 50)

    page = get(per_page=5, page=2)
    assert len(page["items"]) == 5 and page["page"] == 2 and page["pages"] == 3 and page["total"] == run["total"]
    assert get(per_page=5, page=99)["items"] == []
    for bad in ({"status": "x"}, {"grade": "x"}, {"sort": "x"}):
        assert auth_client.get("/api/candidates", query_string=bad).status_code == 400


# --------------------------------------------------------------- CSV export
def test_csv_export_is_filtered_and_formula_safe(auth_client, run):
    cid = run["candidates"][0]["id"]
    patch(auth_client, cid, status="shortlisted", notes="=HYPERLINK(\"http://evil\")")
    r = auth_client.get("/api/candidates/export.csv", query_string={"status": "shortlisted"})
    assert r.status_code == 200 and r.mimetype == "text/csv" and "attachment" in r.headers["Content-Disposition"]
    text = r.get_data(as_text=True).lstrip("﻿")
    lines = [l for l in text.splitlines() if l.strip()]
    assert lines[0].startswith("Rank,Name,Email") and len(lines) == 2
    assert "'=HYPERLINK" in text and ',=HYPERLINK' not in text
    whole = auth_client.get(f"/api/screenings/{run['id']}/export.csv").get_data(as_text=True)
    assert len([l for l in whole.splitlines() if l.strip()]) == run["total"] + 1


def test_csv_safe_helper():
    from webapp.api import csv_safe
    assert csv_safe("=1+1") == "'=1+1" and csv_safe("@cmd") == "'@cmd" and csv_safe("+cmd") == "'+cmd"
    assert csv_safe("+44 7876 340822") == "+44 7876 340822" and csv_safe("-5") == "-5" and csv_safe(None) == ""


# ----------------------------------------------------------------- deletion
def test_delete_candidate_and_screening(auth_client, run):
    cid = run["candidates"][0]["id"]
    assert auth_client.delete(f"/api/candidates/{cid}").status_code == 200
    assert auth_client.get(f"/api/candidates/{cid}").status_code == 404
    assert auth_client.get(f"/api/screenings/{run['id']}").get_json()["candidates"].__len__() == run["total"] - 1
    r = auth_client.post(f"/screenings/{run['id']}/delete", follow_redirects=True)
    assert r.status_code == 200 and b"Deleted the screening" in r.data
    assert auth_client.get(f"/api/screenings/{run['id']}").status_code == 404
    assert auth_client.get("/api/candidates").get_json()["total"] == 0


# ---------------------------------------------------------------- isolation
def test_users_cannot_see_or_change_each_others_data(auth_client, other_client, run):
    cid = run["candidates"][0]["id"]
    sid = run["id"]
    assert other_client.get("/api/candidates").get_json()["total"] == 0
    assert other_client.get("/api/screenings").get_json()["total"] == 0
    assert other_client.get(f"/api/screenings/{sid}").status_code == 404
    assert other_client.get(f"/screenings/{sid}").status_code == 404
    assert other_client.get(f"/api/candidates/{cid}").status_code == 404
    assert patch(other_client, cid, status="shortlisted").status_code == 404
    assert other_client.delete(f"/api/candidates/{cid}").status_code == 404
    assert other_client.delete(f"/api/screenings/{sid}").status_code == 404
    assert other_client.post(f"/screenings/{sid}/delete").status_code == 404
    assert other_client.get(f"/api/screenings/{sid}/export.csv").status_code == 404
    assert other_client.post("/api/candidates/bulk", json={"screening_id": sid, "scope": "all", "status": "rejected"}).status_code == 404
    assert other_client.post("/api/candidates/bulk", json={"ids": [cid], "status": "rejected"}).get_json()["updated"] == 0
    assert other_client.get("/api/candidates", query_string={"screening_id": sid}).get_json()["total"] == 0
    assert "Strong" not in other_client.get("/api/candidates/export.csv").get_data(as_text=True)
    # the owner's data is untouched
    assert auth_client.get(f"/api/candidates/{cid}").get_json()["status"] == "pending"
    assert auth_client.get("/api/candidates").get_json()["total"] == run["total"]


# -------------------------------------------------------------------- pages
def test_dashboard_reflects_real_counts(auth_client):
    html = auth_client.get("/dashboard").get_data(as_text=True)
    assert "Get started in four steps" in html                        # empty state for new users
    run = screen(auth_client).get_json()
    auth_client.post("/api/candidates/bulk", json={"screening_id": run["id"], "scope": "recommended", "status": "shortlisted"})
    html = auth_client.get("/dashboard").get_data(as_text=True)
    assert "Get started in four steps" not in html and "Recent screenings" in html
    assert run["job_title"] in html and f'<b>{run["total"]}</b><span>Candidates screened</span>' in html
    assert '<b>3</b><span>Shortlisted</span>' in html
    assert auth_client.get("/shortlist").status_code == 200
    assert run["job_title"] in auth_client.get("/screenings").get_data(as_text=True)
    assert "No screenings match" in auth_client.get("/screenings?q=zzzz").get_data(as_text=True)


def test_real_uploads_in_every_supported_format(auth_client):
    """PDF, DOCX, legacy DOC and TXT files go through the real multipart upload + extraction path."""
    files = [(io.BytesIO(p.read_bytes()), p.name) for p in list_samples()]
    r = auth_client.post("/api/screen", data={"job_description": JD, "resumes": files}, content_type="multipart/form-data")
    d = r.get_json()
    assert r.status_code == 201 and d["total"] == len(files) and not d["errors"]
    assert {p.suffix for p in list_samples()} >= {".pdf", ".docx", ".doc", ".txt"}
    assert all(c["skills"] for c in d["candidates"])


def test_oversized_upload_returns_json_error(app):
    from conftest import make_app, register
    small = make_app(MAX_CONTENT_LENGTH=2000)
    c = small.test_client()
    register(c)
    r = c.post("/api/screen", data={"job_description": JD, "resumes": (io.BytesIO(b"x" * 5000), "big.txt")},
               content_type="multipart/form-data")
    assert r.status_code == 413 and "too large" in r.get_json()["error"]
