"""
Fetch real tiles from the GTEx Portal's Deep Zoom Image (DZI) server for one
real slide (GTEX-1117F-1026, Lung), to visualize what a gigapixel whole-slide
image actually looks like: a low-res overview + real full-resolution crops.

DZI pyramid: level L has tiles covering a downsampled image of size
  ceil(width / 2^(max_level - L)) x ceil(height / 2^(max_level - L))
Tile size 254px (+1px overlap on each side per the .dzi descriptor).
"""
import math
import os
import time
import urllib.request
from PIL import Image

BASE = "https://gtexportal.org/openslide/gtexhip/GTEX-1117F/GTEX-1117F-1026_files"
FULL_W, FULL_H = 41831, 20575
TILE = 254
OVERLAP = 1
OUT_DIR = "assets/figures/slide_tiles"
os.makedirs(OUT_DIR, exist_ok=True)

MAX_LEVEL = math.ceil(math.log2(max(FULL_W, FULL_H)))
print(f"Full slide: {FULL_W} x {FULL_H} px (~{FULL_W*FULL_H/1e6:.0f} megapixels)")
print(f"Max DZI level: {MAX_LEVEL}")


def level_dims(level):
    scale = 2 ** (MAX_LEVEL - level)
    return math.ceil(FULL_W / scale), math.ceil(FULL_H / scale)


def fetch_tile(level, col, row, retries=3):
    url = f"{BASE}/{level}/{col}_{row}.jpeg"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return Image.open(resp).convert("RGB")
        except Exception as e:
            if attempt == retries - 1:
                print(f"  FAILED {url}: {e}")
                return None
            time.sleep(1)


# --- 1. Low-res overview: pick a level where the whole slide is a
#        manageable handful of tiles (aim for ~6-10 tiles wide) ---
overview_level = MAX_LEVEL
for lvl in range(MAX_LEVEL, 0, -1):
    w, h = level_dims(lvl)
    n_tiles_w = math.ceil(w / TILE)
    if n_tiles_w <= 10:
        overview_level = lvl
        break

ow, oh = level_dims(overview_level)
n_cols = math.ceil(ow / TILE)
n_rows = math.ceil(oh / TILE)
print(f"\nOverview level {overview_level}: {ow}x{oh}px, {n_cols}x{n_rows} tiles")

overview = Image.new("RGB", (ow, oh), "white")
for row in range(n_rows):
    for col in range(n_cols):
        tile = fetch_tile(overview_level, col, row)
        if tile is not None:
            overview.paste(tile, (col * TILE, row * TILE))
overview.save(f"{OUT_DIR}/overview_level{overview_level}.png")
print(f"Saved overview: {OUT_DIR}/overview_level{overview_level}.png ({ow}x{oh})")

# --- 2. Full-resolution crop: grab a small grid of tiles at MAX_LEVEL
#        from roughly the center of the slide, where tissue is likely present ---
fw, fh = level_dims(MAX_LEVEL)

# Locate real tissue by analyzing the overview image (already fetched above)
# rather than guessing: find non-white pixels, take the median position of
# the largest blob, and scale up to full-resolution tile coordinates.
import numpy as np
ov_arr = np.array(overview.convert("RGB"))
gray = ov_arr.mean(axis=2)
tissue_ys, tissue_xs = np.where(gray < 200)
# use the leftmost blob (x < half width) as our detail crop location
left_mask = tissue_xs < (ow / 2)
med_x, med_y = np.median(tissue_xs[left_mask]), np.median(tissue_ys[left_mask])
scale = 2 ** (MAX_LEVEL - overview_level)
full_x, full_y = med_x * scale, med_y * scale
center_col, center_row = int(full_x // TILE), int(full_y // TILE)
print(f"\nReal tissue located via overview: level{overview_level} px ({med_x:.0f},{med_y:.0f}) "
      f"-> level{MAX_LEVEL} tile ({center_col},{center_row})")

crop_size = 3
full_res = Image.new("RGB", (TILE * crop_size, TILE * crop_size), "white")
for dr in range(-1, 2):
    for dc in range(-1, 2):
        tile = fetch_tile(MAX_LEVEL, center_col + dc, center_row + dr)
        if tile is not None:
            full_res.paste(tile, ((dc + 1) * TILE, (dr + 1) * TILE))
full_res.save(f"{OUT_DIR}/fullres_crop_level{MAX_LEVEL}.png")
print(f"Saved full-res crop: {OUT_DIR}/fullres_crop_level{MAX_LEVEL}.png")

# --- 3. One single 224x224-ish tile for the "this is one tile" visual ---
single = fetch_tile(MAX_LEVEL, center_col, center_row)
if single is not None:
    single.save(f"{OUT_DIR}/single_tile_level{MAX_LEVEL}.png")
    print(f"Saved single tile: {OUT_DIR}/single_tile_level{MAX_LEVEL}.png")

print("\nDone.")
