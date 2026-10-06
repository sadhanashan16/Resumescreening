"""Tiny report-HTML generator: numbering, TOC/list bookkeeping and the CSS that mimics the sample report."""
from __future__ import annotations

import base64
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent


def data_uri(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower().replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(path.read_bytes()).decode()


CSS = """
@page { size: A4; margin: 36mm 25.4mm 21mm 25.4mm; }
* { box-sizing: border-box; }
html { font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 12pt; color: #000; }
body { margin: 0; line-height: 1.5; text-align: justify; hyphens: manual; }
p { margin: 0 0 8pt; orphans: 2; widows: 2; }
.pb { break-before: page; }
.center { text-align: center; }
.cover { text-align: center; line-height: 1.3; margin-top: -6mm; }
.cover .title { font-size: 15pt; font-weight: bold; margin-top: 2mm; }
.cover .b { font-weight: bold; } .cover .bi { font-weight: bold; font-style: italic; } .cover .i { font-style: italic; }
.front h1 { font-size: 14pt; text-align: center; margin: 4pt 0 12pt; letter-spacing: .2pt; }
.front h1.l { text-align: left; }
h1.chapter { font-size: 14pt; text-align: center; margin: 0; line-height: 1.55; }
h1.ctitle { font-size: 14pt; text-align: center; margin: 0 0 10pt; line-height: 1.55; }
h2 { font-size: 14pt; margin: 14pt 0 6pt; line-height: 1.4; break-after: avoid; }
h3 { font-size: 13pt; font-style: italic; margin: 12pt 0 5pt; line-height: 1.4; break-after: avoid; }
h4 { font-size: 12pt; margin: 8pt 0 3pt; break-after: avoid; }
ul { margin: 2pt 0 8pt; padding-left: 36pt; list-style: none; }
ul li { position: relative; margin: 0 0 6pt; }
ul li::before { content: "\\2022"; position: absolute; left: -26pt; }
ol.num { margin: 2pt 0 8pt; padding-left: 36pt; } ol.num li { margin-bottom: 6pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 2pt; font-size: 11.5pt; line-height: 1.22; text-align: left; break-inside: auto; }
th { background: #d9d9d9; font-weight: bold; text-align: center; border: 1px solid #000; padding: 4pt 6pt; }
td { border: 1px solid #000; padding: 3pt 6pt; vertical-align: middle; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
td.c { text-align: center; } td.r { text-align: right; }
.cap { text-align: center; font-weight: bold; font-style: italic; margin: 4pt 0 12pt; line-height: 1.35; }
figure { margin: 8pt 0 0; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
pre.code { font-family: 'DejaVu Sans Mono', 'Liberation Mono', monospace; font-size: 7.9pt; line-height: 1.32; background: #f4f4f4; border: 1px solid #8c8c8c; padding: 6pt 8pt; margin: 6pt 0 2pt; white-space: pre-wrap; word-break: break-word; text-align: left; break-inside: avoid; }
.eq { text-align: center; margin: 4pt 0 8pt; font-style: italic; line-height: 1.6; }
.eq sub, .eq sup { font-size: 70%; line-height: 0; }
.note { font-size: 11pt; }
.box { border: 3.5pt solid #ed7d31; border-radius: 22pt; padding: 10pt 16pt 8pt; margin: 14pt 0 22pt; text-align: justify; line-height: 1.95; }
.box .im { font-weight: bold; color: #8b0000; }
.box .dm { font-weight: bold; }
.box p { margin: 0; text-indent: 0; }
.hang { padding-left: 30pt; text-indent: -30pt; margin: 0; }
.refs p { font-size: 10.5pt; line-height: 1.28; margin: 0 0 4.5pt !important; text-align: left; }
.sig { display: flex; gap: 22pt; margin-top: 70pt; line-height: 1.3; text-align: left; } .sig > div { flex: 1; }
.toc .row { display: flex; align-items: baseline; text-align: left; line-height: 1.38; }
.toc .row .t { white-space: nowrap; } .toc .row .d { flex: 1; border-bottom: 1.4pt dotted #000; margin: 0 3pt; transform: translateY(-3pt); } .toc .row .n { min-width: 14pt; text-align: right; }
.toc .l1 { font-weight: bold; margin-top: 2pt; } .toc .l2 { padding-left: 14pt; }
.lof .row { display: flex; align-items: baseline; text-align: left; line-height: 1.55; } .lof .row .t { } .lof .row .d { flex: 1; border-bottom: 1.4pt dotted #000; margin: 0 3pt; transform: translateY(-3pt);} .lof .row .n { min-width: 14pt; text-align: right; }
"""


class Doc:
    def __init__(self):
        self.parts: list[str] = []
        self.toc: list[tuple[int, str, str]] = []   # (level, display text, search key)
        self.figs: list[tuple[str, str]] = []        # (label, caption)
        self.tabs: list[tuple[str, str]] = []
        self.chapter_no = 0
        self.counters: dict[tuple[str, int], int] = {}

    # ---- raw
    def raw(self, s: str): self.parts.append(s)

    def esc(self, s: str) -> str: return html.escape(s, quote=False)

    # ---- structure
    def chapter(self, title: str):
        self.chapter_no += 1
        n = self.chapter_no
        self.raw(f'<div class="pb"></div><h1 class="chapter">CHAPTER {n}</h1><h1 class="ctitle">{title}</h1>')
        self.toc.append((1, f"CHAPTER {n}: {title}", f"CHAPTER {n}"))

    def special(self, title: str, toc=True, cls=""):
        self.raw(f'<div class="pb"></div><h1 class="chapter {cls}" style="margin-bottom:10pt">{title}</h1>')
        if toc:
            self.toc.append((1, title, title))

    def sec(self, label: str, title: str):
        self.raw(f"<h2>{label} {title}</h2>")
        self.toc.append((2, f"{label} {title}", f"{label} {title}"))

    def sub(self, label: str, title: str): self.raw(f"<h3>{label} {title}</h3>")

    def h4(self, t: str): self.raw(f"<h4>{t}</h4>")

    # ---- text
    def p(self, s: str, cls=""): self.raw(f'<p class="{cls}">{s}</p>')

    def ul(self, items: list[str]): self.raw("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")

    def ol(self, items: list[str]): self.raw('<ol class="num">' + "".join(f"<li>{i}</li>" for i in items) + "</ol>")

    def eq(self, s: str): self.raw(f'<div class="eq">{s}</div>')

    # ---- captions
    def _label(self, kind: str) -> str:
        key = (kind, self.chapter_no)
        self.counters[key] = self.counters.get(key, 0) + 1
        return f"{kind} {self.chapter_no}.{self.counters[key]}"

    def figure(self, img: Path, caption: str, width_pct=100):
        label = self._label("Figure")
        self.figs.append((label, caption))
        self.raw(f'<figure><img src="{data_uri(img)}" style="width:{width_pct}%"><div class="cap">{label} — {caption}</div></figure>')

    def table(self, headers: list[str], rows: list[list[str]], caption: str | None, widths: list[int] | None = None,
              center_cols: tuple[int, ...] = ()):
        cg = "".join(f'<col style="width:{w}%">' for w in widths) if widths else ""
        head = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>"
        body = "".join("<tr>" + "".join(
            f'<td class="{"c" if i in center_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
        self.raw(f"<table><colgroup>{cg}</colgroup>{head}<tbody>{body}</tbody></table>")
        if caption:
            label = self._label("Table")
            self.tabs.append((label, caption))
            self.raw(f'<div class="cap">{label} — {caption}</div>')

    def code(self, text: str, caption: str | None = None, kind="Code"):
        self.raw(f'<pre class="code">{html.escape(text)}</pre>')
        if caption:
            label = self._label(kind)
            if kind == "Figure":
                self.figs.append((label, caption))
            self.raw(f'<div class="cap">{label} — {caption}</div>')

    def html(self) -> str:
        return "".join(self.parts)
