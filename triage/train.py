"""Trains the ticket classifier and writes the model and its metrics."""
import argparse
import csv
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

from triage.generate_data import make_dataset


def build_pipeline():
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
            ("clf", LogisticRegression(C=10, max_iter=1000, class_weight="balanced")),
        ]
    )


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r["text"] for r in rows], [r["category"] for r in rows]


def train(output_dir="models", test_csv="data/handwritten_test.csv", n_per_class=120, seed=7):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    train_rows = make_dataset(n_per_class=n_per_class, seed=seed)
    x_train = [t for t, _ in train_rows]
    y_train = [c for _, c in train_rows]
    x_test, y_test = load_csv(test_csv)

    # Cross-validation on synthetic data only measures how well the model learns the templates.
    cv = cross_val_score(build_pipeline(), x_train, y_train, cv=5).mean()

    model = build_pipeline().fit(x_train, y_train)
    pred = model.predict(x_test)
    labels = list(model.classes_)

    metrics = {
        "n_train_synthetic": len(x_train),
        "n_test_handwritten": len(x_test),
        "synthetic_cv_accuracy": round(float(cv), 3),
        "handwritten_accuracy": round(float(accuracy_score(y_test, pred)), 3),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y_test, pred, labels=labels).tolist(),
        "per_class": {
            k: {m: round(float(v), 3) for m, v in vals.items() if m != "support"}
            for k, vals in classification_report(y_test, pred, output_dict=True, zero_division=0).items()
            if k in labels
        },
    }

    joblib.dump(model, out / "model.joblib")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out / "metrics.md").write_text(render_markdown(metrics), encoding="utf-8")
    return metrics


def render_markdown(m):
    lines = [
        "## Ticket classifier results",
        "",
        f"- Training tickets (synthetic): {m['n_train_synthetic']}",
        f"- Test tickets (hand-written): {m['n_test_handwritten']}",
        f"- Cross-validation accuracy on synthetic data: {m['synthetic_cv_accuracy']} (inflated, the data is template-based)",
        f"- **Accuracy on hand-written test tickets: {m['handwritten_accuracy']}**",
        "",
        "| Category | Precision | Recall | F1 |",
        "|---|---|---|---|",
    ]
    for label in m["labels"]:
        c = m["per_class"][label]
        lines.append(f"| {label} | {c['precision']} | {c['recall']} | {c['f1-score']} |")
    lines += ["", "Confusion matrix (rows are true labels, columns are predictions):", "", "```"]
    header = " " * 22 + " ".join(l[:6].rjust(6) for l in m["labels"])
    lines.append(header)
    for label, row in zip(m["labels"], m["confusion_matrix"]):
        lines.append(label.ljust(22) + " ".join(str(v).rjust(6) for v in row))
    lines.append("```")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--test-csv", default="data/handwritten_test.csv")
    args = parser.parse_args()
    result = train(args.output_dir, args.test_csv)
    print(render_markdown(result))
