# Tissue Clocks: a hands-on minicourse

[![Course site](https://img.shields.io/badge/course%20site-live-brightgreen)](https://ryanwangk.github.io/tissue-clocks-minicourse/)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ryanwangk/tissue-clocks-minicourse/blob/main/notebooks/tissue_clock_handson.ipynb)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)

A MICCAI Educational Challenge (MEC) 2026 minicourse on **tissue clocks**: deep-learning
predictors of biological age from histology images, built on the real, pre-extracted
CONCH slide embeddings released alongside Abila, Buljan, Zheng et al., Rendeiro, A. F.,
["Histological aging signatures for monitoring tissue-specific aging and disease,"](https://doi.org/10.1038/s41591-026-04566-5)
*Nature Medicine* (2026).

- **Course site:** https://ryanwangk.github.io/tissue-clocks-minicourse/
- **Hands-on notebook:** [Open in Colab](https://colab.research.google.com/github/ryanwangk/tissue-clocks-minicourse/blob/main/notebooks/tissue_clock_handson.ipynb)
- **Paper:** [doi:10.1038/s41591-026-04566-5](https://doi.org/10.1038/s41591-026-04566-5)
- **Embeddings:** [Zenodo 10.5281/zenodo.20709093](https://doi.org/10.5281/zenodo.20709093)


## Contents

The course builds a small, real tissue clock end to end: donor-level train/test split,
one `HistGradientBoostingClassifier` per tissue plus a pooled model, evaluated against
a naive baseline and cross-checked against Hardy Scale (cause-of-death) metadata the
model never saw. Five of six tissues clearly beat baseline; the one that doesn't
(Brain-Cortex) is reported honestly, including that its razor-thin margin has already
flipped between two independent runs of this same pipeline.

## Repository structure

```
.
├── index.html              # the course site itself (single page)
├── css/style.css           # design system: theming, layout, chart chrome
├── js/main.js               # site interactivity + all chart rendering (real data, no mocks)
│
├── notebooks/
│   └── tissue_clock_handson.ipynb   # fully worked, Colab-ready reproduction of the whole pipeline
│
├── analysis/                # the scripts that actually produced every number on the site
│   ├── train_tissue_clock.py        # donor-level split; per-tissue + pooled model training
│   ├── age_gap_analysis.py          # predicted age gap vs. Hardy Scale / Sex / Tissue
│   ├── make_figures.py              # renders the 5 static PNGs used as reference figures
│   ├── fetch_slide_tiles.py         # pulls real WSI tiles from GTEx Portal's Deep Zoom server
│   ├── results.json                 # per-tissue + pooled accuracy, MAE, baseline MAE
│   ├── test_predictions.csv         # per-slide predictions on the held-out test set
│   └── gap_by_*.csv                 # age-gap summaries used by the site's charts
│
├── assets/figures/          # static PNGs (distribution plots, MAE chart, confusion matrix,
│   └── slide_tiles/         #   age-gap-by-Hardy-Scale, and real WSI overview/crop images)
│
└── data/
    └── gtex.4_tissues.0.5mpp.224px.conch.h5ad   # the real embeddings (10.6 MB, see Data below)
```

## Data

The core dataset is `gtex.4_tissues.0.5mpp.224px.conch.h5ad`: 512-dimensional CONCH
slide-level embeddings for 4,791 histology slides from 971 GTEx donors across 6 tissue
types, openly archived on Zenodo by the tissue-clocks paper's own authors
([10.5281/zenodo.20709093](https://doi.org/10.5281/zenodo.20709093), no login required).

```python
import anndata as ad
adata = ad.read_h5ad("data/gtex.4_tissues.0.5mpp.224px.conch.h5ad")
# adata.X    -> 512-dim CONCH embeddings
# adata.obs  -> Tissue, Subject ID, Sex, Age Bracket, Hardy Scale, Pathology Categories/Notes
```

No GPU or CONCH inference is needed anywhere in this repo: the embeddings are already
extracted. See Section 04 of the course site for why that step is skipped, and what it
would take to run it yourself.

## Reproducing the results

**Easiest path:** open [`notebooks/tissue_clock_handson.ipynb`](notebooks/tissue_clock_handson.ipynb)
in Colab (badge/link above). It fetches the embeddings itself and reproduces every
number and figure on the site in a couple of minutes on a free CPU runtime.

**Locally**, from the repo root, with `data/gtex.4_tissues.0.5mpp.224px.conch.h5ad`
already present:

```bash
pip install anndata pandas numpy scikit-learn matplotlib

python analysis/train_tissue_clock.py      # trains all models, writes results.json
python analysis/age_gap_analysis.py        # writes test_predictions.csv, gap_by_*.csv
python analysis/make_figures.py            # regenerates the 5 PNGs in assets/figures/
```

`train_tissue_clock.py` and `age_gap_analysis.py` both use a fixed `random_state=42`
for the donor-level split, so the split itself is fully reproducible. The trained
models' exact predictions can vary by a few hundredths of a year across machines
(`HistGradientBoostingClassifier` isn't bit-reproducible across platforms), which is
exactly the caveat called out on the site next to the Brain-Cortex result.

## Previewing the site locally

No build step; it's plain HTML/CSS/JS.

```bash
python3 -m http.server 8765
# then open http://localhost:8765/index.html
```

## License and attribution

This repository's own content (site, notebook, analysis scripts) is licensed under
[**CC BY-NC 4.0**](LICENSE), chosen to match the restrictions already carried by what
it's built on:

- The CONCH embeddings (`data/gtex.4_tissues.0.5mpp.224px.conch.h5ad`) are archived on
  Zenodo ([10.5281/zenodo.20709093](https://doi.org/10.5281/zenodo.20709093)) under
  CC BY-NC 4.0.
- CONCH's own license (Lu, M. Y. et al., ["A visual-language foundation model for
  computational pathology,"](https://github.com/mahmoodlab/CONCH) *Nat. Med.* 2024,
  Mahmood Lab) extends its noncommercial restriction to "datasets created from the
  CONCH model" and "models trained on outputs from the CONCH model," which covers the
  embeddings file and the classifiers trained on it here.
- The tissue-clocks paper's own code (referenced, not vendored, here) is
  [PolyForm Noncommercial 1.0.0](https://github.com/rendeirolab/tissue-clocks).
- [GTEx's](https://gtexportal.org/home/license) own data license is more permissive
  (attribution required, no noncommercial restriction) and isn't the limiting factor.

See [LICENSE](LICENSE) for the full reasoning, and the course site's footer for the
complete citation list.

## Authors

Ryan Khalloqi¹, Jun Ma²
¹Department of Electrical and Computer Engineering, Carnegie Mellon University
²Princess Margaret Cancer Centre & AI Hub, University Health Network

## AI-assistance disclosure

This site, notebook, and analysis code were drafted with Claude Code assistance. All
analysis, figures, and results were independently computed and verified by the
authors; see [analysis/](analysis/) and [notebooks/tissue_clock_handson.ipynb](notebooks/tissue_clock_handson.ipynb)
for the exact, runnable pipeline behind every number in this repository.
