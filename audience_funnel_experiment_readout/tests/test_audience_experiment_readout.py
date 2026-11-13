"""Tests for the Audience Funnel & Experiment Readout P1 Extension."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path

from audience_funnel_experiment_readout.src.audience_experiment_readout import (
    compute_required_sample_size,
    run_audience_readout,
)

MODULE_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = tuple(
    base64.b64decode(tok).decode("utf-8")
    for tok in ("ZG93IGpvbmVz", "d2FsbCBzdHJlZXQgam91cm5hbA==", "d3Nq")
)


def make_synthetic_shoppers_and_hillstrom() -> tuple[str, str]:
    s_headers = [
        "Administrative",
        "Administrative_Duration",
        "Informational",
        "Informational_Duration",
        "ProductRelated",
        "ProductRelated_Duration",
        "BounceRates",
        "ExitRates",
        "PageValues",
        "SpecialDay",
        "Month",
        "OperatingSystems",
        "Browser",
        "Region",
        "TrafficType",
        "VisitorType",
        "Weekend",
        "Revenue",
    ]
    s_lines = [",".join(s_headers)]
    for i in range(60):
        info = 2 if i < 20 else 0
        rev = "TRUE" if (info > 0 and i % 3 == 0) or (info == 0 and i % 8 == 0) else "FALSE"
        bounce = "0.25" if i == 1 else "0.02"
        exit_r = "0.05"
        tt = "6" if i == 2 else "2"
        s_lines.append(
            f"1,15.0,{info},20.0,4,120.0,{bounce},{exit_r},0.0,0.0,Nov,2,2,1,{tt},Returning_Visitor,FALSE,{rev}"
        )

    h_headers = [
        "recency",
        "history_segment",
        "history",
        "mens",
        "womens",
        "zip_code",
        "newbie",
        "channel",
        "segment",
        "visit",
        "conversion",
        "spend",
    ]
    h_lines = [",".join(h_headers)]
    arms = ["Mens E-Mail", "Womens E-Mail", "No E-Mail"]
    for i in range(60):
        arm = arms[i % 3]
        conv = 1 if i % 15 == 0 else 0
        h_lines.append(f"3,1) $0 - $100,40.0,1,0,Urban,{i % 2},Web,{arm},1,{conv},20.0")
    return "\n".join(s_lines), "\n".join(h_lines)


class AudienceExperimentReadoutTests(unittest.TestCase):
    def test_power_sample_size_matches_analytical_plan(self) -> None:
        req_n = compute_required_sample_size(0.005726, 0.0025)
        self.assertGreater(req_n, 17000)
        self.assertLess(req_n, 18000)

    def test_offline_cohort_and_tracking_audit(self) -> None:
        s_csv, h_csv = make_synthetic_shoppers_and_hillstrom()
        with tempfile.TemporaryDirectory() as tmp:
            mod_tmp = Path(tmp) / "audience_funnel_experiment_readout"
            (mod_tmp / "sql").mkdir(parents=True, exist_ok=True)
            (mod_tmp / "sql" / "recurring_audience_funnel_views.sql").write_text(
                (MODULE_ROOT / "sql" / "recurring_audience_funnel_views.sql").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            res = run_audience_readout(mod_tmp, shoppers_csv_text=s_csv, hillstrom_csv_text=h_csv, verify_hashes=False)
            self.assertTrue(res["cohort_session_conservation_ok"])
            self.assertEqual(res["uci_online_shoppers_sessions"], 60)
            self.assertEqual(res["hillstrom_campaign_journeys"], 60)
            self.assertGreaterEqual(res["tracking_gap_audit"]["bounce_exceeds_exit_anomalies"], 1)

    def test_committed_outputs_and_hygiene(self) -> None:
        val_file = MODULE_ROOT / "outputs" / "audience_readout_validation.json"
        self.assertTrue(val_file.exists(), "Run audience_experiment_readout before tests.")
        val = json.loads(val_file.read_text(encoding="utf-8"))
        self.assertEqual(val["combined_verified_records"], 76330)
        self.assertEqual(val["tracking_gap_audit"]["total_tracking_anomalies"], 328)
        self.assertAlmostEqual(val["content_assisted_cro_test"]["abs_lift_pp"], 10.0389, places=3)

        for path in MODULE_ROOT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix in {".py", ".sql", ".md", ".json", ".csv"}:
                txt = path.read_text(encoding="utf-8").lower()
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, txt, f"Forbidden term in {path}")


if __name__ == "__main__":
    unittest.main()
