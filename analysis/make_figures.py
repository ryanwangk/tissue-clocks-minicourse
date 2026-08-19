"""Generate real, data-driven figures for the minicourse site from the
actual analysis results (no mockups)."""

import json
import anndata as ad
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

TEAL = "#0f766e"
CORAL = "#e07856"
NEUTRAL = "#94a3b8"
BRACKET_ORDER = ["20-29", "30-39", "40-49", "50-59", "60-69", "70-79"]

adata = ad.read_h5ad("data/gtex.4_tissues.0.5mpp.224px.conch.h5ad")
obs = adata.obs.copy()

with open("analysis/results.json") as f:
    results = json.load(f)

test_obs = pd.read_csv("analysis/test_predictions.csv", index_col=0)
gap_by_hardy = pd.read_csv("analysis/gap_by_hardy.csv", index_col=0)

# --- Figure 1: Tissue distribution ---
fig, ax = plt.subplots(figsize=(7, 4))
counts = obs["Tissue"].value_counts().sort_values()
ax.barh(counts.index, counts.values, color=TEAL)
ax.set_xlabel("Number of slides")
ax.set_title("GTEx histology slides used (4-tissue CONCH subset)")
for i, v in enumerate(counts.values):
    ax.text(v + 10, i, str(v), va="center", fontsize=9)
plt.tight_layout()
plt.savefig("assets/figures/01_tissue_distribution.png", dpi=150)
plt.close()

# --- Figure 2: Age bracket distribution ---
fig, ax = plt.subplots(figsize=(6, 4))
counts = obs["Age Bracket"].value_counts().reindex(BRACKET_ORDER)
ax.bar(counts.index, counts.values, color=CORAL)
ax.set_ylabel("Number of slides")
ax.set_xlabel("Donor age bracket")
ax.set_title("Age distribution across all 4,791 slides (971 donors)")
plt.tight_layout()
plt.savefig("assets/figures/02_age_distribution.png", dpi=150)
plt.close()

# --- Figure 3: Model MAE vs baseline, per tissue ---
tissues = list(results["per_tissue"].keys())
mae = [results["per_tissue"][t]["mae_years"] for t in tissues]
baseline = [results["per_tissue"][t]["baseline_mae_years"] for t in tissues]
short_names = [t.replace(" - ", "\n").replace(" (", "\n(") for t in tissues]

x = np.arange(len(tissues))
width = 0.35
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(x - width/2, baseline, width, label="Baseline (majority class)", color=NEUTRAL)
ax.bar(x + width/2, mae, width, label="Tissue clock (ours)", color=TEAL)
ax.set_ylabel("Mean absolute error (years)")
ax.set_title("Our tissue clock vs. a naive baseline, per tissue")
ax.set_xticks(x)
ax.set_xticklabels(short_names, fontsize=8)
ax.legend()
plt.tight_layout()
plt.savefig("assets/figures/03_mae_vs_baseline.png", dpi=150)
plt.close()

# --- Figure 4: Confusion matrix (pooled model, from test_predictions.csv) ---
cm = confusion_matrix(
    test_obs["Age Bracket"], test_obs["predicted_bracket"], labels=BRACKET_ORDER
)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
fig, ax = plt.subplots(figsize=(5.5, 5))
im = ax.imshow(cm_norm, cmap="YlGnBu", vmin=0, vmax=1)
ax.set_xticks(range(len(BRACKET_ORDER)))
ax.set_yticks(range(len(BRACKET_ORDER)))
ax.set_xticklabels(BRACKET_ORDER, rotation=45)
ax.set_yticklabels(BRACKET_ORDER)
ax.set_xlabel("Predicted age bracket")
ax.set_ylabel("Actual age bracket")
ax.set_title("Pooled model confusion matrix (row-normalized)")
for i in range(len(BRACKET_ORDER)):
    for j in range(len(BRACKET_ORDER)):
        ax.text(j, i, f"{cm_norm[i,j]:.2f}", ha="center", va="center",
                 color="white" if cm_norm[i, j] > 0.5 else "black", fontsize=8)
plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
plt.tight_layout()
plt.savefig("assets/figures/04_confusion_matrix.png", dpi=150)
plt.close()

# --- Figure 5: Age gap by Hardy Scale ---
hardy_order = ["Fast death - violent", "Fast death - natural causes",
               "Intermediate death", "Slow death", "Ventilator case"]
gap_by_hardy = gap_by_hardy.reindex(hardy_order)
fig, ax = plt.subplots(figsize=(7, 4.5))
colors = [CORAL if m > 0 else TEAL for m in gap_by_hardy["mean"]]
sem = gap_by_hardy["std"] / np.sqrt(gap_by_hardy["count"])
ax.bar(range(len(hardy_order)), gap_by_hardy["mean"], yerr=sem, color=colors, capsize=4)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(range(len(hardy_order)))
ax.set_xticklabels([h.replace(" - ", "\n") for h in hardy_order], fontsize=8)
ax.set_ylabel("Mean predicted age gap (years)")
ax.set_title("Predicted tissue-age gap by cause-of-death classification\n(pooled model, held-out test set, error bars = SEM)")
for i, (m, c, s) in enumerate(zip(gap_by_hardy["mean"], gap_by_hardy["count"], sem)):
    offset = s + 0.6
    y = m + offset if m > 0 else m - offset
    ax.text(i, y, f"n={int(c)}", ha="center", fontsize=8)
ax.set_ylim(gap_by_hardy["mean"].min() - sem.max() - 1.8, gap_by_hardy["mean"].max() + sem.max() + 1.8)
plt.tight_layout()
plt.savefig("assets/figures/05_age_gap_by_hardy.png", dpi=150)
plt.close()

print("Saved 5 figures to assets/figures/")
print(json.dumps({t: results["per_tissue"][t] for t in tissues}, indent=2))
