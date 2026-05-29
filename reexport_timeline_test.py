"""
Re-export deforestation-timeline PNGs from an existing batch CSV without
re-running any Earth Engine queries.  Useful for tweaking layout/scale after
a batch run.

Usage:
    PYTHONPATH=reflex_app .venv/bin/python3 reexport_timeline_test.py [options]

Options:
    --folder PATH   deforestation_timeline/ directory (default: Amanaye batch)
    --scale  N      kaleido render scale  (default 3 → ~300 dpi at 1400 px wide)
    --width  W      PNG width in pixels   (default 1400)

Outputs go to <figures_dir>/v2_*.png alongside the originals.
"""

import argparse
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "reflex_app"))

import pandas as pd


def load_series_from_csv(csv_path: pathlib.Path) -> dict:
    """Wide-format timeline CSV → {indicator: {year: float}} dict."""
    df = pd.read_csv(csv_path)
    return {
        col: {int(r["year"]): float(r[col]) for _, r in df.iterrows()}
        for col in df.columns
        if col != "year"
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-export timeline PNGs from CSV.")
    parser.add_argument(
        "--folder",
        default=(
            "/media/leandromb/iron8/Downloads_ubuntuWD/"
            "yvynation_batch_20260529_0913/territory/Amanaye/deforestation_timeline"
        ),
    )
    parser.add_argument("--scale", type=int, default=3)
    parser.add_argument("--width", type=int, default=1400)
    args = parser.parse_args()

    folder = pathlib.Path(args.folder)
    fig_dir = folder / "figures"
    fig_dir.mkdir(exist_ok=True)

    csv_files = list(folder.glob("*_timeline_*.csv"))
    if not csv_files:
        sys.exit(f"No timeline CSV found in {folder}")

    csv_path = csv_files[0]
    print(f"Loading: {csv_path.name}")
    series = load_series_from_csv(csv_path)
    years = sorted({y for s in series.values() for y in s})
    y_start, y_end = years[0], years[-1]
    territory_name = csv_path.stem.split("_deforestation_")[0].replace("_", " ")
    print(f"  Years: {y_start}–{y_end}   Indicators: {list(series.keys())}")

    try:
        from yvynation.utils.visualization import create_deforestation_timeline_chart
    except ImportError as e:
        sys.exit(f"Could not import visualization: {e}")

    variants = [
        ("raw",         "raw"),
        ("moving_avg",  "ma5"),
        ("derivatives", "derivatives"),
    ]

    for variant, suffix in variants:
        print(f"\nVariant: {variant}")
        fig = create_deforestation_timeline_chart(
            series,
            state_code=None,
            year_start=y_start,
            year_end=y_end,
            variant=variant,
            moving_window=5,
            title_suffix=territory_name,
        )
        if fig is None:
            print("  (skipped — no data)")
            continue

        stem = csv_path.stem.replace(
            f"_{y_start}_{y_end}", f"_{y_start}_{y_end}_{suffix}"
        )
        out_path = fig_dir / f"v2_{pathlib.Path(stem).name}.png"
        fig.write_image(
            str(out_path),
            scale=args.scale,
            width=args.width,
            height=fig.layout.height or 1000,
        )
        print(f"  ✓  {out_path}")

    print("\nDone. Compare v2_*.png files in the figures folder.")


if __name__ == "__main__":
    main()
