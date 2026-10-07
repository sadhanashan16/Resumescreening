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

FIG = ROOT / "report" / "figures"
ASSETS = ROOT / "report" / "assets"
M = json.loads(config.METRICS_PATH.read_text())
LAT = json.loads((ROOT / "poster" / "assets" / "latency.json").read_text())
RANK = json.loads((ROOT / "report" / "ranking_demo.json").read_text())

TITLE = "ResumeIQ – AI-Based Resume Screening and Job Matching System"
S1, R1 = "Sadhana Shanmugam", "2104251040837"
S2, R2 = "Dhanya Sri Mohandass", "2104251040189"
h, cv = M["holdout"], M["cross_validation"]
LATENCY = f"{LAT['screen14_median_s'] + 1e-9:.2f}"
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
 <div><b>SIGNATURE</b><br>Ms. SWATHI L,<br><b>MENTOR</b><br><b>Assistant Professor</b><br>Dept. of Computer Science and Engineering<br>Chennai Institute of Technology,<br>Chennai – 69.</div>
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
<p>We would like to extend our thanks to the Project Co-ordinator <b>Ms. SWATHI L,</b> Assistant Professor, Department of Computer Science and Engineering, for their valuable suggestions throughout this project.</p>
<p>We wish to acknowledge the help received from our class advisors <b>Dr. G. IRIN LORETTA M.E.,</b> Assistant Professor, and <b>S.E. NEELA KANDAN M.TECH.,</b> Assistant Professor, of the Department of Computer Science and Engineering for their valuable suggestions and support toward the successful completion of the project.</p>
<p style="text-align:right;margin-top:62pt;margin-bottom:2pt;margin-right:10pt;font-size:12.5pt">{S1} ({R1})</p>
<p style="text-align:right;margin-right:10pt;font-size:12.5pt">{S2} ({R2})</p>
</div>"""


ABSTRACT = (
    "Recruiters routinely receive hundreds of resumes for a single vacancy, and screening them by hand is slow, inconsistent "
    "and prone to human error and bias, so qualified candidates can be overlooked. ResumeIQ is an AI-based resume analysis and "
    "job-matching system that automates this first screening stage. Resumes in PDF, DOC, DOCX and TXT formats are converted to "
    f"text, and a rule-based natural-language-processing layer extracts skills (from a {NSK}-skill taxonomy), education level, "
    "years of experience and contact details. Names, e-mail addresses and phone numbers are removed before scoring so that they "
    "cannot influence a ranking. The cleaned text is converted into TF-IDF vectors (unigrams and bigrams, "
    f"{M['n_features']:,} features), classified into one of {M['n_roles']} job roles by a Multinomial Naive Bayes model and a "
    "calibrated linear Support Vector Machine whose probabilities are averaged, and compared with a job description by cosine "
    "similarity. A transparent five-part match score (text similarity 40%, skill coverage 30%, role fit 15%, experience "
    "10% and education 5%) ranks the candidates and produces a top-N shortlist with matched, related and missing skills for "
    "every candidate; the same engine also recommends the best-fit roles for a single resume. The system is delivered as a "
    "Flask web application with a JSON API and is packaged with Docker and a Render blueprint. The models were trained on "
    f"{M['n_samples']:,} synthetic resumes ({M['n_roles']} roles × 200) because real resumes are personal data. On a held-out "
    f"test set of {M['n_test']} resumes the ensemble reached {h['ensemble']['accuracy'] * 100:.1f}% accuracy ({N_CORRECT}/{M['n_test']}), with "
    f"5-fold cross-validation accuracy of {cv['naive_bayes']['accuracy'] * 100:.1f}% (Naive Bayes) and {cv['svm']['accuracy'] * 100:.1f}% (SVM); "
    "all five hand-written resumes that the data generator never produced were matched to the correct role, and 14 sample "
    f"resumes in four file formats were screened in a median of {LATENCY} s. Because the training data are synthetic, these figures "
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
        ("UI", "User Interface"), ("WSGI", "Web Server Gateway Interface")]


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
<tr><td>{S1}<br>({R1})</td><td>ML Pipeline &amp; Backend Lead</td><td>Designed and implemented the resume text extraction (extractor.py), the rule-based NLP parser and skill taxonomy (parser.py, skills.py), the TF-IDF / Naive Bayes / SVM training and evaluation pipeline (train.py, dataset.py), the scoring and role-recommendation engine (engine.py), and the Flask JSON API.</td></tr>
<tr><td>{S2}<br>({R2})</td><td>Interface, Testing &amp; Deployment Lead</td><td>Designed and implemented the web interface (templates, CSS and JavaScript for the screening, job-match and model-insight pages), prepared the sample resumes and screenshots, wrote the automated test suite, containerised the application with Docker and prepared the Render blueprint and CI workflow.</td></tr>
</tbody></table></div>"""


# ==================================================================== chapters
def build_body() -> Doc:
    d = Doc()
    p, ul, sec, sub = d.p, d.ul, d.sec, d.sub

    # ------------------------------------------------------------ Chapter 1
    d.chapter("INTRODUCTION")
    sec("1.1", "Background")
    p("Hiring begins with a screening problem. A single advertised vacancy can attract hundreds or thousands of applications, and "
      "recruiters must decide, often in minutes per resume, which of them deserve an interview. Done by hand, this first-pass "
      "screening is slow, tiring and inconsistent: two reviewers may rank the same resume differently, one reviewer may judge "
      "differently at the start and the end of a long day, and a qualified candidate can be overlooked simply because the resume "
      "uses different wording from the job advertisement. Applicant tracking systems that filter on exact keywords reduce the "
      "workload but inherit the same weakness, because “machine learning” and “ML”, or “scikit-learn” and “sklearn”, are "
      "different strings to a keyword filter but the same skill to a person.")
    p("Resumes also arrive as unstructured documents in several file formats (PDF, Word and plain text) with no common layout. "
      "Before any comparison can be made, the text must be extracted, the sections must be located, and facts such as skills, "
      "education and years of experience must be recovered from free text. Machine learning offers a natural way to handle the "
      "comparison step: a text-classification model can learn which vocabulary characterises each job family, and a similarity "
      "measure over weighted term vectors can quantify how closely a resume matches a particular job description.")
    p("Automation is not automatically fair. A review of algorithmic-hiring practice found that vendors say little about how "
      "bias is actually validated [1], and a widely reported case in 2018 involved a company withdrawing an experimental "
      "machine-learning recruiting tool after it was found to disadvantage women [2]. A screening system should therefore be "
      "explainable, should keep personal identifiers out of its scoring, and should be positioned as a decision aid rather than "
      "a decision maker.")
    p("ResumeIQ was undertaken as the Project-Based Learning (PBL) component of the Machine Learning course (CS5305). It was "
      "deliberately scoped around the build–learn cycle that PBL is meant to teach: a baseline text classifier, a refinement "
      "driven by what the first results revealed, and a final system that the team can explain component by component rather "
      "than point at as a black box.")
    sec("1.2", "Driving Question")
    p("Can a classical machine-learning pipeline built from TF-IDF features, Naive Bayes and Support Vector Machine classifiers, and "
      "cosine similarity turn unstructured resumes into a ranked, explainable shortlist for a given job description, and "
      "recommend suitable job roles for a single resume, without using the candidate's name or contact details and while "
      "running on ordinary laptop hardware? And if two structurally different classifiers are used, does combining them give a "
      "more reliable role signal than either one alone?")
    p("This question narrows into a concrete, buildable task: extract skills, education and experience from resumes with NLP; "
      "represent resume and job text as TF-IDF vectors; classify each resume into one of twelve job roles with Naive Bayes and "
      "an SVM; and combine text similarity, skill coverage, role agreement, experience and education into a single score that a "
      "recruiter can inspect rather than simply trust.")
    sec("1.3", "Objectives")
    ul(["To accept resumes in PDF and DOC formats (and, in addition, DOCX and plain text) and convert them reliably into text.",
        "To extract key details (skills, education and experience) using natural-language-processing techniques, and to remove "
        "names and contact details before scoring.",
        "To match resumes with job descriptions and measure suitability using TF-IDF vectors and cosine similarity.",
        "To apply TF-IDF, Naive Bayes and SVM for ranking and classification, and to evaluate them with a held-out test set and "
        "cross-validation.",
        "To generate a shortlist of the top candidates automatically, with an explanation (matched, related and missing skills) "
        "for every candidate, and to recommend suitable job roles for a single resume.",
        "To deliver the system as a working website built with Python, Scikit-learn and Pandas, packaged for deployment on "
        "Render, and to document the weekly PBL progress and what the process taught each member."])
    sec("1.4", "Scope and Limitations")
    p(f"ResumeIQ models {M['n_roles']} job roles (Data Scientist, Machine Learning Engineer, Data Analyst, Data Engineer, "
      "Backend Developer, Frontend Developer, Full Stack Developer, DevOps Engineer, Mobile App Developer, QA Engineer, "
      "Cybersecurity Analyst and Business Analyst) and works on English-language, text-based resumes. Skills are recognised "
      f"from a curated taxonomy of {NSK} skills with aliases (for example “sklearn” for Scikit-learn), so skills outside the "
      "taxonomy are not detected. Scanned or image-only documents contain no text layer and are rejected with a clear message; "
      "optical character recognition is outside the scope of this build.")
    p(f"The classifiers were trained on {M['n_samples']:,} synthetic resumes generated from the role catalog, because real "
      "resumes are personal data and no real labelled corpus was available to the team. The reported accuracy therefore "
      "measures how well the pipeline separates the synthetic roles and must not be read as a real-world accuracy estimate "
      "(Chapter 6). The match score is a relative suitability indicator, not a verdict; the system stores no uploaded files and "
      "no candidate data, and every shortlist should be reviewed by a person.")

    # ------------------------------------------------------------ Chapter 2
    d.chapter("CONCEPT EXPLORATION")
    sec("2.1", "Related Approaches")
    sub("2.1.1", "Text representation and similarity")
    p("Spärck Jones showed in 1972 that a term is a more useful discriminator when it occurs in fewer documents, and proposed "
      "weighting terms by their inverse document frequency [3]. Salton and Buckley later compared many term-weighting schemes "
      "experimentally and found that schemes combining a term-frequency component, an inverse-document-frequency component and "
      "length normalisation performed well [4]. In the resulting TF-IDF representation each document becomes a sparse vector; "
      "after length normalisation, the cosine of the angle between two vectors measures how much weighted vocabulary the "
      "documents share [5]. This is exactly what is needed to compare a resume with a job description, and it needs no labelled "
      "data, which is why it forms the similarity component of ResumeIQ's score.")
    sub("2.1.2", "Probabilistic text classification")
    p("McCallum and Nigam compared two event models for Naive Bayes text classification and found that the multinomial model, "
      "which uses word counts, generally performed better than the multi-variate Bernoulli model when the vocabulary was large [6]. "
      "Naive Bayes is attractive for a project of this size because it trains in a single pass, works with small amounts of "
      "data, gives class probabilities directly and exposes which words drive a decision; it was therefore chosen as the first "
      "classifier. Its main weakness is the independence assumption, which makes its probabilities over-confident.")
    sub("2.1.3", "Support Vector Machines for text")
    p("Cortes and Vapnik introduced the soft-margin support-vector network [7]. Joachims argued that text categorisation suits "
      "SVMs because documents are high-dimensional, sparse and mostly linearly separable, and reported in his experiments that "
      "SVMs outperformed k-nearest-neighbour, Naive Bayes, Rocchio and decision-tree classifiers [8]. Linear SVMs for large sparse "
      "data are efficiently implemented in LIBLINEAR [9], which underlies scikit-learn's LinearSVC. An SVM outputs a distance "
      "from the decision boundary rather than a probability; Platt proposed fitting a sigmoid to these scores to obtain "
      "calibrated posterior probabilities [10], which ResumeIQ uses so that the SVM and Naive Bayes outputs can be averaged on "
      "the same scale.")
    sub("2.1.4", "Algorithmic hiring and fairness")
    p("The hiring literature adds a design constraint that the classification literature does not. Raghavan et al. reviewed how "
      "vendors of algorithmic hiring tools describe their bias-mitigation practices and found that public information on how "
      "these claims are validated is limited [1], and the 2018 withdrawal of an experimental recruiting tool that penalised "
      "women's resumes [2] illustrates how a model trained on historical data can reproduce historical bias. ResumeIQ responds "
      "in three modest ways: personal identifiers (name, e-mail, phone, links) are removed before scoring; every score is "
      "decomposed into visible components; and the interface and documentation state that the output is a decision aid.")
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
    p("The literature pointed the team toward the same starting point: represent text with TF-IDF, and begin with Naive Bayes "
      "and a linear SVM because they are the best-understood classifiers for sparse text and need no architecture decisions "
      "beyond a few regularisation settings (Iteration 1, Chapter 4). Because the two models rest on different assumptions "
      "(generative and independence-based on one side, margin-based on the other), the team decided to keep both and average "
      "their calibrated probabilities in Iteration 2, rather than choose one. The skill taxonomy, the five-part match score, "
      "the role-affinity measure and the name-blind scoring were the team's own additions, motivated by the explainability and "
      "fairness concerns in [1] and [2]: a transparent rule or a visible component was preferred to an opaque number.")

    # ------------------------------------------------------------ Chapter 3
    d.chapter("PROJECT PLANNING AND TEAM ORGANISATION")
    sec("3.1", "Weekly PBL Progress Log")
    p("The project ran across the full PBL cycle, from problem framing at the Zeroth Review (21 June 2026) through the final "
      "web-application build and testing. The table below summarises milestones and the work completed; the Mentor Remarks "
      "column is reserved for the mentor's own comments and sign-off.")
    d.table(["Week", "Milestone / Task", "Work Done", "Mentor Remarks"],
            [["1–2", "Problem framing, scope (Zeroth Review)", "Selected resume screening and job matching as the problem; fixed the input formats (PDF, DOC, DOCX, TXT), the twelve target job roles and the objectives; presented scope and aim at the Zeroth Review.", "<br><br><br>"],
             ["3–4", "Concept exploration, baseline plan", "Surveyed TF-IDF, Naive Bayes, SVM and algorithmic-hiring literature (Chapter 2); decided on a text pipeline with two classifiers; designed the skill taxonomy and role catalog.", "<br><br><br>"],
             ["5–7", "Iteration 1: baseline model", "Implemented PDF/DOCX/TXT text extraction and a first synthetic data generator; trained TF-IDF + Naive Bayes + SVM; obtained 100% hold-out accuracy and recognised that the data were too easy.", "<br><br><br>"],
             ["8–10", "Iteration 2: refinement", "Made the generator noisier (hybrid, sparse and ambiguous resumes); built the rule-based parser (sections, experience, education), PII removal and the five-part scoring; replaced the one-hot role-fit with a role-affinity measure; added role recommendation.", "<br><br><br>"],
             ["11–12", "Final approach, implementation, report, demo", "Built the Flask web app and JSON API with the screening, job-match and insight pages; wrote 34 automated tests; fixed defects found in testing; containerised with Docker, prepared the Render blueprint and CI workflow; compiled the final report.", "<br><br><br>"]],
            "Weekly PBL Progress Log", widths=[8, 20, 50, 22], center_cols=(0,))
    sec("3.2", "Requirements")
    p(f"ResumeIQ operates on text extracted from uploaded resumes. The classifiers are trained on {M['n_samples']:,} generated "
      "resumes; a command-line option (--csv) retrains the same pipeline on any CSV of labelled resumes, so no code change is "
      "needed to move from synthetic to real data. All libraries are open source and the pinned versions below were used for "
      "every result in this report [11]–[14].")
    d.table(["Category", "Requirement"],
            [["Processor / RAM", "Any x86-64 processor; 2 GB RAM or more. The running web worker used about 184 MB of resident memory (measured); no GPU is required"],
             ["Programming language", "Python 3.12 (Docker image); Python 3.13 for local development; HTML, CSS and JavaScript (user interface)"],
             ["Libraries / frameworks", "scikit-learn 1.9.1, NumPy 2.5.3, pandas 3.0.5, joblib 1.6.0 (machine learning); Flask 3.1.3, Gunicorn 26.2.0 (web); pypdf 6.17.0, python-docx 1.2.0, olefile 0.47 (resume parsing)"],
             ["External tool", "antiword (text extraction from legacy .doc files, installed in the Docker image)"],
             ["Development environment", "VS Code; Flask development server; pytest 9 for testing; Chromium (Playwright) for browser verification"],
             ["Version control / CI", "Git and GitHub (repository: sadhanashan16/Resumescreening); GitHub Actions workflow"],
             ["Deployment", "Docker container served by Gunicorn on Render (render.yaml blueprint) [15]"]],
            "Hardware and Software Requirements", widths=[26, 74])
    sec("3.3", "Feasibility")
    p(f"Training both classifiers, including 5-fold cross-validation, takes about {M['train_seconds']:.0f} seconds on a single CPU "
      "core, and the trained model file is under 3 MB. Screening all fourteen sample resumes (four file formats, including "
      f"text extraction) took a median of {LATENCY} s and recommending roles for one resume took about {LAT['match1_median_s'] * 1000:.0f} ms, so the "
      "complete PBL cycle (baseline, refinement and final system) was achievable within the twelve-week timeframe on ordinary "
      "student laptop hardware.")
    p("The most time-consuming part of the project was not model training but the parts around the model: the skill taxonomy "
      "and its aliases, reliable parsing of dates and degrees, a realistic data generator, and a safe, verified web interface.")

    # ------------------------------------------------------------ Chapter 4
    d.chapter("ITERATIVE DESIGN AND DEVELOPMENT")
    sec("4.1", "System Architecture")
    p("The end-to-end pipeline runs: uploaded resume → text extraction → NLP parsing (sections, skills, education, experience, "
      "contact details) → normalisation (personal identifiers removed, skills collapsed to canonical tokens) → TF-IDF "
      "vectorisation → Naive Bayes and SVM role probabilities → ensemble → five-part scoring against the job description → "
      "ranked shortlist or role recommendations delivered through a Flask web application and JSON API. Figure 4.1 shows this as "
      "a block diagram; each block is described below it.")
    p("Input and extraction: a resume is accepted as PDF, DOC, DOCX or TXT (up to 30 files of 5 MB each per run). The file type "
      "is checked by extension and by content signature, and text is extracted with pypdf, python-docx or antiword; a file with "
      "no readable text (for example a scanned image) is rejected with an explanatory message.")
    d.figure(FIG / "fig_architecture.png", "System Architecture Diagram", 100)
    p(f"NLP parsing and normalisation: the parser splits the text into sections, recognises skills from the {NSK}-skill taxonomy, "
      "estimates years of experience from date ranges and stated figures, detects the highest degree, and extracts contact "
      "details. For scoring, the name, e-mail, phone numbers and links are removed, and every recognised skill is replaced by a "
      "single canonical token so that “sklearn” and “scikit-learn” are the same feature.")
    p("Classification and scoring: the TF-IDF vectoriser feeds a Multinomial Naive Bayes model and a calibrated linear SVM; "
      "their probabilities are averaged into a role distribution. The scoring engine combines this with cosine similarity, "
      "skill coverage, experience and education into a 0–100 score. Offline, the training script builds the dataset, fits the "
      "models and writes model.joblib and metrics.json, which the web application loads at start-up.")
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
    sub("", "Job roles modelled")
    d.table(["Job role", "Core skills used by the generator and the role profile"],
            [[r["title"], ", ".join(r["core"])] for r in ROLES], "Job Roles Modelled and Their Core Skills", widths=[26, 74])
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

    # ------------------------------------------------------------ Chapter 5
    d.chapter("IMPLEMENTATION")
    sec("5.1", "Module Description")
    sub("", "Machine-learning package: resume_screening/")
    ul(["extractor.py: converts PDF (pypdf), DOCX (python-docx), DOC (antiword, with an olefile fallback) and TXT files to text, checks file signatures and raises user-readable errors for empty, encrypted or scanned files.",
        f"skills.py: the {NSK}-skill taxonomy with aliases, a case-sensitive guard for ambiguous words (Excel, React, Spring), a regular-expression extractor, and related-skill families used for partial credit.",
        "parser.py: section detection, contact-detail extraction, experience estimation (union of dated ranges), education-level detection, and job-description parsing.",
        "text_utils.py: removal of e-mails, URLs and phone numbers, and canonicalisation of skills into vocabulary tokens.",
        "catalog.py and dataset.py: the twelve job-role profiles and the synthetic resume generator with the noise sources described in Chapter 4.",
        "train.py: builds the dataset, runs cross-validation, trains Naive Bayes and the calibrated SVM, evaluates on the hold-out set and writes the model and metrics.",
        "engine.py: loads the model, ranks resumes against a job description, computes the five-part score and recommends roles for a single resume."])
    sub("", "Web application")
    ul(["app.py: the Flask application with four pages (home, screen candidates, find job match, model insights), a JSON API (/api/screen, /api/match, /api/roles, /api/samples, /api/model, /health), upload validation and security headers.",
        "templates/ and static/: the user interface in HTML, CSS and JavaScript; dynamic content is built with textContent so that uploaded text can never inject markup, and a strict Content Security Policy is enforced.",
        "tests/: 34 pytest tests; samples/: 14 fictional sample resumes in PDF, DOCX, DOC and TXT formats; Dockerfile, render.yaml and .github/workflows/ci.yml for deployment and CI."])
    sec("5.2", "Key Code Snippets")
    p("The normalisation function removes personal identifiers and turns each skill spelling variant into one token, so “sklearn” "
      "and “scikit-learn” become the same feature:")
    d.code(src(text_utils.normalize_for_model), "Name-blind text normalisation (text_utils.py)")
    p("The training script defines the three model components; the SVM is wrapped in a sigmoid calibrator:")
    d.code(src(train_mod.make_vectorizer) + "\n\n" + src(train_mod.make_nb) + "\n\n" + src(train_mod.make_svm),
           "TF-IDF, Naive Bayes and calibrated SVM definitions (train.py)")
    p("Skill coverage gives full credit for a skill the resume lists and half credit for a related skill from the same family:")
    d.code(src(eng_mod.ScreeningEngine._skill_overlap), "Skill coverage with related-skill partial credit (engine.py)")
    p("The final score is the re-normalised weighted sum of the components that are available for the job description:")
    sc = src(eng_mod.ScreeningEngine.score_resume)
    sc = sc[: sc.index("    have_set = set(job")].rstrip()
    d.code(sc, "Five-part weighted scoring (engine.py, excerpt)")
    sec("5.3", "User Interface / Demo")
    p("The home page explains the five-stage pipeline and links to the two tools. In recruiter mode (Screen candidates) the "
      "user pastes a job description or loads one of the twelve example descriptions, adds resumes by drag-and-drop (or ticks the "
      "built-in sample resumes for a quick demonstration) and chooses the shortlist size.")
    d.figure(FIG / "ui_home.png", "Home Page of ResumeIQ", 74)
    d.figure(FIG / "ui_screen_form.png", "Screen Candidates Page with a Job Description and Resumes", 74)
    p("The results page shows the job type detected from the description (with the classifier's confidence), the skills "
      "extracted from it and summary counts, followed by one card per candidate in rank order. Each card shows the score and "
      "grade, the predicted role, estimated experience and education, and the matched, related (partial credit) and missing "
      "skills; an expandable panel gives the per-component score bars and the separate Naive Bayes and SVM predictions. The "
      "shortlist and the full ranking can be downloaded as CSV, with spreadsheet formula characters neutralised.")
    d.figure(FIG / "ui_screen_results.png", "Screening Results: Ranked Candidates with Skill Evidence", 74)
    p("In candidate mode (Find job match), a single resume, pasted text or a sample is analysed and the best-fit roles are "
      "listed with their scores, the skills already matched and the skills to learn. The Model insights page reports the "
      "dataset, the model comparison, the per-role results, the confusion matrix and the most predictive terms, and states "
      "prominently that the data are synthetic.")
    d.figure(FIG / "ui_match_results.png", "Find Job Match: Role Recommendations for One Resume", 74)
    d.figure(FIG / "ui_insights.png", "Model Insights Page", 74)
    p("Uploaded files are read into memory, scored and discarded; nothing is written to disk or stored. File type is validated "
      "by extension and content signature, size and count are limited, error responses never expose internals, and the "
      "browser is restricted by a Content Security Policy that blocks inline scripts and styles.")

    sec("5.4", "Interfaces and Deployment")
    p("The same engine serves both the web pages and a JSON API, so the system can be used from a browser or called by another "
      "program. Table 5.1 lists the endpoints. Uploads are accepted as multipart form data; the resumes are read into memory, "
      "scored and discarded, and error responses are returned as JSON with a plain-language message.")
    d.table(["Endpoint", "Method", "Purpose"],
            [["/", "GET", "Home page with the pipeline overview"],
             ["/screen, /match, /insights", "GET", "Recruiter screening page, single-resume job-match page and model-insights page"],
             ["/api/screen", "POST", "Rank uploaded resumes (up to 30) against a job description and return the shortlist as JSON"],
             ["/api/match", "POST", "Recommend job roles for one resume (uploaded file, pasted text or a built-in sample)"],
             ["/api/roles, /api/samples, /api/model", "GET", "Example job descriptions, sample resume list and the stored training metrics"],
             ["/health", "GET", "Health check used by the hosting platform"]],
            "Web Pages and JSON API Endpoints", widths=[34, 12, 54], center_cols=(1,), keep=True)
    p("Deployment follows the standard container route for a machine-learning web service. The Dockerfile starts from a slim "
      "Python 3.12 image, installs antiword for legacy .doc files, installs the pinned requirements, and trains the model while "
      "the image is built, so the container starts immediately and the deployed model is exactly the one that was evaluated. "
      "The application runs under Gunicorn with one worker and four threads, which keeps the resident memory at about 184 MB "
      "(measured) and therefore inside the 512 MB limit of Render's free plan. A render.yaml blueprint describes the web "
      "service and its health check, and a GitHub Actions workflow runs the tests and builds the image on every push.")
    d.table(["Test file", "Tests", "What it checks"],
            [["test_skills_parser.py", "12", "Skill aliases and ambiguous words, Java versus JavaScript, text normalisation, contact details, experience from overlapping dates, education levels, job-description parsing"],
             ["test_extractor.py", "9", "TXT, DOCX, PDF and legacy DOC extraction, and friendly errors for empty, corrupt, scanned or unsupported files"],
             ["test_engine.py", "6", "Metrics file consistency, five hand-written resumes, ranking order, name-blind scoring, re-weighting when a requirement is missing, role recommendations"],
             ["test_app.py", "7", "Page rendering and security headers, screening with uploads, validation of bad input, the 30-file limit, role matching and restricted sample downloads"]],
            "Automated Test Suite (34 tests)", widths=[24, 9, 67], center_cols=(1,), keep=True)
    p("Besides the automated tests, each page was driven in a real browser (Chromium): a job description was loaded, resumes were "
      "uploaded, the CSV export was downloaded and the model-insights page was opened, with the browser console checked for "
      "script and Content-Security-Policy errors. The deployed configuration was also checked by installing only the pinned "
      "requirements into a clean environment, training the model and serving the application with Gunicorn.")

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
      "re-weighting when a requirement is missing); and (c) 34 automated tests covering the parser, extractor, engine and "
      "web interface, plus verification of the pages in a real browser at desktop width and of the screening page at phone width.")
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
      f"job description (a median of {LATENCY} s for all fourteen, including text extraction from PDF, DOCX, DOC and TXT files). "
      "Figure 6.3 and Table 6.3 show the highest-ranked candidates.")
    cands = RANK["candidates"][:8]
    d.table(["Rank", "Candidate", "Predicted role", "Score", "Grade", "Text sim.", "Skills"],
            [[str(c["rank"]), c["name"], c["predicted_role"]["title"], f"{c['score']:.1f}", c["grade"].replace(" match", ""),
              f"{c['components']['text_similarity']:.0f}", f"{c['components']['skills']:.0f}"] for c in cands],
            "Top Candidates for the Data Scientist Job (14 Sample Resumes)", widths=[8, 20, 27, 10, 12, 11, 12], center_cols=(0, 3, 4, 5, 6))
    d.figure(FIG / "fig_ranking.png", "Live Ranking of the Sample Resumes for the Data Scientist Job", 78)
    sec("6.3", "Discussion")
    p("The most consistent observation is that the two classifiers agree: Naive Bayes and the calibrated SVM predicted the same "
      "role for every resume in the sample screening, and their one-error performance on the hold-out set is shared. This is "
      "partly a property of the synthetic data, in which each role has a distinctive skill vocabulary, but it also means that "
      "the ensemble adds robustness rather than changing outcomes here. Its value would be expected to show on noisier real "
      "resumes, where a probabilistic and a margin-based model are likely to disagree more often; this was not tested.")
    p("The scoring layer, rather than the classifier, is what makes the output useful to a recruiter. In the Data Scientist "
      "example the two Data Scientist resumes scored in the strong band (72.0 and 70.7), related roles scored in the partial band "
      "because they share part of the skill set, and unrelated roles scored below 30. Because every component is shown, a "
      "recruiter can see why a candidate ranked where they did, for instance a missing Deep Learning skill or an experience "
      "shortfall, and can override the score. The related-skill rule (half credit) and the role-affinity measure were both "
      "introduced because the first, stricter versions penalised candidates for what a human reader would call near-misses.")
    p("Name-blind scoring was verified directly: replacing a resume's name and e-mail address leaves its score "
      "unchanged. This removes one channel through which bias could enter, but it is not a fairness guarantee: other fields, such "
      "as institution names or employment gaps, can still correlate with protected characteristics in real data, and a proper "
      "fairness audit would need real, demographically annotated resumes that were not available to the team.")
    p("Several defects were found and fixed only because the system was tested as a real web service rather than as a notebook. "
      "A file-name fallback produced “Priya Sharma Resume” instead of “Priya Sharma” because an underscore is not a word boundary "
      "in a regular expression; inline style attributes were blocked by the Content Security Policy and silently removed "
      "spacing; the spreadsheet-injection guard in the CSV export altered phone numbers that begin with “+”; and the confusion "
      "matrix headers were clipped on the insights page. Each was corrected and covered by a test or a browser check.")
    sec("6.4", "Limitations")
    ul([f"The classifiers were trained on {M['n_samples']:,} synthetic resumes. The 99.8% hold-out accuracy shows that the pipeline "
        "works and that the roles are separable in the generated data; it is not a real-world accuracy estimate, and real resumes "
        "are expected to give lower and more variable results. The test suite contains five hand-written resumes as a modest "
        "sanity check, not as a substitute for real evaluation.",
        f"Skill, education and experience extraction is rule-based over a {NSK}-skill taxonomy; skills, phrasings and date formats "
        "outside these rules are missed, and a trained named-entity model would be more robust.",
        "Scanned or image-only resumes are rejected because there is no optical character recognition; very unusual layouts "
        "(multi-column designs, text in images) can reduce extraction quality.",
        "The score weights, the similarity ceiling (0.45), the affinity value (0.4) and the grade thresholds are design choices "
        "made by the team and calibrated on the sample resumes, not parameters learned from recruiter decisions.",
        "The system supports twelve roles and English text only, keeps no database or user accounts, and is a decision aid that "
        "requires human review."])

    # ------------------------------------------------------------ Chapter 7
    d.chapter("TEAM REFLECTION AND LEARNING OUTCOMES")
    sec("7.1", "Individual Reflections")
    p(f"<b>{S1}:</b> I focused on the machine-learning pipeline: the text extractor, the skill taxonomy and parser, the TF-IDF, "
      "Naive Bayes and SVM training code, the data generator and the scoring engine. The biggest thing I learned is that a "
      "perfect score is a question, not an answer: when the first model reached 100% accuracy I had to go back and discover that "
      "the generator, not the model, was doing the work. Making the data realistically hard, and then accepting that it was "
      "still easy and saying so, taught me more about evaluation than the models themselves. The hardest part was the parser: "
      "dates, degrees and skills are written in so many ways that every rule had to be tested against awkward examples.")
    p(f"<b>{S2}:</b> I focused on the web interface, the sample resumes, the automated tests and the deployment files. "
      "Building the interface in plain HTML, CSS and JavaScript with a strict Content Security Policy showed me how many small "
      "things can go wrong between a working model and a usable product: blocked inline styles, clipped chart labels, and a "
      "CSV export that quietly changed phone numbers. The most valuable habit was checking the pages in a real browser, "
      "including at phone width, instead of trusting that the code looked correct, and writing a test for each defect once it "
      "had been found.")
    sec("7.2", "Team Learning")
    p("Splitting ownership along the pipeline/interface boundary worked well once the JSON response format of the engine was "
      "fixed early, because it allowed both members to work in parallel: the interface was built against a documented response "
      "shape while the scoring logic was still being refined underneath it. What we would do differently if we restarted the "
      "cycle is lock that response format even earlier; several interface components had to be reworked when the score "
      "breakdown and the related-skills field were added in Iteration 2.")
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
        "progression (Chapter 4) show the build evolving in response to specific findings, notably the first perfect score and "
        "the one-hot role-fit result.",
        "Teamwork and division of labour: the Team Roles table and the reflections above (Section 7.1) show a consistent "
        "pipeline/interface split with equal contribution and joint review before each milestone.",
        "Engineering rigour beyond the model: 34 automated tests, browser verification, defects found and fixed (Chapter 6), "
        "upload validation, a strict Content Security Policy and a Docker-based deployment show that the system was treated as a "
        "service to be verified, not only a model to be fitted.",
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
      f"sample resumes in four file formats were screened in about {LATENCY} s. Delivered as a tested Flask web application with a "
      "JSON API and a Docker and Render deployment package, the project addressed its driving question directly: text-based "
      "models can separate job roles and rank resumes in a way that a recruiter can inspect. Because the training data are "
      "synthetic, the numerical results show that the pipeline works rather than how accurate it would be on real resumes.")
    sec("8.2", "Future Scope")
    ul(["Train and validate on real, labelled resumes (the --csv option already retrains the same pipeline), with the "
        "consent and anonymisation procedures that personal data requires, and report real-world accuracy.",
        "Replace the rule-based extractor with a trained named-entity model and extend the skill taxonomy and role catalog "
        "beyond twelve roles and English-language resumes.",
        "Add optical character recognition so that scanned resumes can be processed.",
        "Carry out a fairness audit on real, demographically annotated data, and add monitoring so that score distributions can "
        "be compared across groups.",
        "Learn the score weights and the similarity ceiling from recruiter decisions instead of fixing them by hand, and add "
        "recruiter feedback to refine rankings.",
        "Add persistent storage, user accounts and audit logging, and deploy the packaged container on Render with usage monitoring."])

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
            [[S1, "50%", "50%", "Built the extraction, NLP parsing, model training and scoring engine."],
             [S2, "50%", "50%", "Built the web interface, tests, sample data and deployment package."]],
            None, widths=[26, 22, 22, 30], center_cols=(1, 2))
    return d
