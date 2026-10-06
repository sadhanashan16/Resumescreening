"""Text cleaning/normalisation shared by training and inference."""
from __future__ import annotations

import re

from .skills import find_skill_spans, slugify

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|\b(?:linkedin|github)\.com/\S+", re.I)
PHONE_RE = re.compile(r"(?<![\w/])\+?\d[\d\s().-]{8,}\d(?![\w/])")


def clean_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", " ")
    text = text.replace("•", "-").replace("●", "-").replace("", "-")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_contact_info(text: str) -> str:
    """Remove e-mails, URLs and phone numbers (not useful for matching)."""
    text = EMAIL_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)

    def _phone(m):
        digits = re.sub(r"\D", "", m.group(0))
        # leave year ranges such as "2019 - 2022" alone
        if len(digits) in (8,) and re.fullmatch(r"(19|20)\d{2}\D+(19|20)\d{2}", m.group(0)):
            return m.group(0)
        return " " if 10 <= len(digits) <= 14 else m.group(0)

    return PHONE_RE.sub(_phone, text)


def canonicalise_skills(text: str) -> str:
    """Replace every recognised skill mention with a single vocabulary token."""
    spans = find_skill_spans(text)
    if not spans:
        return text
    out, pos = [], 0
    for start, end, name in spans:
        out.append(text[pos:start])
        out.append(f" {slugify(name)} ")
        pos = end
    out.append(text[pos:])
    return "".join(out)


_TOKEN_CLEAN = re.compile(r"[^a-z0-9_ ]+")


def normalize_for_model(text: str) -> str:
    """Text fed to the TF-IDF vectoriser.

    Contact details are removed, skills are collapsed to canonical tokens
    (``scikit-learn`` / ``sklearn`` -> ``skill_scikit_learn``) so that spelling
    variants share one feature, and everything is lower-cased.
    """
    text = strip_contact_info(text)
    text = canonicalise_skills(text)
    text = text.lower()
    text = _TOKEN_CLEAN.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()
