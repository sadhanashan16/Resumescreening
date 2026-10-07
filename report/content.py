"""All report text. Facts come from the repository, models/metrics.json and measurements made on the real system."""
from __future__ import annotations

import inspect
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "report"))

from docgen import Doc, data_uri  # noqa: E402
from resume_screening import config, engine as eng_mod, text_utils, train as train_mod  # noqa: E402
from resume_screening.catalog import ROLES  # noqa: E402
from resume_screening.skills import SKILLS  # noqa: E402
from webapp import auth as auth_mod  # noqa: E402

FIG = ROOT / "report" / "figures"
ASSETS = ROOT / "report" / "assets"
M = json.loads(config.METRICS_PATH.read_text())
LAT = json.loads((ROOT / "poster" / "assets" / "latency.json").read_text())
MEAS = json.loads((ROOT / "report" / "measurements.json").read_text())
RANK = json.loads((ROOT / "report" / "ranking_demo.json").read_text())

TITLE = "ResumeIQ – AI-Based Resume Screening and Job Matching System"
S1, R1 = "Sadhana Shanmugam", "2104251040837"
S2, R2 = "Dhanya Sri Mohandass", "2104251040189"
h, cv = M["holdout"], M["cross_validation"]
LATENCY = f"{MEAS['screen14_median_s'] + 1e-9:.2f}"          # 14 resumes incl. extraction and saving to the database
NTESTS = MEAS['tests_total']
TF = MEAS['tests_by_file']
RSS = f"{MEAS['process_rss_mb']:.0f}"
N_CORRECT = sum(M["confusion_matrix"]["matrix"][i][i] for i in range(M["n_roles"]))
NSK = len(SKILLS)


def src(obj) -> str:
    return textwrap.dedent(inspect.getsource(obj)).rstrip()


# =============================================================== front matter
def cover() -> str:
    return f"""
<div class="cover">
 <div class="title" style="margin-top:6mm">{TITLE}</div>
 <p class="b" style="margin-top:15mm">A PROJECT BASED LEARNING (PBL) REPORT</p>
 <p class="bi" style="margin-top:10mm">Submitted by</p>
 <p class="b" style="font-size:14pt;margin-top:4mm">{S1.upper()} - {R1}</p>
 <p class="b" style="font-size:14pt;margin-top:4mm">{S2.upper()} - {R2}</p>
 <p class="bi" style="margin-top:7mm">Submitted in partial fulfilment of the requirements</p>
 <p class="bi">for the</p>
 <p class="bi" style="margin-top:2mm">Project-Based Learning component of Machine Learning</p>
 <p class="b" style="font-size:14pt;margin-top:5mm">BACHELOR OF ENGINEERING</p>
 <p class="bi" style="font-size:10pt;margin-top:4mm">in</p>
 <p class="b" style="margin-top:3mm">COMPUTER SCIENCE AND ENGINEERING</p>
 <img src="{data_uri(ASSETS / 'cover_logo.png')}" style="width:150pt;margin-top:2mm">
 <p class="b" style="margin-top:3mm">CHENNAI INSTITUTE OF TECHNOLOGY, CHENNAI</p>
 <img src="{data_uri(ASSETS / 'anna_emblem.png')}" style="width:88pt;margin-top:-3mm">
 <p class="b" style="margin-top:0">Affiliated to Anna University, Chennai</p>
 <p class="b">(Autonomous)</p>
 <p style="margin-top:2mm">OCTOBER 2026</p>
</div>"""


def vision_mission() -> str:
    return """
<div class="pb"></div><div class="front">
<h1 class="l" style="margin-top:6pt">Vision of the Institute:</h1>
<div class="box"><p>To be an eminent centre for Academia, Industry and Research by imparting knowledge, relevant practices and inculcating human values to address global challenges through novelty and sustainability.</p></div>
<h1 class="l" style="margin-top:26pt">Mission of the Institute:</h1>
<div class="box" style="margin-top:20pt;line-height:1.9">
<p class="hang"><span class="im">IM1</span>. To creates next generation leaders by effective teaching learning methodologies and in still Scientifics Park in them to meet the global challenges.</p>
<p class="hang"><span class="im">IM2.</span> To transform lives through deployment of emerging technology, novelty and sustainability.</p>
<p class="hang"><span class="im">IM3</span>. To inculcate human values and ethical principles to cater the societal needs.</p>
<p class="hang"><span class="im">IM4</span>. To contributes towards the research ecosystem by providing a suitable,</p>
</div></div>
<div class="pb"></div><div class="front">
<h1 style="margin-top:0;margin-bottom:0;line-height:1.7">DEPARTMENT OF<br>COMPUTER SCIENCE AND ENGINEERING</h1>
<h1 class="l" style="margin-top:14pt">Vision of the Department:</h1>
<div class="box"><p>To Excel in the emerging areas of Computer Science and Engineering by imparting knowledge, relevant practices and inculcating human values to transform the students as potential resources to contribute innovatively through advanced computing in real time situations.</p></div>
<h1 class="l" style="margin-top:34pt">Mission of the Department:</h1>
<div class="box" style="margin-top:20pt;line-height:1.75">
<p class="hang"><span class="dm">DM1.</span> To provide strong fundamentals and technical skills for Computer Science applications through effective teaching learning methodologies.</p>
<p class="hang"><span class="dm">DM2.</span> To transform lives of the students by nurturing ethical values, creativity and novelty to become Entrepreneurs and establish start-ups.</p>
<p class="hang"><span class="dm">DM3.</span> To habituate the students to focus on sustainable solutions to improve the quality of life and the welfare of the society.</p>
</div></div>"""


def bonafide() -> str:
    return f"""
<div class="pb"></div><div class="front">
<h1 style="margin-top:8pt">BONAFIDE CERTIFICATE</h1>
<p style="line-height:1.9">This is to certify that the Project–Based Learning report titled <b>“{TITLE}”</b> is a Bonafide record of work carried out by <b>{S1} [{R1}] , {S2} [{R2}]</b> of the Department of Computer Science and Engineering, Chennai Institute of Technology, as part of the continuous, mentor–guided Project-Based Learning (PBL) component of the Machine Learning course during the academic year [2026–2027] under my supervision.</p>
<div class="sig" style="margin-top:92pt">
 <div><b>SIGNATURE</b><br>Dr. S. PAVITHRA, M.E., Ph.D.,<br><b>Professor and Head,</b><br>Dept. of Computer Science and Engineering<br>Chennai Institute of Technology,<br>Chennai – 69.</div>
 <div><b>SIGNATURE</b><br>Mrs. POORNIMA LAKSHMI,<br><b>MENTOR</b><br><b>Assistant Professor</b><br>Dept. of Computer Science and Engineering<br>Chennai Institute of Technology,<br>Chennai – 69.</div>
</div>
<p style="margin-top:96pt;text-align:left">Submitted for the final review held on …………………….</p>
<div style="display:flex;justify-content:space-between;margin-top:60pt;font-weight:bold"><span>Internal Examiner</span><span style="margin-right:6pt">External Examiner</span></div>
</div>"""


def declaration() -> str:
    return f"""
<div class="pb"></div><div class="front">
<h1 style="margin-top:8pt;font-size:12pt">DECLARATION</h1>
<p style="line-height:1.95">I/We jointly declare that the PBL report on <b>“{TITLE}”</b> is the result of original work done by us and best of our knowledge, similar work has not been submitted to <b>“ANNA UNIVERSITY, CHENNAI”</b> for the requirement of Degree of <b>BACHELOR OF ENGINEERING.</b> This PBL report is submitted on the partial fulfilment of the requirement of the award of Degree of <b>COMPUTER SCIENCE AND ENGINEERING.</b></p>
<p style="text-align:right;font-weight:bold;font-size:14pt;margin-top:96pt">Signature</p>
<p style="text-align:right;margin-top:34pt">{S1}</p>
<p style="text-align:right;margin-top:30pt">{S2}</p>
<p style="text-align:left;font-size:14pt;margin-top:16pt;margin-bottom:2pt">Place: Chennai</p>
<p style="text-align:left;font-size:14pt">Date:</p>
</div>"""


def acknowledgement() -> str:
    return f"""
<div class="pb"></div><div class="front">
<h1 style="margin-top:8pt;font-size:13pt">ACKNOWLEDGEMENT</h1>
<p>We wish to express our sincere gratitude to our honourable Chairman <b>SHRI. P. SRIRAM</b> for providing immense facilities at our institution.</p>
<p>We are very proud to render our thanks to our Principal <b>Dr. A. RAMESH M.E., Ph.D.,</b> for the facilities and the encouragement given by him toward the progress and completion of our project.</p>
<p>We would like to express special thanks and gratitude to our Dean <b>Dr. V. SRINIVASA RAO M.E., Ph.D.,</b> who has been a key source of motivation to us throughout the completion of our course and project work.</p>
<p>We proudly render our immense gratitude to the Head of the Department <b>Dr. S. PAVITHRA M.E., Ph.D.,</b> for her effective leadership, encouragement and guidance throughout the project.</p>
<p>We would like to extend our thanks to the Project Co-ordinator <b>Mrs. POORNIMA LAKSHMI,</b> Assistant Professor, Department of Computer Science and Engineering, for their valuable suggestions throughout this project.</p>
<p>We wish to acknowledge the help received from our class advisors <b>Dr. G. IRIN LORETTA M.E.,</b> Assistant Professor, and <b>S.E. NEELA KANDAN M.TECH.,</b> Assistant Professor, of the Department of Computer Science and Engineering for their valuable suggestions and support toward the successful completion of the project.</p>
<p style="text-align:right;margin-top:62pt;margin-bottom:2pt;margin-right:10pt;font-size:12.5pt">{S1} ({R1})</p>
<p style="text-align:right;margin-right:10pt;font-size:12.5pt">{S2} ({R2})</p>
</div>"""


ABSTRACT = (
    "Recruiters routinely receive hundreds of resumes for a single vacancy, and screening them by hand is slow, inconsistent "
    "and prone to human error and bias, so qualified candidates can be overlooked. ResumeIQ is an AI-based resume analysis and "
    "job-matching system that automates this first screening stage and lets a recruiter manage the outcome. Resumes in PDF, "
    f"DOC, DOCX and TXT formats are converted to text, and a rule-based natural-language-processing layer extracts skills (from a "
    f"{NSK}-skill taxonomy), education level, years of experience and contact details. Names, e-mail addresses and phone numbers "
    "are removed before scoring so that they cannot influence a ranking. The cleaned text is converted into TF-IDF vectors "
    f"(unigrams and bigrams, {M['n_features']:,} features), classified into one of {M['n_roles']} job roles by a Multinomial "
    "Naive Bayes model and a calibrated linear Support Vector Machine whose probabilities are averaged, and compared with a job "
    "description by cosine similarity. A transparent five-part match score (text similarity 40%, skill coverage 30%, role fit "
    "15%, experience 10% and education 5%) ranks the candidates and recommends a top-N shortlist with matched, related and "
    "missing skills for every candidate. The system is delivered as a multi-user Flask web application: recruiters register and "
    "log in, every screening is saved in a relational database (SQLite for development, PostgreSQL in production, with Alembic "
    "migrations), and candidates can be shortlisted, rejected, annotated, searched and exported to CSV. Passwords are hashed "
    "with scrypt, forms are CSRF-protected, login attempts are rate-limited, and all secrets are read from environment "
    "variables. The application is packaged with Docker and a Render blueprint and is covered by "
    f"{NTESTS} automated tests that run on both databases. The models were trained on {M['n_samples']:,} synthetic resumes "
    f"({M['n_roles']} roles × 200) because real resumes are personal data. On a held-out test set of {M['n_test']} resumes the "
    f"ensemble reached {h['ensemble']['accuracy'] * 100:.1f}% accuracy ({N_CORRECT}/{M['n_test']}), with 5-fold cross-validation "
    f"accuracy of {cv['naive_bayes']['accuracy'] * 100:.1f}% (Naive Bayes) and {cv['svm']['accuracy'] * 100:.1f}% (SVM); all five "
    "hand-written resumes that the data generator never produced were matched to the correct role, and 14 sample resumes in four "
    f"file formats were screened and saved in a median of {LATENCY} s. Because the training data are synthetic, these figures "
    "show that the pipeline works and are not an estimate of real-world accuracy; the report states this limitation openly and "
    "documents a code-ready path to retrain on real labelled resumes."
)


def abstract_page() -> str:
    return f"""
<div class="pb"></div><div class="front">
<h1 style="margin-top:2pt;font-size:13pt">ABSTRACT</h1>
<p style="line-height:1.62">{ABSTRACT}</p>
<p style="margin-top:8pt;text-align:left"><b>Keywords:</b> Resume Screening, Job Matching, Natural Language Processing, TF-IDF, Naive Bayes, Support Vector Machine.</p>
</div>"""


def toc_rows(doc: Doc, pages: dict[str, str]) -> str:
    rows = []
    for level, text, key in doc.toc:
        cls = "l1" if level == 1 else "l2"
        rows.append(f'<div class="row {cls}"><span class="t">{doc.esc(text)}</span><span class="d"></span><span class="n">{pages.get(key, "00")}</span></div>')
    return f'<div class="pb"></div><div class="front toc"><h1 style="margin-top:2pt;font-size:13pt">TABLE OF CONTENTS</h1>{"".join(rows)}</div>'


def list_page(title: str, entries, pages: dict[str, str]) -> str:
    rows = "".join(
        f'<div class="row"><span class="t">{lab}&nbsp; {cap}</span><span class="d"></span><span class="n">{pages.get(lab, "00")}</span></div>'
        for lab, cap in entries)
    return f'<div class="pb"></div><div class="front lof"><h1 style="margin-top:2pt;font-size:13pt">{title}</h1><div style="margin-top:12pt">{rows}</div></div>'


ABBR = [("ML", "Machine Learning"), ("NLP", "Natural Language Processing"), ("TF-IDF", "Term Frequency – Inverse Document Frequency"),
        ("NB", "Naive Bayes"), ("SVM", "Support Vector Machine"), ("CV", "Cross-Validation"), ("PBL", "Project-Based Learning"),
        ("PII", "Personally Identifiable Information"), ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"), ("JSON", "JavaScript Object Notation"), ("CSV", "Comma-Separated Values"),
        ("PDF", "Portable Document Format"), ("DOCX", "Office Open XML Word Document"), ("OCR", "Optical Character Recognition"),
        ("NER", "Named Entity Recognition"), ("CSP", "Content Security Policy"), ("CI", "Continuous Integration"),
        ("UI", "User Interface"), ("WSGI", "Web Server Gateway Interface"), ("ORM", "Object-Relational Mapping"),
        ("CSRF", "Cross-Site Request Forgery"), ("HSTS", "HTTP Strict Transport Security"), ("SQL", "Structured Query Language")]


def abbreviations() -> str:
    rows = "".join(f"<tr><td class='c'>{a}</td><td>{b}</td></tr>" for a, b in ABBR)
    return (f'<div class="pb"></div><div class="front"><h1 style="margin-top:2pt;font-size:13pt">LIST OF ABBREVIATIONS</h1>'
            f'<table style="margin-top:14pt"><colgroup><col style="width:22%"><col style="width:78%"></colgroup>'
            f'<thead><tr><th>Abbreviation</th><th>Full Form</th></tr></thead><tbody>{rows}</tbody></table></div>')


def team_roles() -> str:
    return f"""
<div class="pb"></div><div class="front">
<h1 style="margin-top:6pt;font-size:13pt">TEAM ROLES AND RESPONSIBILITIES</h1>
<p>Both members jointly owned problem framing, the weekly mentor-review cycle, the literature exploration in Chapter 2, and the final report, and contributed <b>equally (50% : 50%)</b> to the project. Division of the build work below reflects primary ownership; both members reviewed and tested the full system before each milestone.</p>
<table style="margin-top:26pt"><colgroup><col style="width:22%"><col style="width:24%"><col style="width:54%"></colgroup>
<thead><tr><th>Team Member</th><th>Primary Role</th><th>Key Responsibilities</th></tr></thead><tbody>
<tr><td>{S1}<br>({R1})</td><td>ML Pipeline &amp; Data Backend Lead</td><td>Designed and implemented the resume text extraction (extractor.py), the rule-based NLP parser and skill taxonomy (parser.py, skills.py), the TF-IDF / Naive Bayes / SVM training and evaluation pipeline (train.py, dataset.py), the scoring and role-recommendation engine (engine.py), and, for the web platform, the SQLAlchemy data model, Alembic migrations, the screening and shortlist JSON API and the environment-driven configuration.</td></tr>
<tr><td>{S2}<br>({R2})</td><td>Interface, Security, Testing &amp; Deployment Lead</td><td>Designed and implemented the web interface (dashboard, screening, shortlist, account and model-insight pages in HTML, CSS and JavaScript), the account system (registration, login, lockout, CSRF protection, rate limits and security headers), the sample resumes and screenshots, the {NTESTS}-test automated suite, and the Docker image, Render blueprint and CI workflow.</td></tr>
</tbody></table></div>"""


# ==================================================================== chapters
def build_body() -> Doc:
    d = Doc()
    p, ul, sec, sub = d.p, d.ul, d.sec, d.sub

    # ------------------------------------------------------------ Chapter 1
    d.chapter("INTRODUCTION")
    sec("1.1", "Background")
    p("Hiring begins with a screening problem. A single vacancy can attract hundreds or thousands of applications, and "
      "recruiters must decide, often in minutes per resume, which deserve an interview. Done by hand, this first pass is slow, "
      "tiring and inconsistent: two reviewers may rank the same resume differently, and a qualified candidate can be "
      "overlooked simply because the resume words a skill differently from the advertisement. Keyword filters reduce the "
      "workload but share the weakness, because “machine learning” and “ML”, or “scikit-learn” and “sklearn”, are different "
      "strings to a filter but the same skill to a person.")
    p("Resumes also arrive as unstructured documents (PDF, Word, plain text) with no common layout, so the text must first be "
      "extracted and facts such as skills, education and years of experience recovered from free text. A text-classification "
      "model can then learn which vocabulary characterises each job family, and similarity over weighted term vectors can "
      "quantify how closely a resume matches a job description.")
    p("Automation is not automatically fair. A review of algorithmic-hiring practice found that vendors say little about how "
      "bias is validated [1], and in 2018 a company withdrew an experimental recruiting tool found to disadvantage women [2]. "
      "A screening system should therefore be explainable, keep personal identifiers out of its scoring, and be positioned as "
      "a decision aid rather than a decision maker.")
    p("ResumeIQ was undertaken as the Project-Based Learning (PBL) component of the Machine Learning course (CS5305), "
      "following the build–learn cycle that PBL is meant to teach: a baseline text classifier, a refinement driven by what the "
      "first results revealed, and a final system the team can explain component by component.")
    sec("1.2", "Driving Question")
    p("Can a classical machine-learning pipeline built from TF-IDF features, Naive Bayes and Support Vector Machine classifiers, and "
      "cosine similarity turn unstructured resumes into a ranked, explainable shortlist for a given job description, and "
      "recommend suitable job roles for a single resume, without using the candidate's name or contact details and while "
      "running on ordinary laptop hardware? And if two structurally different classifiers are used, does combining them give a "
      "more reliable role signal than either one alone?")
    p("This narrows into a buildable task: extract skills, education and experience with NLP; represent resume and job text as "
      "TF-IDF vectors; classify each resume into one of twelve roles with Naive Bayes and an SVM; and combine text similarity, "
      "skill coverage, role agreement, experience and education into one score a recruiter can inspect.")
    sec("1.3", "Objectives")
    ul(["To accept resumes in PDF and DOC formats (and DOCX and plain text) and convert them reliably into text.",
        "To extract skills, education and experience using NLP, removing names and contact details before scoring.",
        "To match resumes with job descriptions and measure suitability using TF-IDF vectors and cosine similarity.",
        "To apply TF-IDF, Naive Bayes and SVM for ranking and classification, evaluated with a held-out set and cross-validation.",
        "To generate a top-candidate shortlist automatically, explaining each candidate with matched, related and missing "
        "skills, and to recommend suitable roles for a single resume.",
        "To deliver a working multi-user website built with Python, Scikit-learn and Pandas, with accounts, saved screenings and "
        "shortlist management on a relational database, packaged for deployment on Render, and to document the weekly PBL "
        "progress and what each member learned."])
    sec("1.4", "Scope and Limitations")
    p(f"ResumeIQ models {M['n_roles']} technology and business job roles (for example Data Scientist, DevOps Engineer, QA Engineer "
      f"and Business Analyst) and works on English, text-based resumes. Skills come from a taxonomy of {NSK} skills with "
      "aliases (for example “sklearn” for Scikit-learn), so skills outside it are not detected. Scanned, image-only documents "
      "have no text layer and are rejected with a clear message; OCR is outside the scope of this build.")
    p(f"The classifiers were trained on {M['n_samples']:,} synthetic resumes, because real resumes are personal data and no real "
      "labelled corpus was available. The reported accuracy therefore measures how well the pipeline separates the synthetic "
      "roles and is not a real-world estimate (Chapter 6). Resume files are processed in memory and never stored; only the "
      "extracted details and scores are saved to the recruiter's own account, and every shortlist should be reviewed by a person.")

    # ------------------------------------------------------------ Chapter 2
    d.chapter("CONCEPT EXPLORATION")
    sec("2.1", "Related Approaches")
    sub("2.1.1", "Text representation and similarity")
    p("Spärck Jones proposed in 1972 that terms occurring in fewer documents are better discriminators and should be weighted "
      "by their inverse document frequency [3]. Salton and Buckley compared many term-weighting schemes and found that those "
      "combining term frequency, inverse document frequency and length normalisation performed well [4]. In the resulting "
      "TF-IDF representation each document is a sparse vector, and after length normalisation the cosine of the angle between "
      "two vectors measures how much weighted vocabulary the documents share [5]. This is what is needed to compare a resume "
      "with a job description, and it needs no labelled data, so it forms the similarity component of ResumeIQ's score.")
    sub("2.1.2", "Probabilistic text classification")
    p("McCallum and Nigam compared two Naive Bayes event models and found that the multinomial model, which uses word counts, "
      "generally performed better than the Bernoulli model when the vocabulary was large [6]. Naive Bayes trains in a single "
      "pass, works with little data and gives class probabilities directly, so it was chosen as the first classifier; its main "
      "weakness is the independence assumption, which makes its probabilities over-confident.")
    sub("2.1.3", "Support Vector Machines for text")
    p("Cortes and Vapnik introduced the soft-margin support-vector network [7]. Joachims argued that text suits SVMs because "
      "documents are high-dimensional, sparse and mostly linearly separable, and reported that SVMs outperformed k-nearest-"
      "neighbour, Naive Bayes, Rocchio and decision-tree classifiers in his experiments [8]. Linear SVMs for sparse data are "
      "implemented efficiently in LIBLINEAR [9], which underlies scikit-learn's LinearSVC. Because an SVM outputs a distance "
      "from the boundary rather than a probability, Platt's sigmoid fitting [10] is used to calibrate it so that its output "
      "can be averaged with Naive Bayes.")
    sub("2.1.4", "Algorithmic hiring and fairness")
    p("The hiring literature adds a constraint that the classification literature does not. Raghavan et al. found limited "
      "public information on how vendors validate bias-mitigation claims [1], and the 2018 withdrawal of a recruiting tool that "
      "penalised women's resumes [2] shows how a model trained on historical data can reproduce historical bias. ResumeIQ "
      "responds modestly: identifiers (name, e-mail, phone, links) are removed before scoring, every score is decomposed into "
      "visible components, and the output is presented as a decision aid.")
    sec("2.2", "Summary Table")
    d.table(["Ref.", "Approach / Model", "Setting", "Reported Result"],
            [["[3]", "Inverse document frequency term weighting", "Document-retrieval experiments", "Terms occurring in fewer documents are better discriminators; IDF weighting improved retrieval"],
             ["[4]", "Comparison of term-weighting schemes", "Several standard test collections", "Schemes combining term frequency, IDF and length normalisation performed well"],
             ["[6]", "Naive Bayes event models (multinomial vs. Bernoulli)", "Text-classification corpora", "Multinomial model generally better with large vocabularies"],
             ["[7]", "Support-vector network (soft-margin SVM)", "Pattern-recognition benchmarks", "Introduced the soft-margin SVM with strong benchmark results"],
             ["[8]", "SVM for text categorisation", "Reuters and Ohsumed collections", "SVMs outperformed k-NN, Naive Bayes, Rocchio and C4.5 in the reported experiments"],
             ["[10]", "Sigmoid calibration of SVM outputs", "Support-vector classifiers", "Posterior probabilities obtained from SVM scores via a fitted sigmoid"],
             ["[1]", "Review of algorithmic-hiring bias claims", "Vendor practices (qualitative)", "Limited public information on how bias mitigation is validated"]],
            "Summary of Related Approaches", widths=[9, 29, 26, 36], center_cols=(0,))
    sec("2.3", "What This Told Us")
    p("The literature pointed the team to the same starting point: TF-IDF features with Naive Bayes and a linear SVM, the "
      "best-understood classifiers for sparse text (Iteration 1, Chapter 4). Because the two rest on different assumptions "
      "(generative and independence-based versus margin-based), the team kept both and averaged their calibrated probabilities "
      "in Iteration 2. The skill taxonomy, the five-part score, the role-affinity measure and name-blind scoring were the "
      "team's own additions, motivated by the explainability and fairness concerns in [1] and [2].")

    # ------------------------------------------------------------ Chapter 3
    d.chapter("PROJECT PLANNING AND TEAM ORGANISATION")
    sec("3.1", "Weekly PBL Progress Log")
    p("The project ran across the full PBL cycle, from problem framing at the Zeroth Review (21 June 2026) through the final "
      "web-application build and testing. The table below summarises milestones and the work completed; the Mentor Remarks "
      "column is reserved for the mentor's own comments and sign-off.")
    d.table(["Week", "Milestone / Task", "Work Done", "Mentor Remarks"],
            [["1–2", "Problem framing (Zeroth Review)", "Selected the problem; fixed the input formats, the twelve job roles and the objectives; presented scope and aim.", "<br>"],
             ["3–4", "Concept exploration", "Surveyed TF-IDF, Naive Bayes, SVM and algorithmic-hiring literature (Chapter 2); designed the skill taxonomy and role catalog.", "<br>"],
             ["5–6", "Iteration 1: baseline", "Built text extraction and a first data generator; trained TF-IDF + Naive Bayes + SVM; 100% accuracy showed the data were too easy.", "<br>"],
             ["7–8", "Iteration 2: refinement", "Noisier generator; rule-based parser, PII removal and five-part scoring; role-affinity measure; role recommendation.", "<br>"],
             ["9–10", "First web version", "Flask app and JSON API with screening, job-match and insight pages; first 34 tests; Docker image and Render blueprint.", "<br>"],
             ["11–12", "Iteration 3: platform, report, demo", f"Accounts, PostgreSQL persistence and migrations, dashboard, shortlist management and security hardening; {NTESTS} tests on two databases; browser verification; final report.", "<br>"]],
            "Weekly PBL Progress Log", widths=[8, 20, 50, 22], center_cols=(0,))
    sec("3.2", "Requirements")
    p(f"ResumeIQ operates on text extracted from uploaded resumes. The classifiers are trained on {M['n_samples']:,} generated "
      "resumes; a command-line option (--csv) retrains the same pipeline on any CSV of labelled resumes, so no code change is "
      "needed to move from synthetic to real data. All libraries are open source and the pinned versions below were used for "
      "every result in this report [11]–[14], [19].")
    d.table(["Category", "Requirement"],
            [["Processor / RAM", f"Any x86-64 processor; 2 GB RAM or more. The running web worker, with the model and database loaded, used about {RSS} MB of resident memory (measured); no GPU is required"],
             ["Programming language", "Python 3.12 (Docker image); Python 3.13 for local development; HTML, CSS and JavaScript (user interface)"],
             ["Libraries / frameworks", "scikit-learn 1.9.1, NumPy 2.5.3, pandas 3.0.5, joblib 1.6.0 (machine learning); Flask 3.1.3, Gunicorn 26.2.0, Flask-Login, Flask-WTF, Flask-Limiter (web and accounts); SQLAlchemy 2.1.3, Alembic 1.20.0 (database); pypdf 6.17.0, python-docx 1.2.0, olefile 0.47 (parsing)"],
             ["Database", "SQLite (development, tests); PostgreSQL 16 (production, tests); Alembic migrations [19]"],
             ["Tools", "antiword (legacy .doc files); VS Code; pytest 9; Chromium (Playwright) for browser checks; Git and GitHub with a GitHub Actions workflow"],
             ["Deployment", "Docker container served by Gunicorn on Render with a managed PostgreSQL database (render.yaml blueprint) [15]"]],
            "Hardware and Software Requirements", widths=[26, 74])
    sec("3.3", "Feasibility")
    p(f"Training both classifiers, including 5-fold cross-validation, takes about {M['train_seconds']:.0f} seconds on a single CPU "
      "core, and the trained model file is under 3 MB. Screening all fourteen sample resumes (four file formats, including "
      f"text extraction and saving the results to the database) took a median of {LATENCY} s and recommending roles for one resume took about {LAT['match1_median_s'] * 1000:.0f} ms, so the "
      "complete PBL cycle (baseline, refinement and final system) was achievable within the twelve-week timeframe on ordinary "
      "student laptop hardware.")

    # ------------------------------------------------------------ Chapter 4
    d.chapter("ITERATIVE DESIGN AND DEVELOPMENT")
    sec("4.1", "System Architecture")
    p("A recruiter's browser talks over HTTPS to a Flask application served by Gunicorn inside a Docker container. The "
      "application has four parts: a security layer (response headers, CSRF checks, rate limits), an authentication blueprint, "
      "the page views and a JSON API. Behind them sit the machine-learning engine, loaded once at start-up from the trained "
      "model file, and a relational database that holds users, screenings and candidates (Figure 4.1). Section 4.4 describes the "
      "ML pipeline in detail: resume → text extraction → NLP parsing → normalisation → TF-IDF → Naive Bayes and SVM → "
      "five-part score → ranked shortlist.")
    d.figure(FIG / "fig_architecture.png", "System Architecture Diagram", 100)
    p("A resume is accepted as PDF, DOC, DOCX or TXT (up to 30 files of 5 MB each per run); the file type is checked by "
      "extension and content signature, text is extracted with pypdf, python-docx or antiword, and a file with no readable text "
      "(for example a scanned image) is rejected with a clear message. The parser then recognises skills, education, experience "
      "and contact details, removes the personal identifiers for scoring and maps each skill to one canonical token.")
    p("The TF-IDF vectoriser feeds a Multinomial Naive Bayes model and a calibrated linear SVM whose probabilities are "
      "averaged; the scoring engine combines them with cosine similarity, skill coverage, experience and education into a 0–100 "
      "score, and the result is saved against the logged-in user. Offline, the training script writes model.joblib and metrics.json.")
    sec("4.2", "Iteration 1: Baseline")
    p("The simplest working version generated resumes from the role catalog using role-specific experience-bullet templates, "
      "vectorised them with TF-IDF (unigrams and bigrams) and trained a Multinomial Naive Bayes classifier and a calibrated "
      "linear SVM on an 80/20 stratified split. All three predictors (the two models and their average) scored 1.000 accuracy "
      "on the hold-out set and 1.000 in 5-fold cross-validation.")
    p("A perfect score on a twelve-class problem was a warning sign rather than a success. Inspection showed that each role's "
      "bullet templates were unique to that role, so the label could be recovered from a handful of template phrases; the "
      "model was memorising the generator, not learning to separate roles. This finding motivated Iteration 2.")
    sec("4.3", "Iteration 2: Refinement")
    p("Iteration 2 made the data harder and the system more complete. The generator was changed so that resumes could no longer "
      "be identified by template phrases:")
    ul(["28% of experience bullets are generic (for example “participated in code reviews and daily stand-ups”) and carry no "
        "role information; 14% are borrowed from a neighbouring role, and 35% for hybrid resumes.",
        "25% of resumes are hybrids that mix the skills of a neighbouring role; 12% use a job title from a neighbouring role; "
        "20% are sparse resumes listing only three to six skills.",
        "Each candidate lists a random 35–90% of the role's core skills, so some resumes are only weakly characteristic of "
        "their role."])
    p(f"With these changes the hold-out accuracy moved to {0.996:.3f} (Naive Bayes), {0.992:.3f} (SVM) and {0.996:.3f} (ensemble), "
      f"and after the per-candidate skill-rate variation and a larger hybrid share it settled at {h['ensemble']['accuracy']:.3f} "
      "for all three. The data remain highly separable, which is a property of synthetic data, and this is stated as a "
      "limitation in Chapter 6 rather than tuned away. As a more meaningful check, five resumes written by hand in a different "
      "style from the generator were added to the test suite; all five were classified to the correct role.")
    p("Iteration 2 also improved the scoring. The first version measured role fit as the cosine similarity between the resume's "
      "and the job's role-probability vectors. Because the classifiers are confident, these vectors are almost one-hot, so a "
      "resume for a closely related role scored essentially zero: for the Data Scientist example job, the Machine Learning "
      "Engineer sample scored 0.004. Replacing the cosine with a role-affinity measure (full credit for the same role and 0.4 "
      "for neighbouring roles) raised it to 0.395 while keeping the Data Scientist sample at 0.983. The grade thresholds were "
      "recalibrated from 75/55/35 to 70/50/30 after observing that clearly well-matched resumes scored between the mid-sixties and the low seventies, and "
      "name-blind scoring was verified by a test showing that changing a resume's name and e-mail leaves its score unchanged.")
    sec("4.4", "Final Approach")
    p("The final system is a two-classifier text pipeline with a transparent scoring layer. Its components are:")
    ul([f"TF-IDF features: unigrams and bigrams, minimum document frequency 2, maximum 0.9, English stop-words removed, sublinear "
        f"term frequency, L2 normalisation, {M['n_features']:,} features after fitting. With smoothed inverse document "
        "frequency, the weight of term t in document d is shown below, and each vector is then length-normalised so that the "
        "dot product of two vectors equals their cosine similarity [3]–[5].",
        "Multinomial Naive Bayes (smoothing α = 0.05) [6]: the class posterior is proportional to the class prior times the "
        "product of the word likelihoods raised to their counts.",
        "Linear SVM (LinearSVC, C = 0.8) [7]–[9], calibrated with a sigmoid (cv = 3) [10] so that it outputs probabilities.",
        "Ensemble: the average of the Naive Bayes and calibrated SVM probabilities gives the role distribution of a document."])
    d.eq("w<sub>t,d</sub> = (1 + ln tf<sub>t,d</sub>) × ( ln[(1 + N) / (1 + df<sub>t</sub>)] + 1 )")
    d.eq("P(c | d) ∝ P(c) ∏<sub>t</sub> P(t | c)<sup>tf<sub>t,d</sub></sup>&nbsp;&nbsp;&nbsp;&nbsp; cos(a, b) = a · b / (‖a‖ ‖b‖)")
    p("The match score of a resume against a job description is a weighted sum of five components, each on a 0–1 scale. When "
      "the job description states no experience or education requirement, that component is dropped and the remaining weights "
      "are re-normalised (Table 4.1).")
    d.eq("Score = 100 × Σ<sub>k</sub> w<sub>k</sub> c<sub>k</sub> / Σ<sub>k</sub> w<sub>k</sub> &nbsp;&nbsp;(sum over the components available for the job)")
    d.table(["Component", "Weight", "How it is computed"],
            [["Text similarity", "40%", "TF-IDF cosine similarity between the name-blind resume and the job description, divided by a ceiling of 0.45 and capped at 1"],
             ["Skill coverage", "30%", "Share of the job's technical skills found in the resume; a related skill from the same family (for example MySQL for PostgreSQL) earns half credit"],
             ["Role fit", "15%", "p<sub>resume</sub><sup>T</sup> A p<sub>job</sub>, where p are role distributions and A is the role-affinity matrix (1 for the same role, 0.4 for neighbours)"],
             ["Experience", "10%", "min(1, estimated years / years required); years are the union of dated ranges in the experience section or the stated figure, whichever is larger"],
             ["Education", "5%", "1 if the highest degree meets the requirement, otherwise degree level / required level (1 = school … 5 = doctorate)"]],
            "Components of the Match Score", widths=[18, 10, 72], center_cols=(1,))
    p("Scores are graded Strong (70 or above), Good (50–69), Partial (30–49) and Weak (below 30), and the shortlist is the top "
      "N resumes by score. Besides ranking, the engine recommends roles for a single resume by combining text similarity to each "
      "role profile (30%), weighted skill fit to the role's core and secondary skills (35%) and the classifier probability (35%), "
      "and lists the core skills the resume lacks as skills to learn.")
    d.figure(FIG / "fig_pipeline.png", "ML Scoring Pipeline Data Flow", 80)
    sec("4.5", "Training Procedure")
    p("The labelled data are split 80/20 with stratification (1,920 training and 480 test resumes, 40 test resumes per role). "
      "Five-fold stratified cross-validation is run on the training portion with the TF-IDF vectoriser re-fitted inside every "
      "fold, so no vocabulary or document-frequency information leaks from the validation fold. The final vectoriser and "
      "classifiers are then fitted on the training split and evaluated once on the untouched test split; the model shipped "
      "with the application is exactly the model that the reported hold-out metrics describe.")
    d.table(["Component", "Configuration"],
            [["Dataset", f"{M['n_samples']:,} synthetic resumes, {M['n_roles']} roles × 200, generator seed 42"],
             ["Split", "80/20 stratified: 1,920 training / 480 test; 5-fold stratified cross-validation on the training split"],
             ["Text normalisation", "Contact details removed; skills replaced by canonical tokens; lower-cased; non-alphanumeric characters removed"],
             ["TF-IDF", f"ngram (1, 2), min_df 2, max_df 0.9, sublinear tf, English stop-words, max 30,000 features ({M['n_features']:,} used)"],
             ["Naive Bayes", "MultinomialNB, alpha = 0.05"],
             ["SVM", "LinearSVC (C = 0.8, random_state 42) wrapped in CalibratedClassifierCV (sigmoid, cv = 3)"],
             ["Ensemble", "Mean of the two predicted probability vectors; arg-max gives the predicted role"],
             ["Output", "model.joblib (vectoriser, both classifiers, labels) and metrics.json"]],
            "Dataset and Model Configuration", widths=[24, 76])

    sec("4.6", "Iteration 3: Multi-user Platform")
    p("The first web version was open to anyone and kept nothing, which suits a demonstration but not a recruiter who wants to "
      "return to yesterday's shortlist. Iteration 3 therefore added accounts, persistence and shortlist management without "
      "changing the ML pipeline: the stored results are exactly the engine's output, and a test asserts this. The data model has "
      "three tables (Table 4.3). Resume files themselves are never stored.")
    d.table(["Table", "Main columns", "Purpose and constraints"],
            [["users", "email (unique), name, password_hash, session_token, failed_logins, locked_until", "One row per recruiter; e-mail is lower-cased; the password is stored only as a scrypt hash"],
             ["screenings", "user_id, job_title, job_description, job_info, top_n, total, errors, created_at", "One screening run; deleting a user deletes the runs (ON DELETE CASCADE)"],
             ["candidates", "screening_id, user_id, rank, name, email, score, grade, recommended, status, notes, data (JSON)", "One scored resume; status is pending, shortlisted or rejected; indexed on user, screening, score and status"]],
            "Database Tables (SQLAlchemy models, created by an Alembic migration)", widths=[14, 44, 42])
    p("Security was designed in rather than added afterwards. The OWASP verification standard [16] guided the checklist, scrypt "
      "[17] the password storage and a Content Security Policy [18] the browser restrictions; Table 4.4 lists the controls, each "
      "covered by an automated test.")
    d.table(["Area", "Control in ResumeIQ"],
            [["Passwords", "At least 8 characters with a letter and a number; stored as scrypt hashes (Werkzeug default, N = 32768, r = 8, p = 1); a check costs about " + f"{MEAS['password_check_median_ms']:.0f} ms"],
             ["Login", "Unknown e-mail and wrong password give the same message and timing; 5 failures lock the account for 15 minutes; 15 attempts per minute per address; post-login redirects limited to same-site paths"],
             ["Sessions", "HttpOnly, SameSite=Lax and (in production) Secure cookies; a per-user session token that is rotated on password change so all other sessions stop working"],
             ["Requests", "CSRF token on every form and every state-changing API call; screening limited to 60 and job matching to 120 requests per hour per user; 30 sign-ups per hour per address"],
             ["Data access", "Every query is filtered by the logged-in user; another user's screening or candidate returns 404; CSV export neutralises spreadsheet formulas"],
             ["Browser", "Strict Content Security Policy (no inline scripts or styles), HSTS, same-origin referrer policy and no-store caching of account pages"],
             ["Secrets and deployment", "SECRET_KEY and DATABASE_URL come only from environment variables; production refuses to start without a secret key and, on Render, without a database"]],
            "Security Controls", widths=[16, 84], keep=True)

    # ------------------------------------------------------------ Chapter 5
    d.chapter("IMPLEMENTATION")
    sec("5.1", "Module Description")
    sub("", "Machine-learning package: resume_screening/")
    ul(["extractor.py: converts PDF (pypdf), DOCX (python-docx), DOC (antiword, with an olefile fallback) and TXT files to text, checks file signatures and raises user-readable errors for empty, encrypted or scanned files.",
        f"skills.py and parser.py: the {NSK}-skill taxonomy with aliases and related-skill families, section detection, contact-detail extraction, experience estimation (union of dated ranges), education-level detection and job-description parsing.",
        "text_utils.py, catalog.py and dataset.py: removal of personal identifiers, canonical skill tokens, the twelve job-role profiles and the synthetic resume generator.",
        "train.py and engine.py: train and evaluate Naive Bayes and the calibrated SVM and write the model and metrics; load the model, rank resumes against a job description, compute the five-part score and recommend roles."])
    sub("", "Web platform: app.py and webapp/")
    ul(["app.py: the application factory create_app(), which loads the configuration, initialises the extensions, registers the blueprints, error handlers and security headers, and exposes the WSGI application used by Gunicorn.",
        "settings.py and extensions.py: environment-driven configuration (SECRET_KEY, DATABASE_URL, cookie flags, production safeguards) and the shared SQLAlchemy, Alembic, Flask-Login, CSRF and rate-limiter objects.",
        "models.py and migrations/: the User, Screening and Candidate models and the Alembic revision that creates them; forms.py: validated registration, login, password-change and account-deletion forms.",
        "auth.py: sign-up, login, logout, lockout and account settings; views.py: the dashboard, screening list, screening detail, shortlist, job-match and insight pages; api.py: the JSON endpoints for screening, candidates, CSV export and job matching.",
        f"templates/ and static/: the interface in HTML, CSS and JavaScript (dynamic content is built with textContent so uploaded text cannot inject markup); tests/: {NTESTS} pytest tests; samples/: 14 fictional resumes; Dockerfile, start.sh, render.yaml and .github/workflows/ci.yml for deployment and CI."])
    sec("5.2", "Key Code Snippets")
    p("The normalisation function removes personal identifiers and turns each skill spelling variant into one token, so “sklearn” "
      "and “scikit-learn” become the same feature:")
    d.code(src(text_utils.normalize_for_model), "Name-blind text normalisation (text_utils.py)")
    p("On the account side, a failed login never reveals whether the e-mail exists, and repeated failures lock the account:")
    lg = src(auth_mod.login)
    lg = lg[lg.index("        # Unknown e-mail"): lg.index('        flash("Invalid email')].rstrip()
    d.code(textwrap.dedent(lg), "Failed-login handling and lockout (auth.py, excerpt)")
    sec("5.3", "User Interface / Demo")
    p("A new visitor sees the sign-up and login pages; the password field shows a strength meter and a Show toggle. After "
      "logging in, the recruiter lands on a dashboard with live totals (screenings, candidates screened, shortlisted, average "
      "score), the most recent screenings, the shortlist pipeline and the distribution of match grades. A sidebar gives access to "
      "New screening, Screenings, Shortlist, Job match and Model insights, and collapses to a menu on a phone.")
    p("To screen candidates, the recruiter pastes a job description or loads one of the twelve examples, drops resumes onto the "
      "upload area (or ticks the 14 built-in samples) and chooses how many candidates the AI should recommend. The resumes are "
      "scored by the same engine as before and the run is saved to the account.")
    d.figure(FIG / "ui_dashboard.png", "Dashboard After Logging In", 68)
    d.figure(FIG / "ui_screen_form.png", "New Screening Page with a Job Description and Resumes", 68)
    p("The screening page shows the job type detected from the description, the skills extracted from it and counts per status. "
      "Candidates are listed in rank order as a table or as cards, with score, grade, experience, education and key skills, and "
      "can be searched, filtered by grade or status and sorted. Selecting a candidate opens a panel with the five score "
      "components, the Naive Bayes and SVM predictions and the matched, related and missing skills, with buttons to shortlist, "
      "reject or reset the candidate and a notes field. “Shortlist AI top N” accepts the recommendation in one click.")
    d.figure(FIG / "ui_screening_detail.png", "Saved Screening: 15 Resumes Ranked, AI Top 5 Shortlisted", 68)
    p("The Shortlist page gathers the shortlisted candidates of every screening, with search, filters, notes and CSV export. "
      "The Job match page recommends roles for one resume, and Model insights reports the dataset, the model comparison and the "
      "confusion matrix and states that the data are synthetic.")
    d.figure(FIG / "ui_shortlist.png", "Shortlist Page Across All Screenings", 68)

    sec("5.4", "Interfaces and Deployment")
    p("The same engine serves the web pages and a JSON API, so the system can be used from a browser or called by another "
      "program after logging in. Table 5.1 lists the main endpoints. Uploads are accepted as multipart form data and errors "
      "are returned as JSON with a plain-language message.")
    d.table(["Endpoint", "Method", "Purpose"],
            [["/register, /login, /logout, /account", "GET, POST", "Sign up, log in, log out, change password or delete the account (rate-limited, CSRF-protected)"],
             ["/dashboard, /screenings, /screenings/new, /shortlist", "GET", "Dashboard, saved screenings, new screening form and the cross-screening shortlist"],
             ["/screenings/&lt;id&gt;", "GET", "One saved screening with its ranked candidates (owner only)"],
             ["/api/screen", "POST", "Rank uploaded resumes (up to 30) against a job description, save the run and return its URL"],
             ["/api/screenings[/id]", "GET, DELETE", "List, open or delete the user's screenings"],
             ["/api/candidates[/id|/bulk|/export.csv]", "GET, PATCH, POST", "Search, filter and page candidates; shortlist, reject, annotate or bulk-update them; export CSV"],
             ["/api/match, /api/roles, /api/samples, /api/model", "POST, GET", "Role recommendations for one resume, example job descriptions, sample resumes and training metrics"],
             ["/health", "GET", "Health check that also confirms the database is reachable"]],
            "Web Pages and JSON API Endpoints", widths=[38, 14, 48], center_cols=(1,))
    p("Deployment follows the standard container route. The Dockerfile starts from a slim Python 3.12 image, installs antiword "
      "for legacy .doc files and the pinned requirements, and trains the model while the image is built, so the deployed model "
      "is exactly the one that was evaluated. At start-up, start.sh checks the configuration, applies the Alembic migrations "
      "(retrying while the database wakes up) and launches Gunicorn with one worker and four threads, which keeps the resident "
      f"memory at about {RSS} MB (measured) inside the 512 MB limit of Render's free plan. The render.yaml blueprint creates the "
      "web service and a PostgreSQL database, generates SECRET_KEY, injects DATABASE_URL and sets REQUIRE_PERSISTENT_DB so that "
      "the site refuses to run on a throw-away database. A GitHub Actions workflow runs the tests on SQLite and PostgreSQL and "
      "builds the image, boots it against a throw-away PostgreSQL and checks /health on every push.")
    d.table(["Test file", "Tests", "What it checks"],
            [["test_skills_parser.py", str(TF["test_skills_parser.py"]), "Skill aliases and ambiguous words, text normalisation, contact details, experience from overlapping dates, education levels, job-description parsing"],
             ["test_extractor.py", str(TF["test_extractor.py"]), "TXT, DOCX, PDF and legacy DOC extraction, and friendly errors for empty, corrupt, scanned or unsupported files"],
             ["test_engine.py", str(TF["test_engine.py"]), "Metrics consistency, five hand-written resumes, ranking order, name-blind scoring, re-weighting, role recommendations"],
             ["test_app.py", str(TF["test_app.py"]), "Page rendering, security headers, no inline scripts or styles, health check, job match, restricted sample downloads, input validation, error pages"],
             ["test_auth.py", str(TF["test_auth.py"]), "Registration rules, hashed passwords, login and logout, identical failure messages, lockout, safe redirects, password change rotating sessions, account deletion, CSRF, rate limits, cookie flags"],
             ["test_screenings.py", str(TF["test_screenings.py"]), "Stored results equal engine output, shortlist, reject and notes, bulk updates, search, filter and paging, CSV export, deletion, isolation between users, dashboard counts"],
             ["test_config.py", str(TF["test_config.py"]), "Database URL normalisation, SECRET_KEY and persistent-database requirements in production, migrations build the same schema as the models"]],
            f"Automated Test Suite ({NTESTS} tests)", widths=[24, 8, 68], center_cols=(1,), keep=True)
    p("Besides the automated tests, the platform was driven in a real browser (Chromium) over HTTPS against PostgreSQL 16: an "
      "account was registered, resumes were screened, candidates were shortlisted, the CSV export was downloaded and the pages were "
      "checked at desktop and phone width with the console free of script and Content-Security-Policy errors. Start-up was also "
      "checked in production mode with a missing secret key, a missing database and a database fallback.")

    # ------------------------------------------------------------ Chapter 6
    d.chapter("RESULTS AND DISCUSSION")
    sec("6.1", "Evaluation Metrics")
    p("Role classification is a supervised problem, so it is evaluated with the standard classification metrics on the "
      f"{M['n_test']} held-out resumes: accuracy (share of resumes assigned the correct role), precision and recall (macro-averaged "
      "over the twelve roles) and the F1-score, the harmonic mean of precision and recall. Five-fold cross-validation on the "
      "training split gives a second, independent estimate of accuracy. Ranking quality cannot be measured against ground truth "
      "because no human ranking of the resumes exists, so it was examined qualitatively: whether resumes of the job's role "
      "rise to the top, and whether scores respond sensibly to missing skills, experience and education.")
    d.figure(FIG / "fig_metrics.png", "Evaluation Metrics: Final Model and Accuracy Across Data Iterations", 100)
    p("Three further instruments were used: (a) a set of five hand-written resumes, in a style different from the generator, that "
      "must be classified to the correct role; (b) behavioural tests of the scoring engine (ranking order, name-blindness, "
      f"re-weighting when a requirement is missing); and (c) {NTESTS} automated tests covering the parser, extractor, engine, "
      "accounts, persistence and web interface, plus verification of the pages in a real browser at desktop and phone width.")
    sec("6.2", "Results Across Iterations")
    d.table(["Version", "Training data", "Hold-out accuracy (NB / SVM / Ensemble)", "Key finding"],
            [["Iteration 1", "Template resumes only", "1.000 / 1.000 / 1.000", "Perfect score; label recoverable from template phrases, so the data were too easy"],
             ["Iteration 2a", "+ generic and borrowed bullets, hybrids, sparse resumes", "0.996 / 0.992 / 0.996", "Realistic noise lowered accuracy slightly; 5-fold CV 0.997 / 0.996"],
             ["Final (2b)", "+ per-candidate skill-rate variation, 25% hybrids", f"{h['naive_bayes']['accuracy']:.3f} / {h['svm']['accuracy']:.3f} / {h['ensemble']['accuracy']:.3f}", f"5-fold CV {cv['naive_bayes']['accuracy']:.3f} / {cv['svm']['accuracy']:.3f}; hand-written resumes 5/5 correct"]],
            "Model Evaluation Results Across Iterations", widths=[14, 30, 26, 30], center_cols=(2,))
    p(f"On the final model, the Naive Bayes classifier, the SVM and their ensemble each reached {h['ensemble']['accuracy'] * 100:.1f}% "
      f"accuracy ({N_CORRECT} of {M['n_test']} test resumes), with macro precision, recall and F1 of {h['ensemble']['precision']:.3f}. "
      "The only error is one Cybersecurity Analyst resume classified as a DevOps Engineer, a neighbouring role in the catalog "
      "that shares Linux, monitoring and networking skills (Figure 6.2).")
    d.figure(FIG / "fig_confusion.png", "Confusion Matrix of the Ensemble on the Hold-out Set", 62)
    d.table(["Job role", "Precision", "Recall", "F1-score", "Test resumes"],
            [[r["title"], f"{r['precision']:.3f}", f"{r['recall']:.3f}", f"{r['f1']:.3f}", str(r["support"])] for r in M["per_role"]],
            "Per-role Results of the Ensemble on the Hold-out Set", widths=[34, 16, 16, 16, 18], center_cols=(1, 2, 3, 4))
    p("To see the ranking behave end to end, the fourteen built-in sample resumes were screened against the example Data Scientist "
      f"job description (a median of {LATENCY} s for all fourteen, including text extraction from PDF, DOCX, DOC and TXT files and saving the run). "
      "Figure 6.3 and Table 6.3 show the highest-ranked candidates.")
    cands = RANK["candidates"][:8]
    d.table(["Rank", "Candidate", "Predicted role", "Score", "Grade", "Text sim.", "Skills"],
            [[str(c["rank"]), c["name"], c["predicted_role"]["title"], f"{c['score']:.1f}", c["grade"].replace(" match", ""),
              f"{c['components']['text_similarity']:.0f}", f"{c['components']['skills']:.0f}"] for c in cands],
            "Top Candidates for the Data Scientist Job (14 Sample Resumes)", widths=[8, 20, 27, 10, 12, 11, 12], center_cols=(0, 3, 4, 5, 6))
    d.figure(FIG / "fig_ranking.png", "Live Ranking of the Sample Resumes for the Data Scientist Job", 78)
    sec("6.3", "Platform Verification and Performance")
    p("The platform was measured through the application's own test client on SQLite, so every call used the real views, "
      "database writes and ML engine (Table 6.4). The figures describe one laptop-class machine and are not a load test.")
    d.table(["Measurement", "Result"],
            [["Screening 14 sample resumes (4 file formats), including extraction and saving", f"median {MEAS['screen14_median_s']:.3f} s, maximum {MEAS['screen14_max_s']:.3f} s"],
             ["Opening a 14-candidate screening list (API)", f"median {MEAS['candidate_list_median_ms']:.1f} ms"],
             ["Loading the dashboard", f"median {MEAS['dashboard_median_ms']:.1f} ms"],
             ["One password check (scrypt)", f"median {MEAS['password_check_median_ms']:.0f} ms (deliberately slow)"],
             ["Resident memory of the running web process", f"about {RSS} MB"],
             ["Automated tests", f"{NTESTS} passed on SQLite and on PostgreSQL 16"]],
            "Measured Performance and Verification of the Platform", widths=[68, 32], keep=True)
    sec("6.4", "Discussion")
    p("The most consistent observation is that the two classifiers agree: Naive Bayes and the calibrated SVM predicted the same "
      "role for every resume in the sample screening, and their one-error result on the hold-out set is shared. This is partly "
      "a property of the synthetic data, in which each role has a distinctive skill vocabulary; the ensemble's value would be "
      "expected to show on noisier real resumes, where the two models are likely to disagree more often. This was not tested.")
    p("The scoring layer, rather than the classifier, is what makes the output useful to a recruiter. In the Data Scientist "
      "example the two Data Scientist resumes scored in the strong band (72.0 and 70.7), related roles in the partial band, and "
      "unrelated roles below 30. Because every component is shown, a recruiter can see why a candidate ranked where they did, "
      "for instance a missing Deep Learning skill, and can override the score; the shortlist, reject and notes controls keep that "
      "human decision next to the AI recommendation. The related-skill rule and the role-affinity "
      "measure were introduced because the first, stricter versions penalised near-misses that a human reader would forgive.")
    p("Name-blind scoring was verified directly: replacing a resume's name and e-mail address leaves its score unchanged. This "
      "removes one channel for bias but is not a fairness guarantee, because other fields such as institution names or "
      "employment gaps can still correlate with protected characteristics; a proper audit needs real, demographically annotated "
      "resumes that were not available to the team.")
    p("Several defects were found only because the system was tested as a web service rather than a notebook: inline style "
      "attributes blocked by the Content Security Policy silently removed spacing; the CSV spreadsheet-injection guard altered "
      "phone numbers beginning with “+”; a loading overlay stayed visible because a CSS display rule overrode the hidden "
      "attribute; choosing an example job description before the script had loaded did nothing; and a sign-up limit of 10 per "
      "hour proved too tight for a shared network. Each was corrected and covered by a test or a browser check.")
    sec("6.5", "Limitations")
    ul([f"The classifiers were trained on {M['n_samples']:,} synthetic resumes. The 99.8% hold-out accuracy shows that the pipeline "
        "works and the roles are separable in the generated data; it is not a real-world accuracy estimate, and real resumes are "
        "expected to give lower and more variable results. The five hand-written resumes are a modest sanity check, not a "
        "substitute for real evaluation.",
        f"Extraction is rule-based over a {NSK}-skill taxonomy; skills, phrasings and date formats outside the rules are missed, "
        "and a trained named-entity model would be more robust.",
        "Scanned or image-only resumes are rejected (no OCR), and unusual layouts such as multi-column designs can reduce "
        "extraction quality.",
        "The score weights, the similarity ceiling (0.45), the affinity value (0.4) and the grade thresholds are design choices "
        "calibrated on the sample resumes, not parameters learned from recruiter decisions.",
        "The system supports twelve roles and English text only and is a decision aid that requires human review.",
        "The accounts have no e-mail verification or password reset, use library-default scrypt parameters, and count rate "
        "limits per worker, which suits the single-worker deployment but not a scaled-out one.",
        "Saved candidate records hold names, e-mails and phone numbers, so a real deployment needs a consent and retention "
        "policy; Render's free PostgreSQL plan also expires after about 30 days."])

    # ------------------------------------------------------------ Chapter 7
    d.chapter("TEAM REFLECTION AND LEARNING OUTCOMES")
    sec("7.1", "Individual Reflections")
    p(f"<b>{S1}:</b> I focused on the machine-learning pipeline (extractor, skill taxonomy and parser, TF-IDF, Naive Bayes and "
      "SVM training, data generator, scoring engine) and, in the last iteration, the database layer. The biggest thing I learned "
      "is that a perfect score is a question, not an answer: when the first model reached 100% accuracy I had to discover that "
      "the generator, not the model, was doing the work. Moving from a stateless demo to saved screenings taught me a second "
      "lesson: storing the engine's output unchanged, and testing that it is unchanged, kept the ML and the platform "
      "independent, and the Alembic migration forced me to think about the schema before any data existed.")
    p(f"<b>{S2}:</b> I focused on the interface, the account system, the automated tests and the deployment files. Building the "
      "interface with a strict Content Security Policy showed me how many small things can go wrong between a working model and a "
      "usable product, from blocked inline styles to a loading overlay that would not hide. Writing the login code taught me "
      "that security is mostly about the cases nobody demonstrates: identical messages for unknown users, lockout, rotating "
      "sessions on a password change and checking ownership on every query. The most valuable habit was driving the pages in a real "
      "browser, on PostgreSQL and at phone width, and writing a test for each defect once it had been found.")
    sec("7.2", "Team Learning")
    p("Splitting ownership along the pipeline/interface boundary worked well once the JSON response format of the engine was "
      "fixed early, because it allowed both members to work in parallel: the interface was built against a documented response "
      "shape while the scoring logic was still being refined underneath it. The same contract made Iteration 3 possible, since "
      "the database stores that response unchanged. What we would do differently is lock the response format even earlier; "
      "several interface components had to be reworked when the score breakdown and the related-skills field were added.")
    p("The change that most improved the project was the decision, after the first perfect score, to treat the evaluation "
      "itself as something to be tested. It led to a harder data generator, to a hand-written sanity check, to an honest "
      "limitations section, and to scoring components that a recruiter can read instead of a single opaque number. Both members "
      "also learned to review each other's work before every milestone, which caught several defects before they reached the "
      "demonstration.")
    sec("7.3", "Course Outcomes — Evidence Summary")
    d.figure(FIG / "fig_outcomes.png", "Course Outcomes", 46)
    ul(["Technical / ML competency: the Naive Bayes and SVM text classifiers, TF-IDF features, probability calibration and "
        "cosine-similarity scoring, evaluated with a hold-out set and cross-validation, demonstrate applied understanding of "
        "supervised text classification (Chapters 2 and 4).",
        "Problem framing and iteration: the weekly progress log (Table 3.1) and the Iteration 1 → Iteration 2 → Final Approach "
        "progression (Chapter 4) show the build evolving in response to specific findings, notably the first perfect score, the "
        "one-hot role-fit result and the need for accounts once results had to be kept.",
        "Teamwork and division of labour: the Team Roles table and the reflections above (Section 7.1) show a consistent "
        "pipeline/platform and interface/security split with equal contribution and joint review before each milestone.",
        f"Engineering rigour beyond the model: {NTESTS} automated tests on two databases, browser verification, defects found "
        "and fixed (Chapter 6), hashed passwords, CSRF protection, a strict Content Security Policy and a Docker and Render "
        "deployment show that the system was treated as a service to be verified, not only a model to be fitted.",
        "Honest self-assessment: Chapter 6 states plainly that the data are synthetic and that the headline accuracy is not a "
        "real-world estimate, which is the candid, reflective evaluation the PBL format asks for."])

    # ------------------------------------------------------------ Chapter 8
    d.chapter("CONCLUSION AND FUTURE SCOPE")
    sec("8.1", "Conclusion")
    p("ResumeIQ demonstrates that a classical machine-learning pipeline (TF-IDF features, a Multinomial Naive Bayes model and a "
      "calibrated linear SVM) combined with rule-based NLP extraction and a transparent five-part score can turn unstructured "
      "resumes into a ranked, explainable shortlist and into role recommendations, without using a candidate's name or contact "
      f"details and on ordinary laptop hardware. On {M['n_test']} held-out synthetic resumes the ensemble reached "
      f"{h['ensemble']['accuracy'] * 100:.1f}% accuracy, all five hand-written resumes were matched to the correct role, and fourteen "
      f"sample resumes in four file formats were screened and saved in about {LATENCY} s. Delivered as a multi-user Flask web "
      f"application with accounts, a PostgreSQL-backed history of screenings, shortlist management, {NTESTS} automated tests and a "
      "Docker and Render deployment package, the project addressed its driving question directly: text-based models can separate "
      "job roles and rank resumes in a way that a recruiter can inspect and act on. Because the training data are synthetic, the "
      "numerical results show that the pipeline works rather than how accurate it would be on real resumes.")
    sec("8.2", "Future Scope")
    ul(["Train and validate on real, labelled resumes (the --csv option already retrains the same pipeline), with proper consent "
        "and anonymisation, and run a fairness audit on demographically annotated data.",
        "Replace the rule-based extractor with a trained named-entity model, add optical character recognition for scanned "
        "resumes, and extend the skill taxonomy and role catalog beyond twelve roles and English.",
        "Learn the score weights and the similarity ceiling from recruiter decisions and feedback instead of fixing them by hand.",
        "Strengthen the accounts with e-mail verification, password reset, stronger scrypt or Argon2id parameters and a shared "
        "rate-limit store, and add organisations and roles so that a hiring team can share a shortlist.",
        "Add audit logging, a data-retention policy for stored candidate records, and monitoring on a paid Render database plan."])

    # ------------------------------------------------------------ References / Appendix
    refs = [
        "M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, \"Mitigating bias in algorithmic hiring: Evaluating claims and practices,\" in Proc. ACM Conf. on Fairness, Accountability, and Transparency (FAT*), Barcelona, Spain, 2020, pp. 469–481.",
        "J. Dastin, \"Amazon scraps secret AI recruiting tool that showed bias against women,\" Reuters, Oct. 10, 2018.",
        "K. Spärck Jones, \"A statistical interpretation of term specificity and its application in retrieval,\" Journal of Documentation, vol. 28, no. 1, pp. 11–21, 1972.",
        "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Information Processing &amp; Management, vol. 24, no. 5, pp. 513–523, 1988.",
        "C. D. Manning, P. Raghavan, and H. Schütze, Introduction to Information Retrieval. Cambridge, U.K.: Cambridge University Press, 2008.",
        "A. McCallum and K. Nigam, \"A comparison of event models for Naive Bayes text classification,\" in Proc. AAAI-98 Workshop on Learning for Text Categorization, 1998, pp. 41–48.",
        "C. Cortes and V. Vapnik, \"Support-vector networks,\" Machine Learning, vol. 20, no. 3, pp. 273–297, 1995.",
        "T. Joachims, \"Text categorization with support vector machines: Learning with many relevant features,\" in Proc. European Conf. on Machine Learning (ECML), 1998, pp. 137–142.",
        "R.-E. Fan, K.-W. Chang, C.-J. Hsieh, X.-R. Wang, and C.-J. Lin, \"LIBLINEAR: A library for large linear classification,\" Journal of Machine Learning Research, vol. 9, pp. 1871–1874, 2008.",
        "J. C. Platt, \"Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods,\" in Advances in Large Margin Classifiers, Cambridge, MA, USA: MIT Press, 1999, pp. 61–74.",
        "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
        "C. R. Harris et al., \"Array programming with NumPy,\" Nature, vol. 585, pp. 357–362, 2020.",
        "W. McKinney, \"Data structures for statistical computing in Python,\" in Proc. 9th Python in Science Conf., 2010, pp. 51–56.",
        "Pallets Projects, \"Flask documentation.\" [Online]. Available: https://flask.palletsprojects.com/ (accessed 2026).",
        "Render, \"Blueprint specification (render.yaml).\" [Online]. Available: https://render.com/docs/blueprint-spec (accessed 2026).",
        "OWASP Foundation, \"OWASP Application Security Verification Standard (ASVS), version 4.0.3,\" 2021. [Online]. Available: https://owasp.org/www-project-application-security-verification-standard/ (accessed 2026).",
        "C. Percival and S. Josefsson, \"The scrypt password-based key derivation function,\" RFC 7914, Internet Engineering Task Force, Aug. 2016.",
        "W3C, \"Content Security Policy Level 3,\" W3C Working Draft. [Online]. Available: https://www.w3.org/TR/CSP3/ (accessed 2026).",
        "M. Bayer, \"SQLAlchemy documentation\" and \"Alembic documentation.\" [Online]. Available: https://docs.sqlalchemy.org/ and https://alembic.sqlalchemy.org/ (accessed 2026).",
    ]
    d.special("REFERENCES")
    d.raw('<div class="refs">' + "".join(f'<p class="hang">[{i}] {r}</p>' for i, r in enumerate(refs, 1)) + "</div>")

    d.special("APPENDIX")
    d.raw('<h2>A.1 Full Source Code</h2>')
    d.toc.append((2, "A.1 Full Source Code", "A.1 Full Source Code"))
    d.p('[<a style="color:#0563c1">https://github.com/sadhanashan16/Resumescreening</a>]')
    d.raw('<h2>A.2 Complete Weekly PBL Log</h2>')
    d.toc.append((2, "A.2 Complete Weekly PBL Log", "A.2 Complete Weekly PBL Log"))
    d.p("The full week-by-week log is summarised in Table 3.1 (Chapter 3); this build's log spans the twelve-week PBL cycle "
        "beginning at the Zeroth Review (21 June 2026). The Mentor Remarks column of Table 3.1 is left for the mentor to complete "
        "and sign.")
    d.raw('<h2>A.3 Self and Peer Assessment</h2>')
    d.toc.append((2, "A.3 Self and Peer Assessment", "A.3 Self and Peer Assessment"))
    d.table(["Team Member", "Self-Rated Contribution (%)", "Peer-Rated Contribution (%)", "Remarks"],
            [[S1, "50%", "50%", "Built the extraction, NLP parsing, model training, scoring engine, data model and screening API."],
             [S2, "50%", "50%", "Built the web interface, account and security layer, tests, sample data and deployment package."]],
            None, widths=[26, 22, 22, 30], center_cols=(1, 2))
    return d
