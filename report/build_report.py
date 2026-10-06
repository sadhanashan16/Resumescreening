"""Build the PBL report PDF: Chromium renders the content, pypdf overlays the sample's header banner, watermark and page numbers."""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402
from docgen import CSS  # noqa: E402

OUT_PDF = HERE / "ResumeIQ_PBL_Report.pdf"
A4 = (595.32, 841.92)
# Exact placement taken from the sample PDF's content stream (points, origin bottom-left)
WATERMARK = dict(x=66.6, y=350.87, w=451.2, h=131.75)
BANNER = dict(x=72.0, y=747.07, w=451.3, h=59.45)


def assemble(pages: dict[str, str]) -> str:
    body = C.build_body()
    front = (C.cover() + C.vision_mission() + C.bonafide() + C.declaration() + C.acknowledgement() + C.abstract_page()
             + C.toc_rows(body, pages) + C.list_page("LIST OF FIGURES", body.figs, pages)
             + C.list_page("LIST OF TABLES", body.tabs, pages) + C.abbreviations() + C.team_roles())
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{C.TITLE}</title><style>{CSS}</style></head><body>{front}{body.html()}</body></html>"
    assemble.body = body
    return html


def render(html: str) -> bytes:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        pg = b.new_page()
        pg.set_content(html, wait_until="load")
        pg.wait_for_timeout(500)
        pdf = pg.pdf(prefer_css_page_size=True, print_background=True)
        b.close()
    return pdf


def page_texts(pdf: bytes) -> list[str]:
    return [(pg.extract_text() or "") for pg in PdfReader(io.BytesIO(pdf)).pages]


def locate(pdf: bytes, body) -> dict[str, str]:
    texts = page_texts(pdf)
    ch1 = next(i for i, t in enumerate(texts) if re.search(r"^CHAPTER 1\s*$", t, re.M) and "INTRODUCTION" in t)
    pages: dict[str, str] = {}
    cursor = ch1

    def find(pattern: str, start: int) -> int | None:
        for i in range(start, len(texts)):
            if re.search(pattern, texts[i], re.M):
                return i
        return None

    for level, text, key in body.toc:
        pat = r"^\s*" + re.escape(key) + r"\s*$" if level == 1 else r"^\s*" + re.escape(key) + r"\s*$"
        i = find(pat, cursor)
        if i is not None:
            pages[key] = str(i - ch1 + 1)
            cursor = i
    for lab, cap in body.figs + body.tabs:
        i = find(r"^\s*" + re.escape(lab) + r"\s+[—–-]", ch1) or find(r"^\s*" + re.escape(lab), ch1)
        if i is not None:
            pages[lab] = str(i - ch1 + 1)
    pages["_ch1"] = str(ch1)
    return pages


def overlay(content_pdf: bytes, ch1_index: int) -> bytes:
    wm = ImageReader(str(HERE / "assets" / "watermark.png"))
    bn = ImageReader(str(HERE / "assets" / "banner.jpg"))
    reader = PdfReader(io.BytesIO(content_pdf))
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i == 0:                         # cover page: no banner / watermark / number (as in the sample)
            writer.add_page(page)
            continue
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.drawImage(wm, WATERMARK["x"], WATERMARK["y"], WATERMARK["w"], WATERMARK["h"])   # drawn first = behind the text
        c.drawImage(bn, BANNER["x"], BANNER["y"], BANNER["w"], BANNER["h"])
        c.showPage(); c.save()
        under = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
        under.merge_page(page)             # content on top of watermark + banner
        if i >= ch1_index:                 # numbered pages start at Chapter 1 = page 1
            nb = io.BytesIO()
            c2 = canvas.Canvas(nb, pagesize=A4)
            c2.setFont("Times-Roman", 12)
            c2.drawCentredString(A4[0] / 2, 47, str(i - ch1_index + 1))
            c2.showPage(); c2.save()
            under.merge_page(PdfReader(io.BytesIO(nb.getvalue())).pages[0])
        writer.add_page(under)
    writer.add_metadata({"/Title": C.TITLE, "/Author": f"{C.S1}; {C.S2}", "/Subject": "Project-Based Learning (PBL) Report - Machine Learning"})
    try:
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    except Exception as exc:  # older pypdf
        print("dedupe skipped:", exc)
    out = io.BytesIO(); writer.write(out)
    return out.getvalue()


def sanity_checks():
    """Assert every data-dependent claim written in the prose."""
    cands = C.RANK["candidates"]
    assert all(c["naive_bayes_role"] == c["svm_role"] for c in cands), "NB and SVM disagree on a sample resume"
    s = {c["name"]: c["score"] for c in cands}
    assert s["David Sato"] == 72.0 and s["James Mensah"] == 70.7, s
    top = [c for c in cands if c["score"] >= 70]
    assert len(top) == 2 and all(c["predicted_role"]["title"] == "Data Scientist" for c in top)
    mid = [c for c in cands if 30 <= c["score"] < 50]
    assert {c["predicted_role"]["title"] for c in mid} == {"Data Analyst", "Machine Learning Engineer", "Data Engineer"}, mid
    assert all(c["score"] < 30 for c in cands if c not in top and c not in mid)
    assert C.N_CORRECT == 479 and C.h["ensemble"]["accuracy"] == 0.9979, (C.N_CORRECT, C.h["ensemble"])


def main():
    sanity_checks()
    pages: dict[str, str] = {}
    html = assemble(pages)
    pdf1 = render(html)
    pages = locate(pdf1, assemble.body)
    html = assemble(pages)
    pdf2 = render(html)
    pages2 = locate(pdf2, assemble.body)
    if pages2 != pages:   # TOC length is stable, so one extra pass settles any drift
        html = assemble(pages2); pdf2 = render(html); pages2 = locate(pdf2, assemble.body)
    final = overlay(pdf2, int(pages2["_ch1"]))
    OUT_PDF.write_bytes(final)
    (HERE / "report.html").write_text(html, encoding="utf-8")
    n = len(PdfReader(io.BytesIO(final)).pages)
    print(f"wrote {OUT_PDF.name}: {n} pages, {OUT_PDF.stat().st_size // 1024} KB; chapter 1 at pdf page {int(pages2['_ch1']) + 1}")


if __name__ == "__main__":
    main()
