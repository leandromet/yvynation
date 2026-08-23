#!/usr/bin/env python3
"""Shrink the per-territory PNGs under a yvynation_report dataset's images/
folder in place, for PDF export size. Safe to run destructively: these PNGs
are byte-identical copies of files that still exist untouched in the source
batch folder (territory/*/maps, mapbiomas/figures, etc.), so nothing here is
actually lost -- worst case, re-copy from the batch and re-run.

Resizes to a max dimension, drops alpha, and quantizes to a 256-colour
adaptive palette (PNG mode 'P') -- these are rendered maps/charts with large
flat-colour regions, not photos, so 256 colours is visually lossless at
report/PDF viewing size while cutting file size by roughly 5-10x.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

MAX_DIM = 1000


def compress_one(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    im = Image.open(path)
    w, h = im.size
    scale = min(1.0, MAX_DIM / max(w, h))
    rgb = im.convert("RGB")
    if scale < 1.0:
        rgb = rgb.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    pal = rgb.convert("P", palette=Image.ADAPTIVE, colors=256)
    pal.save(path, optimize=True)
    return before, path.stat().st_size


def main():
    root = Path(sys.argv[1])
    files = sorted(root.rglob("*.png"))
    print(f"{len(files)} PNGs under {root}")
    total_before = total_after = 0
    for i, f in enumerate(files, 1):
        before, after = compress_one(f)
        total_before += before
        total_after += after
        if i % 50 == 0 or i == len(files):
            print(f"  {i}/{len(files)}  running total {total_before/1e6:.0f}MB -> {total_after/1e6:.0f}MB")
    print(f"Done. {total_before/1e6:.1f}MB -> {total_after/1e6:.1f}MB "
          f"({100 * (1 - total_after / total_before):.0f}% smaller)")


if __name__ == "__main__":
    main()
