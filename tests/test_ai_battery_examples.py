import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "examples" / "ai_battery" / "msd_from_csv.py"
CSV = ROOT / "examples" / "ai_battery" / "example_trajectory.csv"


class AiBatteryExampleTests(unittest.TestCase):
    def test_msd_units_multi_origin_and_ballistic_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "msd.json"
            subprocess.run([sys.executable, str(SCRIPT), str(CSV), "--output", str(output)], check=True)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["points"][0]["msd_A2"], 1.0)
        slope = result["fit"]["slope_A2_per_ps"]
        self.assertGreater(slope, 0)
        self.assertAlmostEqual(result["fit"]["candidate_D_cm2_per_s"], slope / 6.0 * 1e-4)
        self.assertFalse(result["fit"]["diffusive_regime_verified"])
        self.assertIn("cannot establish", result["fit"]["interpretation"])


    def test_relax_help_does_not_import_optional_stack(self):
        script = ROOT / "examples" / "ai_battery" / "relax_mace.py"
        subprocess.run([sys.executable, str(script), "--help"], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
