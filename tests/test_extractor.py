import io
from pathlib import Path

import pytest
from docx import Document

from resume_screening.extractor import ExtractionError, extract_text

ROOT = Path(__file__).resolve().parent.parent
LONG = "Jane Doe\nPython developer with SQL and Flask experience building REST APIs for four years."


def make_docx(text=LONG):
    d = Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_txt_and_docx():
    assert "Python developer" in extract_text("a.txt", LONG.encode())
    assert "Python developer" in extract_text("a.docx", make_docx())


def test_pdf_samples():
    for p in (ROOT / "samples").glob("*.pdf"):
        assert len(extract_text(p.name, p.read_bytes())) > 300


def test_legacy_doc():
    text = extract_text("legacy.doc", (ROOT / "tests/fixtures/legacy.doc").read_bytes())
    assert "Lina Reddy" in text and "Postman" in text


@pytest.mark.parametrize("name,data", [
    ("x.pdf", b"not a pdf"), ("x.docx", b"not a zip"), ("x.doc", b"garbage"), ("x.txt", b""),
    ("x.txt", b"tiny"), ("x.exe", b"MZ" * 50),
])
def test_bad_files_raise_friendly_errors(name, data):
    with pytest.raises(ExtractionError):
        extract_text(name, data)
