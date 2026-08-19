"""
Compute per-sample age gaps (predicted - actual, in years, using bracket
midpoints) for the pooled tissue-clock model, and relate them to the real
Hardy Scale (death classification) metadata bundled in the same file.

Hardy Scale categories (GTEx), roughly ordered by how "sudden" the death was:
  Fast death - violent      (accident/trauma, no illness progression)
  Fast death - natural causes
  Intermediate death
  Slow death                 (prolonged illness)
  Ventilator case            (on a ventilator before death - confounds
                              the aging signal with acute critical illness)
"""

import json
import anndata as ad
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupShuffleSplit

RANDOM_STATE = 42
BRACKET_MIDPOINT = {
    "20-29": 25, "30-39": 35, "40-49": 45,
    "50-59": 55, "60-69": 65, "70-79": 75,
}

adata = ad.read_h5ad("data/gtex.4_tissues.0.5mpp.224px.conch.h5ad")
obs = adata.obs.copy()
X_all = adata.X
subjects = obs["Subject ID"].values

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
train_idx, test_idx = next(gss.split(X_all, groups=subjects))

tissue_dummies = pd.get_dummies(obs["Tissue"], prefix="tissue")
X_pooled = np.hstack([X_all, tissue_dummies.values])
X_tr, X_te = X_pooled[train_idx], X_pooled[test_idx]
y_tr = obs.iloc[train_idx]["Age Bracket"].values

clf = HistGradientBoostingClassifier(random_state=RANDOM_STATE, max_iter=300)
clf.fit(X_tr, y_tr)
y_pred = clf.predict(X_te)

test_obs = obs.iloc[test_idx].copy()
test_obs["predicted_bracket"] = y_pred
test_obs["actual_midpoint"] = test_obs["Age Bracket"].astype(str).map(BRACKET_MIDPOINT).astype(float)
test_obs["predicted_midpoint"] = pd.Series(test_obs["predicted_bracket"]).astype(str).map(BRACKET_MIDPOINT).astype(float).values
test_obs["age_gap_years"] = test_obs["predicted_midpoint"] - test_obs["actual_midpoint"]

print("=== Age gap by Hardy Scale (test set, pooled model) ===")
gap_by_hardy = test_obs.groupby("Hardy Scale")["age_gap_years"].agg(["mean", "std", "count"])
print(gap_by_hardy)
print()

print("=== Age gap by Sex ===")
gap_by_sex = test_obs.groupby("Sex")["age_gap_years"].agg(["mean", "std", "count"])
print(gap_by_sex)
print()

print("=== Age gap by Tissue ===")
gap_by_tissue = test_obs.groupby("Tissue")["age_gap_years"].agg(["mean", "std", "count"])
print(gap_by_tissue)
print()

# Save test-set predictions for figure-making
test_obs.to_csv("analysis/test_predictions.csv")
gap_by_hardy.to_csv("analysis/gap_by_hardy.csv")
gap_by_sex.to_csv("analysis/gap_by_sex.csv")
gap_by_tissue.to_csv("analysis/gap_by_tissue.csv")
print("Saved analysis/test_predictions.csv, gap_by_hardy.csv, gap_by_sex.csv, gap_by_tissue.csv")
