"""
Train a small tissue-clock model on real pre-extracted CONCH embeddings
from the tissue-clocks paper's Zenodo archive (record 20709093).

Data: gtex.4_tissues.0.5mpp.224px.conch.h5ad
  - 4,791 slides, 971 unique donors, 6 tissue types
  - X: 512-dim CONCH slide-level embeddings
  - obs: Tissue, Subject ID, Sex, Age Bracket (20-29..70-79), Hardy Scale,
    Pathology Categories, Pathology Notes

This is an ORIGINAL analysis for the MEC minicourse, not a reproduction of
the paper's own modeling choices (paper uses fastai; we use sklearn for a
lighter, fully-reproducible-in-Colab pipeline).
"""

import json
import anndata as ad
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, mean_absolute_error, balanced_accuracy_score

RANDOM_STATE = 42
BRACKET_MIDPOINT = {
    "20-29": 25, "30-39": 35, "40-49": 45,
    "50-59": 55, "60-69": 65, "70-79": 75,
}
BRACKET_ORDER = ["20-29", "30-39", "40-49", "50-59", "60-69", "70-79"]

adata = ad.read_h5ad("data/gtex.4_tissues.0.5mpp.224px.conch.h5ad")
obs = adata.obs.copy()
X_all = adata.X
subjects = obs["Subject ID"].values

# Subject-level split: no donor appears in both train and test, even though
# a donor contributes multiple tissue samples (up to 6 organs each).
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
train_idx, test_idx = next(gss.split(X_all, groups=subjects))

print(f"Total slides: {len(obs)}, unique donors: {obs['Subject ID'].nunique()}")
print(f"Train slides: {len(train_idx)} ({obs.iloc[train_idx]['Subject ID'].nunique()} donors)")
print(f"Test slides:  {len(test_idx)} ({obs.iloc[test_idx]['Subject ID'].nunique()} donors)")
print()

results = {"per_tissue": {}, "pooled": {}}

# --- Per-tissue models ---
for tissue in sorted(obs["Tissue"].unique()):
    tissue_mask = (obs["Tissue"] == tissue).values
    tr_idx = np.intersect1d(train_idx, np.where(tissue_mask)[0])
    te_idx = np.intersect1d(test_idx, np.where(tissue_mask)[0])

    if len(tr_idx) < 20 or len(te_idx) < 5:
        print(f"[{tissue}] skipped: too few samples (train={len(tr_idx)}, test={len(te_idx)})")
        continue

    X_tr, X_te = X_all[tr_idx], X_all[te_idx]
    y_tr = obs.iloc[tr_idx]["Age Bracket"].values
    y_te = obs.iloc[te_idx]["Age Bracket"].values

    clf = HistGradientBoostingClassifier(random_state=RANDOM_STATE, max_iter=200)
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)

    acc = accuracy_score(y_te, y_pred)
    bal_acc = balanced_accuracy_score(y_te, y_pred)
    mae_years = mean_absolute_error(
        [BRACKET_MIDPOINT[b] for b in y_te],
        [BRACKET_MIDPOINT[b] for b in y_pred],
    )
    # naive baseline: always predict the most common training bracket
    majority_bracket = pd.Series(y_tr).mode()[0]
    baseline_mae = mean_absolute_error(
        [BRACKET_MIDPOINT[b] for b in y_te],
        [BRACKET_MIDPOINT[majority_bracket]] * len(y_te),
    )

    results["per_tissue"][tissue] = {
        "n_train": int(len(tr_idx)),
        "n_test": int(len(te_idx)),
        "accuracy": round(float(acc), 4),
        "balanced_accuracy": round(float(bal_acc), 4),
        "mae_years": round(float(mae_years), 2),
        "baseline_mae_years": round(float(baseline_mae), 2),
        "majority_bracket": majority_bracket,
    }
    print(f"[{tissue}] n_train={len(tr_idx)} n_test={len(te_idx)} "
          f"acc={acc:.3f} bal_acc={bal_acc:.3f} MAE={mae_years:.2f}yr "
          f"(baseline MAE={baseline_mae:.2f}yr)")

# --- Pooled model (all tissues, tissue as a one-hot feature) ---
print()
tissue_dummies = pd.get_dummies(obs["Tissue"], prefix="tissue")
X_pooled = np.hstack([X_all, tissue_dummies.values])
X_tr, X_te = X_pooled[train_idx], X_pooled[test_idx]
y_tr = obs.iloc[train_idx]["Age Bracket"].values
y_te = obs.iloc[test_idx]["Age Bracket"].values

clf = HistGradientBoostingClassifier(random_state=RANDOM_STATE, max_iter=300)
clf.fit(X_tr, y_tr)
y_pred = clf.predict(X_te)

acc = accuracy_score(y_te, y_pred)
bal_acc = balanced_accuracy_score(y_te, y_pred)
mae_years = mean_absolute_error(
    [BRACKET_MIDPOINT[b] for b in y_te],
    [BRACKET_MIDPOINT[b] for b in y_pred],
)
majority_bracket = pd.Series(y_tr).mode()[0]
baseline_mae = mean_absolute_error(
    [BRACKET_MIDPOINT[b] for b in y_te],
    [BRACKET_MIDPOINT[majority_bracket]] * len(y_te),
)
results["pooled"] = {
    "n_train": int(len(train_idx)),
    "n_test": int(len(test_idx)),
    "accuracy": round(float(acc), 4),
    "balanced_accuracy": round(float(bal_acc), 4),
    "mae_years": round(float(mae_years), 2),
    "baseline_mae_years": round(float(baseline_mae), 2),
    "majority_bracket": majority_bracket,
}
print(f"[POOLED, all tissues] n_train={len(train_idx)} n_test={len(test_idx)} "
      f"acc={acc:.3f} bal_acc={bal_acc:.3f} MAE={mae_years:.2f}yr "
      f"(baseline MAE={baseline_mae:.2f}yr)")

with open("analysis/results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved results to analysis/results.json")
