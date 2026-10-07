"""Search line spacing and figure sizes so numbered pages have minimal blank space and end on page TARGET.

    python report/tune.py        # writes report/tuning.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = 29
FIGS = ["ui_home", "ui_screen_form", "ui_screen_results", "ui_match_results", "ui_insights", "fig_architecture", "fig_pipeline", "fig_metrics", "fig_confusion", "fig_ranking", "fig_outcomes"]

TRIAL = r'''
import sys, json
sys.path.insert(0, "%s")
import build_report as B
html = B.assemble({})
pdf = B.render(html)
texts = B.page_texts(pdf)
import re
ch1 = next(i for i, t in enumerate(texts) if re.search(r"^CHAPTER 1\s*$", t, re.M) and "INTRODUCTION" in t)
gaps = B.gap_report(pdf, ch1)
print("RESULT" + json.dumps([[int(a), float(b)] for a, b in gaps]))
''' % HERE


def trial(tuning: dict):
    env = dict(os.environ, REPORT_TUNING=json.dumps(tuning))
    out = subprocess.run([sys.executable, "-c", TRIAL], capture_output=True, text=True, env=env).stdout
    line = [l for l in out.splitlines() if l.startswith("RESULT")]
    gaps = json.loads(line[0][6:])
    last = gaps[-1][0]
    body = [g for _, g in gaps[:-1]]
    score = sum(max(0, g - 3) ** 2 for g in body) + 400 * abs(last - TARGET) + 3 * max(body)
    return score, last, max(body), body


def main():
    best = json.loads((HERE / "tuning.json").read_text()) if (HERE / "tuning.json").exists() else {"line_height": 1.65, "scales": {}}
    bs, last, mx, _ = trial(best)
    print("start", round(bs), last, mx, flush=True)
    for lh in (1.6, 1.65, 1.7):
        t = dict(best, line_height=lh)
        s, l, m, _ = trial(t)
        print("lh", lh, round(s), l, m, flush=True)
        if s < bs:
            best, bs = t, s
    for sweep in range(1):
        for f in FIGS:
            for k in (0.6, 0.75, 0.9, 1.0, 1.1):
                t = json.loads(json.dumps(best)); t["scales"][f] = k
                s, l, m, _ = trial(t)
                if s < bs - 1e-6:
                    best, bs = t, s
                    print("  improve", f, k, round(s), l, m, flush=True)
        (HERE / "tuning.json").write_text(json.dumps(best, indent=1))
    s, l, m, body = trial(best)
    print("FINAL", best, round(s), l, m, body, flush=True)
    (HERE / "tuning.json").write_text(json.dumps(best, indent=1))


if __name__ == "__main__":
    main()
