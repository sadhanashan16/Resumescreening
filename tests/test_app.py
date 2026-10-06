import io

from resume_screening.catalog import ROLE_BY_ID, role_job_description

JD = role_job_description(ROLE_BY_ID["data-scientist"])
RESUME = ("Jane Doe\njane@example.com\nData Scientist with 3 years of experience.\nExperience\nData Scientist, Acme 2021 - 2024\n"
          "Built machine learning models in Python with scikit-learn, pandas and SQL.\nEducation\nBSc Statistics\n")


def test_pages_render(client):
    for path in ("/", "/screen", "/match", "/insights"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "Content-Security-Policy" in r.headers
    assert client.get("/missing").status_code == 404


def test_health(client):
    assert client.get("/health").get_json()["status"] == "ok"


def test_screen_with_upload_and_samples(client):
    r = client.post("/api/screen", data={
        "job_description": JD, "top_n": "2", "use_samples": "1",
        "resumes": [(io.BytesIO(RESUME.encode()), "jane.txt"), (io.BytesIO(b"junk"), "bad.pdf")],
    }, content_type="multipart/form-data")
    d = r.get_json()
    assert r.status_code == 200
    assert d["summary"]["total"] > 10 and d["shortlist_size"] == 2
    assert any(e["filename"] == "bad.pdf" for e in d["errors"])
    assert "jane.txt" in {c["filename"] for c in d["candidates"]}
    assert sum(c["shortlisted"] for c in d["candidates"]) == 2


def test_screen_validation(client):
    post = lambda **kw: client.post("/api/screen", data=kw, content_type="multipart/form-data")  # noqa: E731
    assert post(job_description="short").status_code == 400
    assert post(job_description=JD).status_code == 400  # no resumes
    r = post(job_description=JD, resumes=(io.BytesIO(b"x"), "evil.exe"))
    assert r.status_code == 400 and "Unsupported" in r.get_json()["error"]


def test_screen_rejects_too_many_files(client):
    files = [(io.BytesIO(RESUME.encode()), f"r{i}.txt") for i in range(31)]
    r = client.post("/api/screen", data={"job_description": JD, "resumes": files}, content_type="multipart/form-data")
    assert r.status_code == 400 and "Too many" in r.get_json()["error"]


def test_match_endpoint(client):
    r = client.post("/api/match", data={"resume_text": RESUME}, content_type="multipart/form-data")
    d = r.get_json()
    assert r.status_code == 200 and d["roles"][0]["title"] == "Data Scientist"
    r = client.post("/api/match", data={"sample": "../app.py"}, content_type="multipart/form-data")
    assert r.status_code == 404
    assert client.post("/api/match", data={}, content_type="multipart/form-data").status_code == 400


def test_samples_download_is_restricted(client):
    assert client.get("/api/samples").get_json()
    assert client.get("/samples/../app.py").status_code == 404
    assert client.get("/samples/app.py").status_code == 404
