"""Synthetic labelled resumes for training.

No real resume corpus ships with this project (resumes are personal data), so
resumes are sampled from the role catalog with deliberate noise: skills shared
between neighbouring roles, "career-changer" resumes that mix two roles,
varying seniority, education and formatting. To train on real data pass a CSV
to ``python -m resume_screening.train --csv``.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .catalog import ROLE_BY_ID, ROLES
from .skills import skill_category

FIRST = ["Aarav", "Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Arjun", "Divya", "Karthik", "Meera",
         "Emily", "Daniel", "Sophia", "James", "Olivia", "Michael", "Isabella", "David", "Grace", "Samuel",
         "Fatima", "Omar", "Lina", "Yusuf", "Chen", "Mei", "Hiro", "Aiko", "Lucas", "Elena",
         "Noah", "Amara", "Kwame", "Zara", "Ravi", "Nisha", "Tomas", "Ingrid", "Pedro", "Carla"]
LAST = ["Sharma", "Patel", "Iyer", "Reddy", "Nair", "Gupta", "Mehta", "Singh", "Kumar", "Das",
        "Johnson", "Smith", "Brown", "Williams", "Taylor", "Davis", "Miller", "Wilson", "Clark", "Lewis",
        "Khan", "Hassan", "Ali", "Wang", "Li", "Tanaka", "Sato", "Garcia", "Rossi", "Muller",
        "Okafor", "Mensah", "Novak", "Larsen", "Costa", "Fernandez", "Silva", "Ivanov", "Kim", "Park"]
COMPANIES = ["Infosys", "TCS", "Wipro", "Accenture", "Capgemini", "Zoho", "Freshworks", "Flipkart", "Paytm", "Swiggy",
             "Nimbus Labs", "BlueOrbit", "Northwind Systems", "Pixel & Co", "Helix Analytics", "Quantum Retail", "Brightpath",
             "CloudNine Tech", "Vertex Solutions", "Orion Digital", "Lumen Software", "Apex Financial", "Medisys", "Greenfield Energy",
             "Nova Logistics", "Skyline Media", "DataHarbor", "CodeCraft", "Atlas Insurance", "Pioneer Telecom"]
UNIVERSITIES = ["Anna University", "VIT University", "IIT Madras", "NIT Trichy", "BITS Pilani", "Delhi University", "Pune University",
                "University of Texas", "Arizona State University", "University of Toronto", "Univ. of Manchester", "TU Munich",
                "National University of Singapore", "University of Melbourne", "SRM Institute of Science and Technology"]
GENERIC_SKILLS = ["Git", "Agile", "Communication", "Teamwork", "Problem Solving", "Documentation", "Linux"]
BACHELORS = ["B.Tech in {f}", "B.E. in {f}", "B.Sc in {f}", "Bachelor of Science in {f}", "Bachelor of Engineering in {f}", "BCA", "B.Com"]
MASTERS = ["M.Tech in {f}", "M.Sc in {f}", "MS in {f}", "Master of Science in {f}", "MCA", "MBA"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
END_YEAR = 2025
GENERIC_BULLETS = [
    "Collaborated with cross-functional teams to deliver projects on schedule",
    "Participated in code reviews, sprint planning and daily stand-ups",
    "Documented processes and shared knowledge with the wider team",
    "Worked closely with stakeholders to understand requirements and prioritise work",
    "Mentored interns and new joiners and contributed to team best practices",
    "Delivered {n} projects on time while maintaining high quality standards",
    "Investigated and resolved production issues, improving stability by {pct}%",
]


@dataclass
class GeneratedResume:
    role_id: str
    name: str
    email: str
    phone: str
    years: float
    sections: list[tuple[str, list[str]]] = field(default_factory=list)

    def to_text(self) -> str:
        out = [self.name, f"{self.email} | {self.phone}", ""]
        for heading, lines in self.sections:
            out.append(heading)
            out.extend(lines)
            out.append("")
        return "\n".join(out).strip() + "\n"


def _fill(template: str, rng: random.Random, skills: list[str]) -> str:
    return template.format(
        s=rng.choice(skills), pct=rng.randint(8, 45), n=rng.randint(3, 60),
        n2=rng.randint(20, 500), a=rng.randint(0, 9), b=rng.randint(0, 9),
    )


def _pick_title(role: dict, rng: random.Random, years: float) -> str:
    options = [t for t in role["titles"] if "Intern" not in t]
    if years < 2:
        options = [t for t in options if not t.startswith("Senior")] or options
    elif years < 5:
        options = [t for t in options if not t.startswith(("Senior", "Junior"))] or options
    return rng.choice(options)


def _bullets(role: dict, rng: random.Random, k: int, hybrid: bool) -> list[str]:
    """Experience bullets: mostly role-specific, but some generic or borrowed
    from a neighbouring role so the label is never trivially recoverable."""
    out = []
    for _ in range(k):
        x = rng.random()
        if x < 0.28:
            out.append(rng.choice(GENERIC_BULLETS))
        elif x < 0.28 + (0.35 if hybrid else 0.14) and role["adjacent"]:
            out.append(rng.choice(ROLE_BY_ID[rng.choice(role["adjacent"])]["bullets"]))
        else:
            out.append(rng.choice(role["bullets"]))
    return out


def generate_resume(role_id: str, rng: random.Random, hybrid: bool | None = None) -> GeneratedResume:
    role = ROLE_BY_ID[role_id]
    if hybrid is None:
        hybrid = rng.random() < 0.25

    years = rng.choice([0, 0.5, 1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 8, 10, 12])
    core_rate = rng.uniform(0.35, 0.9)  # how completely this candidate lists the role's core skills
    skills = [s for s in role["core"] if rng.random() < core_rate]
    skills += [s for s in role["secondary"] if rng.random() < core_rate / 2]
    if not skills:
        skills = [rng.choice(role["core"])]
    # skill overlap with neighbouring roles
    for adj in role["adjacent"]:
        if rng.random() < (0.55 if hybrid else 0.25):
            other = ROLE_BY_ID[adj]
            k = rng.randint(2, 5) if hybrid else rng.randint(1, 3)
            skills += rng.sample(other["core"], min(k, len(other["core"])))
    skills += [g for g in GENERIC_SKILLS if rng.random() < 0.35]
    skills = list(dict.fromkeys(skills))
    rng.shuffle(skills)
    if rng.random() < 0.2:  # sparse resume: short skills list
        skills = skills[: rng.randint(3, 6)]

    first, last = rng.choice(FIRST), rng.choice(LAST)
    name = f"{first} {last}"
    email = f"{first}.{last}{rng.randint(1, 99) if rng.random() < 0.4 else ''}@example.com".lower()
    phone = rng.choice([f"+91 {rng.randint(70000, 99999)} {rng.randint(10000, 99999)}",
                        f"+1 ({rng.randint(200, 999)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}",
                        f"+44 7{rng.randint(100, 999)} {rng.randint(100000, 999999)}"])
    r = GeneratedResume(role["id"], name, email, phone, years)

    level = "Junior " if years < 2 and rng.random() < 0.5 else ("Senior " if years >= 6 and rng.random() < 0.6 else "")
    title_role = ROLE_BY_ID[rng.choice(role["adjacent"])] if rng.random() < 0.12 else role
    base_title = _pick_title(title_role, rng, years)
    tech_skills = [x for x in skills if x not in GENERIC_SKILLS and skill_category(x) != "soft"] or skills
    title = base_title if base_title.startswith(("Junior", "Senior")) else level + base_title
    if years >= 1 and rng.random() < 0.7:
        summary = (f"{title.replace('Junior ', '').replace('Senior ', '')} with {int(years) if years >= 1 else 1}+ years of experience "
                   f"in {', '.join(skills[:3])}." + (" " + role["description"] if rng.random() < 0.5 else ""))
    elif years < 1:
        summary = (f"Motivated graduate seeking a {role['title']} position. "
                   f"Hands-on project experience with {', '.join(skills[:3])}.")
    else:
        summary = f"{role['title']} focused on {', '.join(skills[:2])}. " + role["responsibilities"][0] + "."
    r.sections.append(("Summary", [summary]))

    r.sections.append((rng.choice(["Skills", "Technical Skills", "Core Competencies"]),
                       [rng.choice(["", "Technologies: ", "Tools: "]) + ", ".join(skills)]))

    # experience: split the years across 1-3 positions, newest first
    exp_lines: list[str] = []
    if years >= 0.5:
        n_jobs = 1 if years < 2 else rng.randint(1, min(3, int(years)))
        chunk_months = [max(6, int(years * 12 / n_jobs))] * n_jobs
        end = END_YEAR * 12 + rng.randint(0, 5)
        present = rng.random() < 0.6
        for i, months in enumerate(chunk_months):
            start = end - months
            fmt = lambda idx: f"{MONTHS[idx % 12]} {idx // 12}"  # noqa: E731
            end_label = "Present" if (present and i == 0) else fmt(end)
            job_title = title if i == 0 else _pick_title(title_role if rng.random() < 0.5 else role, rng, years)
            exp_lines.append(f"{job_title}, {rng.choice(COMPANIES)}  {fmt(start)} - {end_label}")
            for tpl in _bullets(role, rng, rng.randint(2, 4), hybrid):
                exp_lines.append("- " + _fill(tpl, rng, tech_skills))
            end = start - rng.randint(1, 4)
    elif rng.random() < 0.7:
        exp_lines.append(f"{role['title']} Intern, {rng.choice(COMPANIES)}  Jun {END_YEAR - 1} - Aug {END_YEAR - 1}")
        for tpl in _bullets(role, rng, 2, hybrid):
            exp_lines.append("- " + _fill(tpl, rng, tech_skills))
    if exp_lines:
        r.sections.append((rng.choice(["Experience", "Work Experience", "Professional Experience"]), exp_lines))

    # projects
    proj = []
    for tpl in _bullets(role, rng, rng.randint(1, 2), hybrid):
        proj.append("- " + _fill(tpl, rng, tech_skills))
    if years < 3 or rng.random() < 0.4:
        r.sections.append(("Projects", proj))

    # education
    field_ = rng.choice(role["edu_fields"])
    masters_p = 0.45 if role["id"] in ("data-scientist", "machine-learning-engineer") else 0.2
    grad_year = END_YEAR - int(years) - rng.randint(0, 1)
    edu = [f"{rng.choice(BACHELORS).format(f=field_)}, {rng.choice(UNIVERSITIES)}  {grad_year - 4} - {grad_year}"]
    if rng.random() < masters_p:
        edu.insert(0, f"{rng.choice(MASTERS).format(f=field_)}, {rng.choice(UNIVERSITIES)}  {grad_year} - {grad_year + 2}")
    r.sections.append(("Education", edu))

    if rng.random() < 0.55:
        r.sections.append(("Certifications", ["- " + c for c in rng.sample(role["certs"], rng.randint(1, 2))]))
    return r


def generate_dataset(n_per_role: int = 200, seed: int = 42) -> list[tuple[str, str]]:
    """Return ``[(resume_text, role_id), ...]`` with balanced classes."""
    rng = random.Random(seed)
    rows = []
    for role in ROLES:
        for _ in range(n_per_role):
            rows.append((generate_resume(role["id"], rng).to_text(), role["id"]))
    rng.shuffle(rows)
    return rows
