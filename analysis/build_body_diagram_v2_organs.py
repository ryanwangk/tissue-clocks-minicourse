"""
v2 of the Background-section body diagram: uses a real, public-domain
anatomical illustration (Mikael Häggström, CC0, via Wikimedia Commons,
"Male template with organs.svg") that already draws the organs themselves
inside the body, so unlike v1 (a flat silhouette + separate organ icons)
this version needs no icons at all -- just leader lines and text pointing
at organs that are already visibly drawn in the source image.

The source file is a 1363x1211 template with its own placeholder
"Header" / "- Example text" callouts; those are cropped away (not edited
out of the source, since it's referenced live via <image> rather than
inlined) by choosing an outer viewBox that shows only the central body
column, clear of all the original text (measured directly via
getBBox() on the live DOM: left-column text's rightmost edge is x=477,
right-column text's leftmost edge is x=824, header bottom is y=122).
"""

# Same real GTEX-1E2YA donor / age gaps as v1
ORGANS = [
    dict(name="Brain", gap=10, xy=(588, 180)),
    dict(name="Lung", gap=-30, xy=(665, 497)),
    dict(name="Colon", gap=0, xy=(588, 1002)),
    dict(name="Skin", gap=-10, xy=(790, 680)),
]

CROP_X, CROP_Y, CROP_W, CROP_H = 477, 122, 347, 928
SRC_W, SRC_H = 1363, 1211
IMG_PATH = "assets/figures/organs/male_template_with_organs_clean.svg"

# label positions: alternate left/right of the crop, spread down its height
LABELS = {
    "Brain": (CROP_X - 150, CROP_Y + 40, "left"),
    "Lung": (CROP_X + CROP_W + 20, CROP_Y + 460, "right"),
    "Colon": (CROP_X - 150, CROP_Y + 780, "left"),
    "Skin": (CROP_X + CROP_W + 20, CROP_Y + 330, "right"),
}

VIEW_PAD_L, VIEW_PAD_R = 190, 190

parts = []
parts.append(f'<clipPath id="bodyCrop"><rect x="{CROP_X}" y="{CROP_Y}" width="{CROP_W}" height="{CROP_H}"/></clipPath>')
parts.append(f'<image href="{IMG_PATH}" x="0" y="0" width="{SRC_W}" height="{SRC_H}" clip-path="url(#bodyCrop)"/>')

for o in ORGANS:
    bx, by = o["xy"]
    lx, ly, side = LABELS[o["name"]]
    gap = o["gap"]
    color_var = "var(--accent-orange)" if gap > 0 else ("var(--accent-aqua)" if gap < 0 else "var(--text-muted)")
    sign = f"{gap:+.0f}" if gap != 0 else "0"
    text_anchor = "end" if side == "left" else "start"
    label_x = lx if side == "left" else lx

    parts.append(f'<line x1="{bx}" y1="{by}" x2="{lx}" y2="{ly}" stroke="{color_var}" stroke-width="2" stroke-dasharray="4 3"/>')
    parts.append(f'<circle cx="{bx}" cy="{by}" r="6" style="fill:{color_var};stroke:white;stroke-width:1.5"/>')
    parts.append(f'<text x="{label_x}" y="{ly - 6}" text-anchor="{text_anchor}" font-size="20" font-weight="700" style="fill:var(--text-primary)">{o["name"]}</text>')
    parts.append(f'<text x="{label_x}" y="{ly + 20}" text-anchor="{text_anchor}" font-size="20" font-weight="700" style="fill:{color_var}">{sign} yr</text>')

inner_svg = "\n    ".join(parts)

view_x = CROP_X - VIEW_PAD_L
view_w = CROP_W + VIEW_PAD_L + VIEW_PAD_R
svg_full = f'''<svg viewBox="{view_x} {CROP_Y} {view_w} {CROP_H}" role="img" aria-label="Real anatomical diagram (Mikael Haggstrom, public domain) with real donor GTEX-1E2YA's per-organ age gaps marked: brain +10 years, lung -30 years, colon 0 years, skin -10 years">
    {inner_svg}
  </svg>'''

with open("assets/figures/organs/body_diagram.svg.inc", "w") as f:
    f.write(svg_full)

preview = f'''<!doctype html><html><head><style>
  body {{ background:#f7f6f2; padding:30px; }}
  :root {{ --text-primary:#0b0b0b; --text-muted:#898781; --accent-orange:#eb6834; --accent-aqua:#1baf7a; }}
  svg {{ width: 640px; border: 1px solid #ddd; }}
</style></head><body>
{svg_full}
</body></html>'''
with open("body_diagram_preview.html", "w") as f:
    f.write(preview)

print(f"Saved. viewBox={view_x} {CROP_Y} {view_w} {CROP_H}")
