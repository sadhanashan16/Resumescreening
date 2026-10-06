from datetime import date

from resume_screening.catalog import ROLES
from resume_screening.parser import (estimate_experience, extract_education, parse_job_description,
                                     parse_resume, split_sections)
from resume_screening.skills import SKILL_BY_NAME, extract_skills, related_skills
from resume_screening.text_utils import normalize_for_model, strip_contact_info


def test_catalog_skills_exist_in_taxonomy():
    for role in ROLES:
        for s in role["core"] + role["secondary"]:
            assert s in SKILL_BY_NAME, (role["id"], s)


def test_skill_aliases_and_punctuation():
    text = "Python, C++, C#, Node.js, sklearn, k8s, CI/CD, PL/SQL and .NET."
    assert {"Python", "C++", "C#", "Node.js", "Scikit-learn", "Kubernetes", "CI/CD", "SQL", ".NET"} <= set(extract_skills(text))


def test_java_is_not_javascript():
    assert extract_skills("Experienced with JavaScript") == ["JavaScript"]
    assert extract_skills("Core Java developer") == ["Java"]


def test_ambiguous_words_are_not_skills():
    assert extract_skills("We excel in teamwork. React to change quickly. Spring 2019 semester.") == ["Teamwork"]
    assert "Excel" in extract_skills("Skills: SQL, Excel, Tableau")
    assert "React" in extract_skills("Built UIs with React and Redux")


def test_related_skills():
    assert "MySQL" in related_skills("PostgreSQL")


def test_normalize_collapses_spelling_variants():
    assert normalize_for_model("sklearn") == normalize_for_model("scikit-learn")
    assert "@" not in normalize_for_model("mail me at a.b@example.com or +91 98765 43210")
    assert "98765" not in normalize_for_model("call +91 98765 43210")


def test_strip_contact_keeps_year_ranges():
    assert "2019 - 2022" in strip_contact_info("Engineer 2019 - 2022")


RESUME = """JOHN SMITH
john.smith@mail.com | +91 98765 43210

Summary
Data scientist with 4+ years of experience in ML.

Experience
Data Scientist, Acme Corp  Jan 2019 - Mar 2022
Senior DS, Beta Inc   06/2021 - Present

Education
B.Tech in Computer Science, XYZ University 2014 - 2018
M.S. in Data Science

Skills
Python, SQL, scikit-learn
"""


def test_parse_resume_fields():
    p = parse_resume(RESUME, "john.pdf", today=date(2025, 6, 1))
    assert p["name"] == "John Smith"
    assert p["email"] == "john.smith@mail.com"
    assert p["phone"] == "+91 98765 43210"
    assert p["education"]["level"] == 4
    assert {"Python", "SQL", "Scikit-learn", "Machine Learning"} <= set(p["skills"])
    # Jan 2019 -> Jun 2025 (overlapping jobs are merged, not double counted); education dates excluded
    assert p["experience_years"] == 6.4
    assert "john.smith" not in p["blind_text"].lower() and "John Smith" not in p["blind_text"]


def test_experience_overlap_and_explicit():
    s = split_sections("Experience\nA 2020 - 2022\nB 2021 - 2023\n")
    # 2020-01 .. 2023-12 merged (overlap counted once), not 2 + 2 = 4 separate years
    assert estimate_experience(s, "", date(2025, 1, 1)) == 3.9
    s = split_sections("Summary\n10 years of experience in sales\n")
    assert estimate_experience(s, "10 years of experience in sales") == 10.0


def test_education_levels():
    assert extract_education({}, "PhD in Physics")["level"] == 5
    assert extract_education({}, "MBA, XYZ")["level"] == 4
    assert extract_education({}, "Bachelor of Engineering")["level"] == 3
    assert extract_education({}, "Diploma in IT")["level"] == 2
    assert extract_education({}, "I use MS Office daily")["level"] == 0
    assert extract_education({}, "nothing")["label"] == "Not detected"


def test_name_fallback_to_filename():
    assert parse_resume("python developer with skills in sql and flask " * 3, "priya_sharma_resume.pdf")["name"] == "Priya Sharma"


def test_job_description_parsing():
    jd = parse_job_description("We are hiring a Data Scientist.\nRequires 3+ years of experience, Bachelor's degree, Python and SQL.")
    assert jd["title"] == "Data Scientist" and jd["min_years"] == 3 and jd["education_level"] == 3
    assert set(jd["skills"]) == {"Python", "SQL"}
