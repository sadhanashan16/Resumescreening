"""Rule-based NLP: pull structured facts out of resume and job-description text."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .skills import extract_skills
from .text_utils import EMAIL_RE, PHONE_RE, strip_contact_info

# ----------------------------------------------------------------- sections
_HEADINGS = {
    "summary": r"(?:professional |career |personal )?(?:summary|profile|objective)|about me|career objective",
    "skills": r"(?:technical |key |core |it )?skills(?: set| summary)?|core competencies|technologies|tech stack|tools(?: and technologies)?|areas of expertise",
    "experience": r"(?:work |professional |relevant |industry )?experience|employment(?: history)?|work history|career history|internships?",
    "education": r"education(?:al)?(?: background| qualifications?)?|academic(?:s| background| qualifications?)|qualifications?",
    "projects": r"(?:academic |personal |key )?projects",
    "certifications": r"certifications?(?: and (?:courses|training))?|licen[sc]es|courses|training",
    "other": r"awards?(?: and honou?rs)?|achievements|interests|hobbies|languages|references|publications|volunteer(?:ing)?|activities|extra[- ]?curricular",
}
_HEADING_RES = {k: re.compile(rf"^(?:{v})$", re.I) for k, v in _HEADINGS.items()}


def split_sections(text: str) -> dict[str, str]:
    """Split resume text into sections keyed by heading type."""
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        stripped = re.sub(r"[^A-Za-z &/]", "", line).strip()
        kind = None
        if 2 <= len(stripped) <= 40 and len(line.strip()) <= 45:
            for k, rx in _HEADING_RES.items():
                if rx.match(stripped):
                    kind = k
                    break
        if kind:
            current = kind
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


# ------------------------------------------------------------------ contact
_NOT_NAME = re.compile(
    r"resume|curriculum|vitae|\bcv\b|summary|profile|objective|experience|education|skills|@|http|www|linkedin|github|\d",
    re.I,
)


def extract_name(text: str, filename: str = "") -> str:
    for line in text.splitlines()[:6]:
        line = line.strip(" \t|-,:")
        if not line or _NOT_NAME.search(line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'’-]*", w) for w in words):
            return " ".join(w.capitalize() if w.isupper() else w for w in words)
    stem = Path(filename).stem if filename else ""
    stem = re.sub(r"[_\-.]+|\d+", " ", stem)
    stem = re.sub(r"(?i)\b(resume|cv|curriculum vitae)\b", " ", stem).strip()
    stem = re.sub(r"\s+", " ", stem)
    return stem.title() if stem else "Unknown candidate"


def extract_email(text: str) -> str | None:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def extract_phone(text: str) -> str | None:
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 14 and not re.search(r"(19|20)\d{2}\D{1,4}(19|20)\d{2}", m.group(0)):
            return m.group(0).strip()
    return None


# --------------------------------------------------------------- experience
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_END_WORDS = r"present|current|currently|now|till date|to date|ongoing|today"
_DATE_RANGE = re.compile(
    rf"(?:(?P<sm>{_MON})[\s,]*|(?P<sn>\d{{1,2}})[/.-])?(?P<sy>(?:19|20)\d{{2}})"
    rf"\s*(?:-|–|—|to|until)\s*"
    rf"(?:(?P<em>{_MON})[\s,]*|(?P<en>\d{{1,2}})[/.-])?(?:(?P<ey>(?:19|20)\d{{2}})|(?P<now>{_END_WORDS}))",
    re.I,
)
_EXPLICIT_YEARS = [
    re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:[\w/&-]+)){0,4}?\s+experience", re.I),
    re.compile(r"experience\s*(?:of|:)?\s*(?:over\s+)?(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)", re.I),
]


def _month_index(month_name, month_num, default):
    if month_name:
        return _MONTHS.get(month_name[:3].lower(), default)
    if month_num and 1 <= int(month_num) <= 12:
        return int(month_num)
    return default


def date_ranges(text: str, today: date | None = None) -> list[tuple[int, int]]:
    """Employment-style date ranges as (start_month_index, end_month_index)."""
    today = today or date.today()
    now_idx = today.year * 12 + today.month
    ranges = []
    for m in _DATE_RANGE.finditer(text):
        sy = int(m.group("sy"))
        start = sy * 12 + _month_index(m.group("sm"), m.group("sn"), 1)
        if m.group("now"):
            end = now_idx
        else:
            ey = int(m.group("ey"))
            end = ey * 12 + _month_index(m.group("em"), m.group("en"), 12)
        end = min(end, now_idx)
        if 1970 <= sy and start <= end and (end - start) <= 12 * 50:
            ranges.append((start, end))
    return ranges


def _union_months(ranges: list[tuple[int, int]]) -> int:
    total, cur_s, cur_e = 0, None, None
    for s, e in sorted(ranges):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total


def explicit_years(text: str) -> float | None:
    vals = []
    for rx in _EXPLICIT_YEARS:
        vals += [float(v) for v in rx.findall(text)]
    vals = [v for v in vals if 0 < v <= 45]
    return max(vals) if vals else None


def estimate_experience(sections: dict[str, str], text: str, today: date | None = None) -> float:
    """Years of professional experience: the larger of the stated figure and
    the union of dated ranges in the experience section."""
    if sections.get("experience"):
        scope = sections["experience"]
    else:  # no heading found: use everything except education/projects/certs
        scope = "\n".join(v for k, v in sections.items() if k not in {"education", "projects", "certifications", "other"})
    months = _union_months(date_ranges(scope, today))
    stated = explicit_years(text) or 0
    return round(max(months / 12, stated), 1)


# ---------------------------------------------------------------- education
_EDU_LEVELS = [
    (5, "Doctorate", [r"\bph\.?\s?d\b", r"\bdoctorate\b", r"\bdoctor of philosophy\b"], [r"\bD\.?Phil\b"]),
    (4, "Master's", [r"\bmaster'?s?\b", r"\bm\.?\s?tech\b", r"\bm\.?\s?sc\b", r"\bmca\b", r"\bmba\b", r"\bpost[- ]?graduate\b", r"\bm\.?\s?eng\b", r"\bpgdm\b"],
     [r"\bM\.?S\.?(?=\s+(?:in|of|\())", r"\bM\.?E\.?(?=\s+(?:in|of|\())", r"\bM\.?A\.?(?=\s+(?:in|of|\())", r"\bM\.?Com\b"]),
    (3, "Bachelor's", [r"\bbachelor'?s?\b", r"\bb\.?\s?tech\b", r"\bb\.?\s?sc\b", r"\bbca\b", r"\bbba\b", r"\bb\.?\s?com\b", r"\bundergraduate degree\b", r"\bb\.?\s?eng\b", r"\bbachelors\b"],
     [r"\bB\.?E\.?(?=\s+(?:in|of|\())", r"\bB\.?S\.?(?=\s+(?:in|of|\())", r"\bB\.?A\.?(?=\s+(?:in|of|\())"]),
    (2, "Diploma", [r"\bdiploma\b", r"\bpolytechnic\b", r"\bassociate degree\b"], []),
    (1, "High school", [r"\bhigh school\b", r"\bhsc\b", r"\bssc\b", r"\b12th\b", r"\b10th\b", r"\bsecondary school\b", r"\ba-levels?\b"], []),
]
_EDU_COMPILED = [
    (lvl, label, re.compile("|".join(ci), re.I), re.compile("|".join(cs)) if cs else None)
    for lvl, label, ci, cs in _EDU_LEVELS
]


def education_levels(text: str) -> set[int]:
    found = set()
    for lvl, _, ci, cs in _EDU_COMPILED:
        if ci.search(text) or (cs and cs.search(text)):
            found.add(lvl)
    return found


def extract_education(sections: dict[str, str], text: str) -> dict:
    """Highest degree found (searching the education section first)."""
    for scope in (sections.get("education", ""), text):
        levels = education_levels(scope)
        if levels:
            top = max(levels)
            label = next(l for lvl, l, _, _ in _EDU_COMPILED if lvl == top)
            _, _, ci, cs = next(x for x in _EDU_COMPILED if x[0] == top)
            detail = ""
            for line in scope.splitlines():
                if ci.search(line) or (cs and cs.search(line)):
                    detail = re.sub(r"\s+", " ", line).strip(" -|,")[:110]
                    break
            return {"level": top, "label": label, "detail": detail}
    return {"level": 0, "label": "Not detected", "detail": ""}


# --------------------------------------------------------------------- jobs
_JD_YEARS = [
    re.compile(r"(\d{1,2})\s*\+?\s*(?:-|to)?\s*(?:\d{1,2})?\s*\+?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+[\w/&-]+){0,4}?\s+(?:experience|exp)", re.I),
    re.compile(r"(?:minimum|at least|min\.?)\s*(?:of\s+)?(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"experience\s*(?:of|:)?\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I),
]


def parse_job_description(text: str, title: str = "") -> dict:
    years = []
    for rx in _JD_YEARS:
        years += [int(v) for v in rx.findall(text)]
    years = [y for y in years if 0 < y <= 30]
    levels = education_levels(text)
    return {
        "title": title.strip() or _guess_title(text),
        "skills": extract_skills(text),
        "min_years": min(years) if years else None,
        "education_level": min(levels) if levels else None,
    }


def _guess_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip(" -#*:\t")
        if 3 <= len(line) <= 70:
            m = re.search(r"(?:hiring|looking for|seeking|role:|position:|job title:)\s*(?:an?\s+)?(.+)", line, re.I)
            return (m.group(1) if m else line).strip(" .:")[:70]
    return "Job description"


# ------------------------------------------------------------ resume entry
def parse_resume(text: str, filename: str = "", today: date | None = None) -> dict:
    sections = split_sections(text)
    skills = extract_skills(text)
    name = extract_name(text, filename)
    # "Blind" text used for scoring: no name / contact details, so these
    # cannot influence ranking.
    blind = strip_contact_info(text)
    if name and name != "Unknown candidate":
        blind = re.sub(re.escape(name), " ", blind, flags=re.I)
    return {
        "filename": filename,
        "name": name,
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": skills,
        "experience_years": estimate_experience(sections, text, today),
        "education": extract_education(sections, text),
        "sections": [k for k, v in sections.items() if v and k != "header"],
        "word_count": len(text.split()),
        "text": text,
        "blind_text": blind,
    }
