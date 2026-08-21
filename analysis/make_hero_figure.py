"""
Real scatter-plus-image-insets hero figure: predicted age gap vs. chronological
age for every real Lung test-set sample, with a few real tissue crops attached
to their actual data points via leader lines, in the style of the tissue-clocks
paper's own Figure 1i/j (age gap vs. chronological age for cerebellum/aorta,
with histology insets).

Crops are fetched separately by fetch_sample_crop.py. Renders both a light-
and dark-mode version, since this is a raster image (not a themed inline SVG
like the rest of the site's charts) and can't re-theme itself in the browser;
index.html swaps between the two files with CSS based on the active theme.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

RANDOM_STATE = 7
BRACKET_MIDPOINT = {"20-29": 25, "30-39": 35, "40-49": 45, "50-59": 55, "60-69": 65, "70-79": 75}

# real crops, matched to real sample IDs, chosen as genuine extremes + one
# near-zero case from the real Lung test-set age-gap distribution
INSETS = [
    "GTEX-1E2YA-0926",
    "GTEX-1MCQQ-0426",
    "GTEX-14DAR-0226",
    "GTEX-139D8-1726",
]

# positioned by hand (adjust these directly to move a tile: figure-fraction
# coordinates, x/y each 0-1, (0,0) = bottom left of the canvas). label_side
# controls which way its text label offsets from the box.
INSET_POSITIONS = {
    "GTEX-139D8-1726": (0.35, 0.8, "above"),   # +30 case, top-left
    "GTEX-14DAR-0226": (0.47, 0.8, "above"),   # +10 case, top-right of that
    "GTEX-1MCQQ-0426": (0.6, 0.7, "below"),    # 0 case
    "GTEX-1E2YA-0926": (0.35, 0.45, "below"),  # -30 case
}

# same tokens as css/style.css, light and dark
THEME = {
    "light": {"ink": "#0b0b0b", "muted": "#898781", "orange": "#eb6834", "aqua": "#1baf7a"},
    "dark":  {"ink": "#ffffff", "muted": "#c3c2b7", "orange": "#d95926", "aqua": "#199e70"},
}

df = pd.read_csv("analysis/test_predictions.csv", index_col=0)
lung = df[df["Tissue"] == "Lung"].copy()
lung["age_mid"] = lung["Age Bracket"].map(BRACKET_MIDPOINT)

rng = np.random.default_rng(RANDOM_STATE)
lung["x_jitter"] = lung["age_mid"] + rng.uniform(-3.2, 3.2, len(lung))
lung["y_jitter"] = lung["age_gap_years"] + rng.uniform(-1.4, 1.4, len(lung))


def render(mode, out_path):
    ink, muted = THEME[mode]["ink"], THEME[mode]["muted"]
    orange, aqua = THEME[mode]["orange"], THEME[mode]["aqua"]

    fig, ax = plt.subplots(figsize=(9.4, 6.4), dpi=160)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # shrink the plot itself so all 4 image insets live in the margins around
    # it, never on top of the axes, its tick labels/title, or the scatter
    AX_LEFT, AX_BOTTOM, AX_W, AX_H = 0.10, 0.32, 0.56, 0.50
    ax.set_position([AX_LEFT, AX_BOTTOM, AX_W, AX_H])

    norm = plt.Normalize(-30, 30)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list(
        "gap", [aqua, "#d9d6ce", orange])

    ax.axhline(0, color=muted, linewidth=1, zorder=1)
    ax.scatter(
        lung["x_jitter"], lung["y_jitter"],
        c=lung["age_gap_years"], cmap=cmap, norm=norm,
        s=26, alpha=0.65, edgecolors="none", zorder=2,
    )

    ax.set_xlim(15, 82)
    ax.set_ylim(-42, 42)
    ax.set_xlabel("Chronological age (bracket midpoint, jittered)", fontsize=10, color=ink)
    ax.set_ylabel("Predicted age gap (years)", fontsize=10, color=ink)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(muted)
    ax.tick_params(colors=muted, labelsize=9)

    ZOOM = 0.11
    IMG_H = (508 * ZOOM / 72) / 6.4  # image height as a fraction of figure height

    annotation_boxes = []
    for sample_id in INSETS:
        row = lung.loc[sample_id]
        img_path = f"assets/figures/samples/{sample_id}.png"
        img = np.array(Image.open(img_path))
        imagebox = OffsetImage(img, zoom=ZOOM)
        imagebox.image.axes = ax
        box_x, box_y, label_side = INSET_POSITIONS[sample_id]
        ab = AnnotationBbox(
            imagebox, (row["x_jitter"], row["y_jitter"]),
            xybox=(box_x, box_y), xycoords="data", boxcoords="figure fraction",
            frameon=True, pad=0.15,
            bboxprops=dict(edgecolor=ink, linewidth=1.1),
            arrowprops=dict(arrowstyle="-", color=ink, linewidth=1, shrinkA=0, shrinkB=6),
            zorder=5,
            annotation_clip=False,
        )
        ax.add_artist(ab)
        annotation_boxes.append(ab)
        gap = row["age_gap_years"]
        label = f"{gap:+.0f} years" if gap != 0 else "0 years"
        if label_side == "above":
            label_y, va = box_y + IMG_H / 2 + 0.010, "bottom"
        else:
            label_y, va = box_y - IMG_H / 2 - 0.010, "top"
        txt = fig.text(box_x, label_y, label, fontsize=8.5, color=ink, fontweight="700", ha="center", va=va)
        annotation_boxes.append(txt)

    # bbox_inches="tight" repeatedly clipped real content here (it doesn't
    # reliably measure AnnotationBbox artists placed outside the axes, even
    # when passed explicitly via bbox_extra_artists), so we don't use it.
    # Save the full canvas, then crop to the actual non-transparent pixel
    # content ourselves -- reliable because it's just reading the rendered
    # PNG, not asking matplotlib to predict its own layout ahead of time.
    raw_path = out_path.replace(".png", "_raw.png")
    plt.savefig(raw_path, dpi=160, transparent=True)
    plt.close(fig)

    raw = Image.open(raw_path)
    alpha = np.array(raw.convert("RGBA"))[:, :, 3]
    rows = np.where(alpha.max(axis=1) > 0)[0]
    cols = np.where(alpha.max(axis=0) > 0)[0]
    PAD = 14  # px, a little breathing room around the true content bounds
    top, bottom = max(rows.min() - PAD, 0), min(rows.max() + PAD, alpha.shape[0])
    left, right = max(cols.min() - PAD, 0), min(cols.max() + PAD, alpha.shape[1])
    raw.crop((left, top, right, bottom)).save(out_path)
    os.remove(raw_path)
    print(f"Saved {out_path} (cropped to real content, {right-left}x{bottom-top}px)")


render("light", "assets/figures/hero_age_gap_scatter.png")
render("dark", "assets/figures/hero_age_gap_scatter_dark.png")
