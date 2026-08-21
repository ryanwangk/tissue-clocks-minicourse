"""
v3 of the Background-section body diagram: uses a real, public-domain,
illustrated (not photographic) anatomical diagram -- Mikael Haggstrom, CC0,
"Adult male with organs.png" via Wikimedia Commons -- a flat skin-tone
silhouette with real illustrated organs (brain cross-section, lungs/heart,
liver/gallbladder/pancreas, intestines) layered in, plus muscular/vascular
detail on the arms. No photographic face, unlike v2 (which the user found
unsettling) -- and unlike v1, the organs themselves are real illustrations,
not separate icons.

The source PNG is already tightly cropped to the figure (alpha bbox
x:17-2506, y:38-3622 out of a 2543x3623 canvas), so this version only needs
a modest crop to focus on the head+torso (where all 4 real landmarks are)
and drop the lower arms, not the elaborate label-avoidance clipping v2
needed.
"""

# Same real GTEX-1E2YA donor / age gaps as v1 and v2
ORGANS = [
    dict(name="Brain", gap=10, xy=(1208, 260)),
    dict(name="Lung", gap=-30, xy=(860, 1920)),
    dict(name="Colon", gap=0, xy=(1550, 3300)),
    dict(name="Skin", gap=-10, xy=(1610, 1290)),
]

IMG_PATH = "assets/figures/organs/adult_male_with_organs.png"
SRC_W, SRC_H = 2543, 3623

# full image (real alpha-channel content bounds of the source PNG -- x:17-2506,
# y:38-3622 out of a 2543x3623 canvas -- i.e. not cropped, just trimmed of the
# few fully-transparent edge pixels)
CROP_X, CROP_Y, CROP_W, CROP_H = 17, 38, 2489, 3584

LABELS = {
    "Brain": (CROP_X - 20, CROP_Y + 80, "left"),
    "Skin": (CROP_X + CROP_W + 40, CROP_Y + 300, "right"),
    "Lung": (CROP_X - 20, CROP_Y + 1500, "left"),
    "Colon": (CROP_X + CROP_W + 40, CROP_Y + 3050, "right"),
}

VIEW_PAD_L, VIEW_PAD_R = 300, 300

parts = []
parts.append(f'<image href="{IMG_PATH}" x="0" y="0" width="{SRC_W}" height="{SRC_H}"/>')

for o in ORGANS:
    bx, by = o["xy"]
    lx, ly, side = LABELS[o["name"]]
    gap = o["gap"]
    color_var = "var(--accent-orange)" if gap > 0 else ("var(--accent-aqua)" if gap < 0 else "var(--text-primary)")
    sign = f"{gap:+.0f}" if gap != 0 else "0"
    text_anchor = "end" if side == "left" else "start"

    parts.append(f'<line x1="{bx}" y1="{by}" x2="{lx}" y2="{ly}" stroke="{color_var}" stroke-width="4" stroke-dasharray="10 8"/>')
    parts.append(f'<circle cx="{bx}" cy="{by}" r="14" style="fill:{color_var};stroke:white;stroke-width:4"/>')
    parts.append(f'<text x="{lx}" y="{ly - 14}" text-anchor="{text_anchor}" font-size="64" font-weight="700" style="fill:var(--text-primary)">{o["name"]}</text>')
    parts.append(f'<text x="{lx}" y="{ly + 58}" text-anchor="{text_anchor}" font-size="64" font-weight="700" style="fill:{color_var}">{sign} yr</text>')

inner_svg = "\n    ".join(parts)

view_x = CROP_X - VIEW_PAD_L
view_w = CROP_W + VIEW_PAD_L + VIEW_PAD_R
svg_full = f'''<svg viewBox="{view_x} {CROP_Y} {view_w} {CROP_H}" role="img" aria-label="Real illustrated anatomical diagram (Mikael Haggstrom, public domain) with real donor GTEX-1E2YA's per-organ age gaps marked: brain +10 years, lung -30 years, colon 0 years, skin -10 years">
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
