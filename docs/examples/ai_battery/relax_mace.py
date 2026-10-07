"""Small ASE/MACE relaxation example with explicit provenance.

MACE and ASE are imported lazily so ``--help`` and repository tests do not
require the optional scientific stack or download a checkpoint.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import math
import platform
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Relax a CIF with an official MACE pretrained calculator.")
    parser.add_argument("input_cif", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("mace_relax_out"))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--model", default="small", help="MACE foundation-model name supported by installed mace-torch.")
    parser.add_argument("--fmax", type=float, default=0.05, help="ASE stopping tolerance in eV/Angstrom (not a convergence guarantee).")
    parser.add_argument("--steps", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input_cif.exists():
        raise SystemExit(f"input CIF not found: {args.input_cif}")
    if args.fmax <= 0 or args.steps < 1:
        raise SystemExit("--fmax must be positive and --steps must be at least 1")

    try:
        from ase.io import read, write
        from ase.optimize import BFGS
        from mace.calculators import mace_mp
    except ImportError as exc:
        raise SystemExit("Install optional ASE and mace-torch packages first; see the official MACE installation guide.") from exc

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atoms = read(args.input_cif)
    # mace_mp is the documented foundation-model ASE loader. It may download
    # and cache weights on first use; this script never hides that side effect.
    calculator = mace_mp(model=args.model, device=args.device)
    atoms.calc = calculator
    initial_energy = float(atoms.get_potential_energy())
    dyn = BFGS(atoms, logfile=str(args.output_dir / "opt.log"), trajectory=str(args.output_dir / "opt.traj"))
    converged = bool(dyn.run(fmax=args.fmax, steps=args.steps))
    final_energy = float(atoms.get_potential_energy())
    forces = atoms.get_forces()
    final_fmax = max(math.sqrt(sum(float(value) ** 2 for value in force)) for force in forces)
    if not all(math.isfinite(value) for value in (initial_energy, final_energy, final_fmax)):
        raise SystemExit("Non-finite energy/force: inspect model domain and input structure")
    write(args.output_dir / "relaxed.cif", atoms)
    write(args.output_dir / "relaxed.xyz", atoms)
    provenance = {
        "input": str(args.input_cif.resolve()),
        "model": args.model,
        "device": args.device,
        "fmax_eV_per_A": args.fmax,
        "max_steps": args.steps,
        "initial_energy_eV": initial_energy,
        "final_energy_eV": final_energy,
        "final_fmax_eV_per_A": final_fmax,
        "optimizer_converged": converged,
        "steps_taken": dyn.nsteps,
        "cell_optimized": False,
        "input_sha256": hashlib.sha256(args.input_cif.read_bytes()).hexdigest(),
        "atoms": len(atoms),
        "units": {"energy": "eV", "force": "eV/Angstrom", "length": "Angstrom"},
        "software": {"python": platform.python_version()},
        "note": "fmax/steps are stopping settings; inspect forces, trajectory and model domain before scientific use.",
    }
    for package in ("ase", "mace-torch", "torch"):
        try:
            provenance["software"][package] = version(package)
        except PackageNotFoundError:
            provenance["software"][package] = "unknown"
    checkpoint = Path(args.model)
    provenance["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest() if checkpoint.is_file() else None
    provenance["checkpoint_note"] = "Pin a local checkpoint path with --model to record an exact hash; aliases may resolve to different weights across package versions."
    (args.output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))
    return 0 if converged else 2


if __name__ == "__main__":
    raise SystemExit(main())
