"""Train and evaluate the resume -> job-role classifiers.

    python -m resume_screening.train                 # synthetic data
    python -m resume_screening.train --csv data.csv  # your own labelled resumes

Pipeline: text normalisation -> TF-IDF (1-2 grams) -> Multinomial Naive Bayes
and a calibrated linear SVM. Their probabilities are averaged for the final
prediction. Metrics are measured on a held-out stratified test split and with
5-fold cross-validation on the training split, then written next to the model.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from . import __version__
from .catalog import ROLE_BY_ID, ROLE_BY_TITLE, ROLES
from .config import METRICS_PATH, MODEL_DIR, MODEL_PATH, RANDOM_STATE
from .dataset import generate_dataset
from .text_utils import normalize_for_model

TOKEN_PATTERN = r"(?u)\b[a-z][a-z0-9_]+\b"


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True,
        stop_words="english", token_pattern=TOKEN_PATTERN, max_features=30000,
    )


def make_nb() -> MultinomialNB:
    return MultinomialNB(alpha=0.05)


def make_svm() -> CalibratedClassifierCV:
    return CalibratedClassifierCV(LinearSVC(C=0.8, random_state=RANDOM_STATE), cv=3, method="sigmoid")


def load_csv(path: str, text_col: str, label_col: str) -> list[tuple[str, str]]:
    df = pd.read_csv(path)
    rows, skipped = [], set()
    for text, label in zip(df[text_col].astype(str), df[label_col].astype(str)):
        rid = label if label in ROLE_BY_ID else getattr(ROLE_BY_TITLE.get(label), "get", lambda *_: None)("id")
        if rid:
            rows.append((text, rid))
        else:
            skipped.add(label)
    if skipped:
        print(f"warning: ignored labels not in the role catalog: {sorted(skipped)}")
    if not rows:
        raise SystemExit("no usable rows in CSV")
    return rows


def _scores(y_true, y_pred) -> dict:
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {"accuracy": round(accuracy_score(y_true, y_pred), 4), "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f, 4)}


def _top_features(vectorizer, svm, labels, k=8) -> dict:
    names = np.array(vectorizer.get_feature_names_out())
    coefs = np.mean([c.estimator.coef_ for c in svm.calibrated_classifiers_], axis=0)
    out = {}
    for i, label in enumerate(labels):
        idx = np.argsort(coefs[i])[::-1][:k]
        out[label] = [n.replace("skill_", "").replace("_", " ") for n in names[idx]]
    return out


def train(rows: list[tuple[str, str]], source: str) -> dict:
    t0 = time.time()
    texts = [normalize_for_model(t) for t, _ in rows]
    y = np.array([r for _, r in rows])
    labels = [r["id"] for r in ROLES if r["id"] in set(y)]

    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    # cross-validation (vectoriser refit inside every fold - no leakage)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv = {}
    for name, factory in (("naive_bayes", make_nb), ("svm", make_svm)):
        pipe = make_pipeline(make_vectorizer(), factory())
        pred = cross_val_predict(pipe, X_tr, y_tr, cv=skf, n_jobs=1)
        cv[name] = _scores(y_tr, pred)

    vec = make_vectorizer()
    Xv_tr = vec.fit_transform(X_tr)
    Xv_te = vec.transform(X_te)
    nb = make_nb().fit(Xv_tr, y_tr)
    svm = make_svm().fit(Xv_tr, y_tr)
    assert list(nb.classes_) == list(svm.classes_)
    classes = list(nb.classes_)

    p_nb, p_svm = nb.predict_proba(Xv_te), svm.predict_proba(Xv_te)
    p_ens = (p_nb + p_svm) / 2
    pred = {"naive_bayes": np.array(classes)[p_nb.argmax(1)],
            "svm": np.array(classes)[p_svm.argmax(1)],
            "ensemble": np.array(classes)[p_ens.argmax(1)]}
    holdout = {k: _scores(y_te, v) for k, v in pred.items()}

    p, r, f, support = precision_recall_fscore_support(y_te, pred["ensemble"], labels=classes, zero_division=0)
    per_role = [{"id": c, "title": ROLE_BY_ID[c]["title"], "precision": round(float(p[i]), 3),
                 "recall": round(float(r[i]), 3), "f1": round(float(f[i]), 3), "support": int(support[i])}
                for i, c in enumerate(classes)]
    cm = confusion_matrix(y_te, pred["ensemble"], labels=classes)

    # ship the model that the reported hold-out metrics describe
    bundle = {"vectorizer": vec, "nb": nb, "svm": svm, "labels": classes, "version": __version__}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH, compress=3)

    metrics = {
        "version": __version__,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_source": source,
        "n_samples": len(rows), "n_train": len(X_tr), "n_test": len(X_te),
        "n_features": int(Xv_tr.shape[1]), "n_roles": len(classes),
        "holdout": holdout, "cross_validation": cv,
        "per_role": per_role,
        "confusion_matrix": {"labels": [ROLE_BY_ID[c]["title"] for c in classes], "matrix": cm.tolist()},
        "top_features": {ROLE_BY_ID[k]["title"]: v for k, v in _top_features(vec, svm, classes).items()},
        "train_seconds": round(time.time() - t0, 1),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="CSV of labelled resumes (labels = role ids or titles from the catalog)")
    ap.add_argument("--text-col", default="text")
    ap.add_argument("--label-col", default="role")
    ap.add_argument("--n-per-role", type=int, default=200, help="synthetic resumes per role")
    ap.add_argument("--seed", type=int, default=RANDOM_STATE)
    args = ap.parse_args(argv)

    if args.csv:
        rows, source = load_csv(args.csv, args.text_col, args.label_col), f"csv:{args.csv}"
    else:
        rows, source = generate_dataset(args.n_per_role, args.seed), f"synthetic ({args.n_per_role}/role, seed {args.seed})"
    print(f"training on {len(rows)} resumes from {source} ...")
    m = train(rows, source)
    for k, v in m["holdout"].items():
        print(f"  holdout {k:<12} acc={v['accuracy']:.3f} f1={v['f1']:.3f}")
    for k, v in m["cross_validation"].items():
        print(f"  5-fold  {k:<12} acc={v['accuracy']:.3f} f1={v['f1']:.3f}")
    print(f"saved {MODEL_PATH} ({m['train_seconds']}s)")
    return m


if __name__ == "__main__":
    main()
