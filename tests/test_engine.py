import json

import numpy as np

from resume_screening import config
from resume_screening.catalog import ROLE_BY_ID, role_job_description
from resume_screening.dataset import generate_resume

HAND_WRITTEN = {
    "data-scientist": "Maria Gonzalez\nExperience\nAnalyst, Contoso Bank 2021 - Present\nTrained XGBoost models to predict loan default using pandas, numpy and SQL with cross validation. Statistical modelling and hypothesis testing.\nEducation\nMSc Statistics\nSkills: Python, R, scikit-learn, Jupyter",
    "frontend-developer": "Tom Becker\nBuilt landing pages and web apps with React, TypeScript, Tailwind CSS and Next.js for 3 years. Improved accessibility and Lighthouse scores. Figma handoff, responsive design.",
    "cybersecurity-analyst": "Priya Raman\nSOC Analyst. Monitor alerts in Splunk SIEM, investigate phishing, incident response and threat hunting. Vulnerability scans with Nessus and Nmap. ISO 27001 audits.",
    "qa-engineer": "Liam Connor\nQA Tester. Wrote test cases, regression and smoke tests, logged bugs in Jira, automated UI checks using Selenium and Java, API tests with Postman.",
    "business-analyst": "Aisha Khan\nBusiness Analyst gathering requirements, writing BRDs and user stories, process mapping with BPMN and Visio, stakeholder workshops, gap analysis. Jira, Confluence.",
}


def test_metrics_file_is_consistent():
    m = json.loads(config.METRICS_PATH.read_text())
    assert m["n_roles"] == len(ROLE_BY_ID)
    assert m["holdout"]["ensemble"]["accuracy"] > 0.9
    assert np.array(m["confusion_matrix"]["matrix"]).sum() == m["n_test"]


def test_classifier_generalises_to_hand_written_resumes(engine):
    """Resumes not produced by the synthetic generator."""
    for role_id, text in HAND_WRITTEN.items():
        top = engine.recommend_roles(text)["roles"][0]
        assert top["id"] == role_id, (role_id, top["title"])


def test_ranking_puts_matching_role_first(engine):
    import random
    rng = random.Random(123)
    ids = ["data-scientist", "frontend-developer", "devops-engineer", "qa-engineer"]
    resumes = [{"filename": f"{r}.txt", "text": generate_resume(r, rng, hybrid=False).to_text()} for r in ids]
    out = engine.screen(resumes, role_job_description(ROLE_BY_ID["devops-engineer"]), top_n=2)
    assert out["candidates"][0]["filename"] == "devops-engineer.txt"
    assert [c["shortlisted"] for c in out["candidates"]] == [True, True, False, False]
    assert out["job"]["predicted_role"]["title"] == "DevOps Engineer"
    scores = [c["score"] for c in out["candidates"]]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 100 for s in scores)
    json.dumps(out)  # must be JSON serialisable


def test_scoring_ignores_name_and_contact(engine):
    import random
    base = generate_resume("data-scientist", random.Random(9), hybrid=False)
    a = base.to_text()
    b = a.replace(base.name, "Zzyzx Qwerty").replace(base.email, "zzz@other.org")
    jd = role_job_description(ROLE_BY_ID["data-scientist"])
    out = engine.screen([{"filename": "a.txt", "text": a}, {"filename": "b.txt", "text": b}], jd)
    s = {c["filename"]: c["score"] for c in out["candidates"]}
    assert s["a.txt"] == s["b.txt"]


def test_missing_requirements_are_reweighted(engine):
    jd = "Looking for a Python and SQL developer to build machine learning models."
    out = engine.screen([{"filename": "a.txt", "text": HAND_WRITTEN["data-scientist"]}], jd)
    c = out["candidates"][0]
    assert c["components"]["experience"] is None and c["components"]["education"] is None
    assert abs(sum(c["weights_used"].values()) - 1) < 0.01


def test_recommend_returns_skills_to_learn(engine):
    r = engine.recommend_roles(HAND_WRITTEN["frontend-developer"], top_k=3)
    assert len(r["roles"]) == 3 and r["roles"][0]["skills_to_learn"] is not None
