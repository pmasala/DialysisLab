"""Tests of trace/evidence bookkeeping; these do not exercise dialysis software."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "check_traceability.py"
spec = importlib.util.spec_from_file_location("tracecheck", MODULE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TraceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.joinpath("fixture.txt").write_text("synthetic checker-test fixture")
        self.artifact = {"path": "fixture.txt", "sha256": hashlib.sha256(self.root.joinpath("fixture.txt").read_bytes()).hexdigest()}
        self.data = {
            "schema_version": 1, "baseline": "synthetic-unit-test",
            "needs": [{"id": "N1"}], "hazards": [{"id": "H1"}], "designs": [{"id": "D1"}],
            "requirements": [{"id": "R1", "statement": "Synthetic test requirement", "acceptance": "Synthetic acceptance", "needs": ["N1"], "hazards": ["H1"], "designs": ["D1"], "tests": ["T1"], "status": "verified", "reviewer": "synthetic fixture", "unresolved": [], "implementation": [dict(self.artifact)]}],
            "tests": [{"id": "T1", "requirements": ["R1"], "procedure": "Synthetic procedure", "expected": "Synthetic outcome", "result": "passed", "evidence": dict(self.artifact, baseline="synthetic-unit-test", run_id="fixture", executed_at="fixture", reviewer="fixture", environment="fixture")}],
            "prerequisites": [{"id": "P1", "status": "satisfied", "reviewer": "fixture", "evidence": dict(self.artifact)}]}

    def report(self):
        return checker.inspect(self.data, self.root)

    def test_complete_synthetic_graph(self):
        self.assertTrue(self.report()["recorded_release_gate_passed"])

    def test_draft_cannot_pass_release(self):
        self.data["requirements"][0]["status"] = "draft"
        self.assertFalse(self.report()["recorded_release_gate_passed"])

    def test_pass_without_evidence_is_error(self):
        del self.data["tests"][0]["evidence"]
        self.assertTrue(self.report()["structural_errors"])

    def test_tampered_evidence(self):
        self.root.joinpath("fixture.txt").write_text("changed")
        self.assertTrue(any("hash mismatch" in e for e in self.report()["structural_errors"]))

    def test_wrong_baseline(self):
        self.data["tests"][0]["evidence"]["baseline"] = "old"
        self.assertTrue(self.report()["structural_errors"])

    def test_broken_bidirectional_link(self):
        self.data["tests"][0]["requirements"] = []
        self.assertTrue(self.report()["structural_errors"])

    def test_unknown_reference(self):
        self.data["requirements"][0]["designs"] = ["MISSING"]
        self.assertTrue(self.report()["structural_errors"])

    def test_orphan_hazard(self):
        self.data["hazards"].append({"id": "H2"})
        self.assertTrue(any("orphan" in e for e in self.report()["structural_errors"]))

    def test_outside_root_artifact(self):
        self.data["tests"][0]["evidence"]["path"] = "../outside"
        self.assertTrue(any("outside project root" in e for e in self.report()["structural_errors"]))

    def test_duplicate_id(self):
        self.data["needs"].append({"id": "N1"})
        self.assertTrue(self.report()["structural_errors"])

    def test_open_prerequisite(self):
        self.data["prerequisites"][0]["status"] = "open"
        self.assertFalse(self.report()["recorded_release_gate_passed"])

    def test_planned_test_is_not_pass(self):
        self.data["tests"][0]["result"] = "planned"
        self.assertFalse(self.report()["recorded_release_gate_passed"])


if __name__ == "__main__":
    unittest.main()
