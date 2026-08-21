"""
Assembles the real-donor body diagram (Background section) as inline SVG:
a real, public-domain body silhouette (Wikimedia Commons, Mikael Häggström)
with leader lines to real organ icons (lungs/colon: healthicons.org CC0;
brain: hand-drawn to match their flat style) labeled with GTEX-1E2YA's real
per-organ age gaps (the same donor used in the hero figure).

Writes body_diagram.svg.inc (just the inner <g>...</g> markup, to paste into
index.html) plus a standalone preview.html for visual iteration in the browser.
"""
import re

ORGANS_DIR = "assets/figures/organs"


def extract_body_path(svg_text):
    g_transform = re.search(r'<g\s+[^>]*transform="([^"]*)"', svg_text).group(1)
    m = re.search(r'<path\s+style="([^"]*)"\s+d="([^"]*)"', svg_text)
    style, d = m.group(1), m.group(2)
    return g_transform, style, d


def extract_icon_paths(svg_text):
    # returns list of (tag_attrs_str,) for each <path .../> in a 0..48 viewBox icon
    return re.findall(r'<path[^>]*/>', svg_text)


with open(f"{ORGANS_DIR}/body_silhouette.svg") as f:
    body_g_transform, body_style, body_d = extract_body_path(f.read())

with open(f"{ORGANS_DIR}/lungs.svg") as f:
    lungs_paths = extract_icon_paths(f.read())
with open(f"{ORGANS_DIR}/colon.svg") as f:
    colon_paths = extract_icon_paths(f.read())
with open(f"{ORGANS_DIR}/brain.svg") as f:
    brain_paths = extract_icon_paths(f.read())

# ---- layout ----
BODY_SCALE = 0.155
BODY_TX, BODY_TY = 300, 30   # top-left of the body's own 970x2200 box, post-scale

ICON_SIZE = 34  # rendered icon box, in diagram units


def icon_group(paths, x, y, color):
    inner = "\n      ".join(paths)
    s = ICON_SIZE / 48
    return f'''<g transform="translate({x},{y}) scale({s})" style="color:{color}">
      {inner}
    </g>'''


# GTEX-1E2YA, age bracket 50-59 (real test-set donor, also used in the hero
# figure's -30 lung inset): real per-organ age gaps from test_predictions.csv
ORGANS = [
    dict(name="Brain", gap=10, icon="brain", side="right",
         body_xy=(375.5, 53), label_xy=(520, 15)),
    dict(name="Lung", gap=-30, icon="lungs", side="right",
         body_xy=(376, 138), label_xy=(560, 128)),
    dict(name="Colon", gap=0, icon="colon", side="left",
         body_xy=(376, 193), label_xy=(150, 200)),
    dict(name="Skin", gap=-10, icon="skin", side="left",
         body_xy=(335, 162), label_xy=(150, 60)),
]

ICON_LOOKUP = {"lungs": lungs_paths, "colon": colon_paths, "brain": brain_paths}

parts = []
parts.append(f'<g transform="translate({BODY_TX},{BODY_TY}) scale({BODY_SCALE})">'
             f'<g transform="{body_g_transform}"><path style="{body_style}" d="{body_d}"/></g></g>')

for o in ORGANS:
    bx, by = o["body_xy"]
    lx, ly = o["label_xy"]
    gap = o["gap"]
    older = gap > 0
    color_var = "var(--accent-orange)" if older else ("var(--accent-aqua)" if gap < 0 else "var(--text-muted)")
    sign = f"{gap:+.0f}" if gap != 0 else "0"

    # leader line from body point to icon anchor
    icon_x = lx if o["side"] == "right" else lx + 40
    icon_y = ly
    parts.append(f'<line x1="{bx}" y1="{by}" x2="{icon_x + ICON_SIZE/2}" y2="{icon_y + ICON_SIZE/2}" '
                 f'stroke="{color_var}" stroke-width="1.5" stroke-dasharray="3 3"/>')
    parts.append(f'<circle cx="{bx}" cy="{by}" r="3.5" style="fill:{color_var}"/>')

    if o["icon"] != "skin":
        parts.append(icon_group(ICON_LOOKUP[o["icon"]], icon_x, icon_y, color_var))
    else:
        # skin has no separate organ icon: mark the surface point itself
        parts.append(f'<circle cx="{icon_x + ICON_SIZE/2}" cy="{icon_y + ICON_SIZE/2}" r="{ICON_SIZE/2 - 4}" '
                     f'style="fill:none;stroke:{color_var};stroke-width:2"/>')

    text_x = icon_x + ICON_SIZE/2
    text_anchor = "middle"
    label_below_y = icon_y + ICON_SIZE + 16
    parts.append(f'<text x="{text_x}" y="{label_below_y}" text-anchor="{text_anchor}" '
                 f'font-size="12" font-weight="700" style="fill:var(--text-primary)">{o["name"]}</text>')
    parts.append(f'<text x="{text_x}" y="{label_below_y + 15}" text-anchor="{text_anchor}" '
                 f'font-size="12" font-weight="700" style="fill:{color_var}">{sign} yr</text>')

inner_svg = "\n    ".join(parts)

svg_full = f'''<svg viewBox="0 0 680 385" role="img" aria-label="Diagram: for real donor GTEX-1E2YA (age bracket 50 to 59), skin and lung read biologically younger than chronological age, brain reads older, colon reads about the same">
    {inner_svg}
  </svg>'''

with open("assets/figures/organs/body_diagram.svg.inc", "w") as f:
    f.write(svg_full)

preview = f'''<!doctype html><html><head><style>
  body {{ background:#f7f6f2; padding:30px; }}
  :root {{ --text-primary:#0b0b0b; --text-muted:#898781; --accent-orange:#eb6834; --accent-aqua:#1baf7a; }}
  svg {{ width: 680px; border: 1px solid #ddd; }}
</style></head><body>
{svg_full}
</body></html>'''
with open("body_diagram_preview.html", "w") as f:
    f.write(preview)

print("Wrote assets/figures/organs/body_diagram.svg.inc and body_diagram_preview.html")
