#!/usr/bin/env python3
"""Unit and boundary tests for the Omnichannel Digital Demand & CRO Analytics Engine."""

import json
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from digital_demand_funnel_cro_engine import (  # noqa: E402
    holm_bonferroni,
    run_pipeline,
    sample_size_two_proportion,
    wilson_newcombe_diff_ci,
)


class TestDigitalDemandEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        scratch_data = ROOT_DIR.parents[1] / "data"
        cls.summary = run_pipeline(scratch_cache_dir=scratch_data if scratch_data.exists() else None)

    def test_all_12_quality_gates_pass(self) -> None:
        self.assertEqual(self.summary["quality_gates_passed"], 12)
        self.assertEqual(self.summary["quality_gates_total"], 12)
        for gate, passed in self.summary["quality_gates"].items():
            self.assertTrue(passed, f"Quality gate failed: {gate}")

    def test_funnel_and_record_conservation(self) -> None:
        self.assertEqual(self.summary["datasets"]["combined_verified_records"], 76330)
        funnel = self.summary["funnel_overview"]
        self.assertEqual(funnel["total_visits"], 12330)
        self.assertEqual(funnel["completed_orders"], 1908)
        self.assertGreater(funnel["engaged_leads"], funnel["completed_orders"])
        self.assertGreater(funnel["net_new_customer_orders"], 400)

    def test_statistical_rigor_and_multiplicity_bounds(self) -> None:
        pvals = [0.0001, 0.02, 0.04, 0.25]
        adj = holm_bonferroni(pvals)
        self.assertEqual(len(adj), 4)
        for raw_p, adj_p in zip(pvals, adj):
            self.assertGreaterEqual(adj_p, raw_p)
            self.assertLessEqual(adj_p, 1.0)

        low, high = wilson_newcombe_diff_ci(267, 21307, 122, 21306)
        self.assertGreater(low, 0.0045)
        self.assertLess(high, 0.0090)

    def test_power_sample_size_plan(self) -> None:
        n_req = sample_size_two_proportion(0.005726, 0.0025, alpha=0.05, power=0.80)
        self.assertGreater(n_req, 15000)
        self.assertLess(n_req, 21000)
        self.assertTrue(self.summary["power_measurement_plan"]["adequately_powered"])

    def test_aop_positive_lift_and_output_artifacts(self) -> None:
        aop = self.summary["aop_investment_sizing"]
        self.assertEqual(aop["annual_aop_budget_usd"], 1_200_000.0)
        self.assertGreater(aop["incremental_aop_revenue_lift_usd"], 0.0)
        for fname in (
            "digital_demand_validation_summary.json",
            "channel_funnel_attribution_aop_mart.csv",
            "audience_segment_sizing_mart.csv",
            "cro_ab_measurement_readout.csv",
            "tracking_gap_risk_audit.csv",
        ):
            p = ROOT_DIR / "outputs" / fname
            self.assertTrue(p.exists(), f"Missing output artifact: {fname}")
            self.assertGreater(p.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
