import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from worker import parse_gaussian_output, run_smoke, validate_gaussian_input, validate_request

class TestWorker(unittest.TestCase):
    def setUp(self):
        self.config = {"allowed_projects": ["SIM-MN-001"], "max_cpu_index": 15, "max_memory_gb": 100}

    def test_smoke_request(self):
        data = {"schema_version": 1, "job_id": "MB-SMOKE-001",
                "project_id": "SIM-MN-001", "kind": "smoke", "mode": "synthetic"}
        self.assertEqual(validate_request(data, "MB-SMOKE-001.json", self.config), "MB-SMOKE-001")
        with tempfile.TemporaryDirectory() as work:
            output = run_smoke(data, Path(work))
            self.assertEqual(output["status"], "completed")
            self.assertIsNone(output["gaussian"])

    def test_gaussian_input_limit(self):
        good = b"%CPU=0-15\n%mem=60GB\n#p B3LYP/def2SVP Opt Freq\n\nH2\n\n0 1\nH 0 0 0\nH 0 0 0.74\n"
        self.assertIn("#p", validate_gaussian_input(good, self.config))
        with self.assertRaises(ValueError):
            validate_gaussian_input(good.replace(b"%CPU=0-15", b"%CPU=0-63"), self.config)
        with self.assertRaises(ValueError):
            validate_gaussian_input(good + b"\n%rwf=/tmp/evil\n", self.config)
        with self.assertRaises(ValueError):
            validate_gaussian_input(good + b"\n--Link1--\n", self.config)

    def test_real_request_gated(self):
        job = {"schema_version": 1, "job_id": "MB-G16-001",
               "project_id": "SIM-MN-001", "kind": "gaussian16",
               "mode": "real-computation", "approved": False,
               "input_path": "jobs/inputs/MB-G16-001.inp",
               "input_sha256": "0" * 64}
        with self.assertRaises(ValueError):
            validate_request(job, "MB-G16-001.json", self.config)
        job["approved"] = True
        self.assertEqual(validate_request(job, "MB-G16-001.json", self.config), "MB-G16-001")

    def test_parser_is_not_ts_validator(self):
        fixture = (
            " SCF Done:  E(UB3LYP) =  -1500.1234567890     A.U. after   10 cycles\n"
            " Optimization completed.\n"
            " Frequencies --  -512.3   120.5   240.8\n"
            " Sum of electronic and thermal Free Energies= -1499.950000\n"
            " Normal termination of Gaussian 16 at Fri Jan 01 01:00:00 2027.\n"
        )
        with tempfile.TemporaryDirectory() as work:
            file = Path(work) / "synthetic_parser_test.out"
            file.write_text(fixture)
            parsed = parse_gaussian_output(file)
        self.assertEqual(parsed["scf_energy_hartree"], -1500.123456789)
        self.assertEqual(parsed["gibbs_energy_hartree"], -1499.95)
        self.assertEqual(parsed["imaginary_count_below_zero"], 1)
        self.assertTrue(parsed["normal_termination"])
        self.assertFalse(parsed["ts_irc_validated"])

if __name__ == "__main__":
    unittest.main()
