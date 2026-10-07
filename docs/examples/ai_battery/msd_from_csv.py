"""Multi-time-origin tracer MSD from a fixed-cell, pre-unwrapped CSV.

Input columns: time_ps, atom_id, x_A, y_A, z_A. No PBC unwrapping is done.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def load_rows(path: Path):
    required = {"time_ps", "atom_id", "x_A", "y_A", "z_A"}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
    frames = defaultdict(dict)
    for row in rows:
        time = float(row["time_ps"])
        if not math.isfinite(time) or time < 0:
            raise ValueError("time_ps values must be finite and non-negative")
        atom = row["atom_id"]
        if atom in frames[time]:
            raise ValueError(f"duplicate atom_id {atom!r} at time {time}")
        coords = tuple(float(row[k]) for k in ("x_A", "y_A", "z_A"))
        if any(not math.isfinite(value) for value in coords):
            raise ValueError("coordinates must be finite")
        frames[time][atom] = coords
    times = sorted(frames)
    if len(times) < 2:
        raise ValueError("at least two time frames are required")
    atom_ids = set(frames[times[0]])
    if any(set(frames[t]) != atom_ids for t in times[1:]):
        raise ValueError("every frame must contain the same atom IDs")
    dts = [b - a for a, b in zip(times, times[1:])]
    dt = dts[0]
    if dt <= 0 or any(not math.isclose(value, dt, rel_tol=1e-7, abs_tol=1e-10) for value in dts):
        raise ValueError("time_ps values must be strictly increasing and uniformly spaced")
    return times, frames, sorted(atom_ids), dt


def calculate(times, frames, atom_ids, center: str):
    origins = []
    for lag in range(1, len(times)):
        values = []
        for origin in range(len(times) - lag):
            displacements = []
            for atom in atom_ids:
                start = frames[times[origin]][atom]
                end = frames[times[origin + lag]][atom]
                displacements.append(tuple(end[i] - start[i] for i in range(3)))
            if center == "subtract-mean":
                means = tuple(sum(item[i] for item in displacements) / len(displacements) for i in range(3))
                displacements = [tuple(item[i] - means[i] for i in range(3)) for item in displacements]
            values.extend(sum(component * component for component in item) for item in displacements)
        origins.append({"lag": lag, "time_ps": times[lag] - times[0], "msd_A2": sum(values) / len(values), "samples": len(values)})
    return origins


def fit_window(points, start: float, end: float):
    selected = [(point["time_ps"], point["msd_A2"]) for point in points if start <= point["time_ps"] <= end]
    if len(selected) < 3:
        raise ValueError("fit window must contain at least three MSD points")
    mean_x = sum(x for x, _ in selected) / len(selected)
    mean_y = sum(y for _, y in selected) / len(selected)
    denom = sum((x - mean_x) ** 2 for x, _ in selected)
    if denom == 0:
        raise ValueError("fit window has zero time span")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in selected) / denom
    intercept = mean_y - slope * mean_x
    residual = sum((y - (slope * x + intercept)) ** 2 for x, y in selected)
    total = sum((y - mean_y) ** 2 for _, y in selected)
    r_squared = 1.0 - residual / total if total else 1.0
    return {"start_ps": start, "end_ps": end, "points": len(selected), "slope_A2_per_ps": slope,
            "intercept_A2": intercept, "residual_sum_A4": residual, "r_squared": r_squared,
            "diffusive_regime_verified": False, "candidate_D_cm2_per_s": slope / 6.0 * 1e-4 if slope >= 0 else None,
            "interpretation": "A linear fit alone cannot establish a diffusive regime. Check lag-window dependence, equilibration, finite-size effects, independent trajectories and uncertainty before interpreting candidate_D."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("msd.json"))
    parser.add_argument("--center", choices=("none", "subtract-mean"), default="none", help="none is tracer default; subtract-mean removes mean motion of SELECTED atoms, not whole-system mass-weighted COM")
    parser.add_argument("--fit-start-ps", type=float, default=0.0)
    parser.add_argument("--fit-end-ps", type=float)
    args = parser.parse_args()
    times, frames, atom_ids, dt = load_rows(args.csv)
    points = calculate(times, frames, atom_ids, args.center)
    fit_end = args.fit_end_ps if args.fit_end_ps is not None else points[-1]["time_ps"]
    result = {"input": str(args.csv.resolve()), "dt_ps": dt, "atom_count": len(atom_ids), "center": args.center,
              "points": points, "fit": fit_window(points, args.fit_start_ps, fit_end),
              "note": "Fixed-cell pre-unwrapped selected-atom MSD only. The inferred D is provisional; no conductivity or correlation correction is applied. Subtracting selected-ion mean motion alters transport statistics and is not a substitute for removing whole-system drift."}
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["fit"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
