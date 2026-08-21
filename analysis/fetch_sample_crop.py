"""
Fetch one real, representative tissue crop for an arbitrary GTEx sample from
the GTEx Portal's Deep Zoom Image (DZI) server, by locating real tissue in a
low-res overview (same approach as fetch_slide_tiles.py) and cropping a small
grid of full-resolution tiles around it.

Used to build a real scatter-plus-image-insets figure (age gap vs. chronological
age, per sample, with real crops attached to a few real points) for the hero
visual, in the style of the tissue-clocks paper's own Figure 1i/j.

Usage: python3 analysis/fetch_sample_crop.py SUBJECT_ID SAMPLE_ID OUT_PATH
  e.g. python3 analysis/fetch_sample_crop.py GTEX-1E2YA GTEX-1E2YA-0926 assets/figures/samples/GTEX-1E2YA-0926.png
"""
import math
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

BASE_ROOT = "https://gtexportal.org/openslide/gtexhip"
TILE = 254


def fetch_dzi_dims(subject, sample):
    url = f"{BASE_ROOT}/{subject}/{sample}.dzi"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        xml_text = resp.read()
    ns = {"d": "http://schemas.microsoft.com/deepzoom/2008"}
    root = ET.fromstring(xml_text)
    size = root.find("d:Size", ns)
    return int(size.get("Width")), int(size.get("Height"))


def fetch_tile(subject, sample, level, col, row, retries=3):
    url = f"{BASE_ROOT}/{subject}/{sample}_files/{level}/{col}_{row}.jpeg"
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


def fetch_sample_crop(subject, sample, out_path, crop_size=2):
    full_w, full_h = fetch_dzi_dims(subject, sample)
    max_level = math.ceil(math.log2(max(full_w, full_h)))
    print(f"{sample}: {full_w}x{full_h}px (~{full_w*full_h/1e6:.0f}MP), max level {max_level}")

    def level_dims(level):
        scale = 2 ** (max_level - level)
        return math.ceil(full_w / scale), math.ceil(full_h / scale)

    overview_level = max_level
    for lvl in range(max_level, 0, -1):
        w, h = level_dims(lvl)
        if math.ceil(w / TILE) <= 10:
            overview_level = lvl
            break
    ow, oh = level_dims(overview_level)
    n_cols, n_rows = math.ceil(ow / TILE), math.ceil(oh / TILE)

    overview = Image.new("RGB", (ow, oh), "white")
    for row in range(n_rows):
        for col in range(n_cols):
            tile = fetch_tile(subject, sample, overview_level, col, row)
            if tile is not None:
                overview.paste(tile, (col * TILE, row * TILE))

    ov_arr = np.array(overview.convert("RGB"))
    gray = ov_arr.mean(axis=2)
    tissue_ys, tissue_xs = np.where(gray < 200)
    if len(tissue_xs) == 0:
        print(f"  WARNING: no tissue found in overview for {sample}")
        return False
    med_x, med_y = np.median(tissue_xs), np.median(tissue_ys)
    scale = 2 ** (max_level - overview_level)
    full_x, full_y = med_x * scale, med_y * scale
    center_col, center_row = int(full_x // TILE), int(full_y // TILE)

    crop = Image.new("RGB", (TILE * crop_size, TILE * crop_size), "white")
    half = crop_size // 2
    for dr in range(-half, crop_size - half):
        for dc in range(-half, crop_size - half):
            tile = fetch_tile(subject, sample, max_level, center_col + dc, center_row + dr)
            if tile is not None:
                crop.paste(tile, ((dc + half) * TILE, (dr + half) * TILE))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    crop.save(out_path)
    print(f"  Saved: {out_path}")
    return True


if __name__ == "__main__":
    subject, sample, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    fetch_sample_crop(subject, sample, out_path)
