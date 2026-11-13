"""Recurring Audience Funnel Cohort, MDE Power Diagnostics & Tracking Audit Module.

Extends the core digital demand analytics repository with Mode/Tableau-ready SQL
cohort views, content-assisted conversion lift readout, guardrail checks, and
telemetry anomaly tracking across 76,330 SHA-256-verified public web session
and multi-channel campaign records.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sqlite3
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ONLINE_SHOPPERS_URL = (
    "https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip"
)
ONLINE_SHOPPERS_ZIP_SHA256 = "2972e6184d3ad7beaaa831d9fc2b059dc3ee29df69d1ec593c466a5cd8485d14"

HILLSTROM_URL = (
    "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)
HILLSTROM_CSV_SHA256 = "0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece"

CHANNEL_MAP: Dict[int, str] = {
    1: "Paid Search",
    2: "SEO / GEO Organic",
    3: "Paid Social",
    4: "Email Marketing",
    5: "Marketplaces & Syndication",
    6: "eCommerce Direct",
    7: "Marketplaces & Syndication",
    8: "SEO / GEO Organic",
    9: "Email Marketing",
    10: "Paid Search",
    11: "Paid Social",
    12: "Paid Social",
    13: "eCommerce Direct",
    14: "Marketplaces & Syndication",
    15: "Paid Search",
    16: "Marketplaces & Syndication",
    17: "Paid Social",
    18: "Email Marketing",
    19: "SEO / GEO Organic",
    20: "eCommerce Direct",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def ensure_verified_bytes(url: str, expected_sha256: Optional[str], cache_path: Path, verify: bool = True) -> bytes:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        raw = cache_path.read_bytes()
        if not verify or not expected_sha256 or sha256_bytes(raw) == expected_sha256:
            return raw
    req = urllib.request.Request(url, headers={"User-Agent": "AudienceFunnelReadout/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    digest = sha256_bytes(raw)
    if verify and expected_sha256 and digest != expected_sha256:
        raise ValueError(f"Checksum mismatch for {cache_path.name}: expected {expected_sha256}, got {digest}")
    cache_path.write_bytes(raw)
    return raw


def compute_required_sample_size(p0: float, mde_abs: float, alpha: float = 0.05, power: float = 0.80) -> int:
    z_alpha = 1.959963984540054 if abs(alpha - 0.05) < 1e-6 else 1.96
    z_beta = 0.8416212335729143 if abs(power - 0.80) < 1e-6 else 0.84
    p1 = p0 + mde_abs
    p_bar = 0.5 * (p0 + p1)
    num = (
        z_alpha * math.sqrt(2.0 * p_bar * (1.0 - p_bar))
        + z_beta * math.sqrt(p0 * (1.0 - p0) + p1 * (1.0 - p1))
    ) ** 2
    return int(math.ceil(num / (mde_abs ** 2)))


def normal_two_sided_p(z_abs: float) -> float:
    return math.erfc(abs(z_abs) / math.sqrt(2.0))


def run_audience_readout(
    module_root: Path,
    shoppers_csv_text: Optional[str] = None,
    hillstrom_csv_text: Optional[str] = None,
    verify_hashes: bool = True,
) -> Dict[str, Any]:
    """Run cohort SQL views, MDE power plan, content lift Z-test, and tracking-gap audit."""
    repo_root = module_root.parent
    cache_dir = repo_root / "data"
    sql_path = module_root / "sql" / "recurring_audience_funnel_views.sql"
    outputs_dir = module_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if shoppers_csv_text is None:
        z_bytes = ensure_verified_bytes(
            ONLINE_SHOPPERS_URL,
            ONLINE_SHOPPERS_ZIP_SHA256,
            cache_dir / "online_shoppers.zip",
            verify=verify_hashes,
        )
        with zipfile.ZipFile(io.BytesIO(z_bytes)) as zf:
            csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
            shoppers_csv_text = zf.read(csv_name).decode("utf-8")

    if hillstrom_csv_text is None:
        h_bytes = ensure_verified_bytes(
            HILLSTROM_URL,
            HILLSTROM_CSV_SHA256,
            cache_dir / "hillstrom.csv",
            verify=verify_hashes,
        )
        hillstrom_csv_text = h_bytes.decode("utf-8")

    shoppers_rows = list(csv.DictReader(io.StringIO(shoppers_csv_text)))
    hill_rows = list(csv.DictReader(io.StringIO(hillstrom_csv_text)))

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE TABLE stg_web_sessions (
                session_id INTEGER PRIMARY KEY,
                month_name TEXT,
                visitor_type TEXT,
                traffic_type INTEGER,
                channel_name TEXT,
                bounce_rate REAL,
                exit_rate REAL,
                page_values REAL,
                total_duration REAL,
                engaged_lead INTEGER,
                is_content_assisted INTEGER,
                revenue_flag INTEGER
            )
            """
        )
        batch = []
        for idx, r in enumerate(shoppers_rows, start=1):
            t_type = int(float(r["TrafficType"]))
            channel = CHANNEL_MAP.get(t_type, "eCommerce Direct")
            info_pages = int(float(r["Informational"]))
            admin_pages = int(float(r["Administrative"]))
            prod_pages = int(float(r["ProductRelated"]))
            total_dur = (
                float(r["Administrative_Duration"])
                + float(r["Informational_Duration"])
                + float(r["ProductRelated_Duration"])
            )
            bounce = float(r["BounceRates"])
            exit_r = float(r["ExitRates"])
            page_val = float(r["PageValues"])
            rev = 1 if r["Revenue"].strip().upper() == "TRUE" else 0
            engaged = 1 if (prod_pages + info_pages + admin_pages >= 3 or total_dur >= 60.0 or page_val > 0.0) else 0
            content_assisted = 1 if info_pages > 0 else 0
            batch.append(
                (
                    idx,
                    r["Month"].strip(),
                    r["VisitorType"].strip(),
                    t_type,
                    channel,
                    bounce,
                    exit_r,
                    page_val,
                    total_dur,
                    engaged,
                    content_assisted,
                    rev,
                )
            )
        conn.executemany("INSERT INTO stg_web_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch)
        conn.executescript(sql_path.read_text(encoding="utf-8"))

        cohort_rows = conn.execute(
            """
            SELECT month_name, visitor_type, channel_name, sessions, month_traffic_share_pct,
                   engaged_leads, visit_to_lead_pct, completed_orders, visit_to_order_cvr_pct,
                   content_assisted_sessions, content_assisted_orders, avg_bounce_rate, avg_exit_rate
            FROM vw_recurring_audience_cohort_funnel
            ORDER BY sessions DESC
            """
        ).fetchall()
        cohort_cols = [
            "month_name",
            "visitor_type",
            "channel_name",
            "sessions",
            "month_traffic_share_pct",
            "engaged_leads",
            "visit_to_lead_pct",
            "completed_orders",
            "visit_to_order_cvr_pct",
            "content_assisted_sessions",
            "content_assisted_orders",
            "avg_bounce_rate",
            "avg_exit_rate",
        ]
        with (outputs_dir / "weekly_audience_cohort_scorecard.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cohort_cols)
            w.writerows(cohort_rows)

        audit_row = conn.execute(
            """
            SELECT
                SUM(bounce_exceeds_exit_anomalies),
                SUM(zero_duration_order_tag_gaps),
                SUM(utm_taxonomy_drift_sessions),
                SUM(high_intent_checkout_dropoffs)
            FROM vw_telemetry_tracking_gap_audit
            """
        ).fetchone()
        b_anom, z_anom, u_anom, d_anom = [int(x or 0) for x in audit_row]
        total_anomalies = b_anom + z_anom + u_anom + d_anom

        # Content-assisted funnel comparison on product-engaged cohorts (ProductRelated > 0)
        ca_treat_n = sum(1 for r in shoppers_rows if int(float(r["ProductRelated"])) > 0 and int(float(r["Informational"])) > 0)
        ca_treat_c = sum(
            1
            for r in shoppers_rows
            if int(float(r["ProductRelated"])) > 0
            and int(float(r["Informational"])) > 0
            and r["Revenue"].strip().upper() == "TRUE"
        )
        ca_ctrl_n = sum(1 for r in shoppers_rows if int(float(r["ProductRelated"])) > 0 and int(float(r["Informational"])) == 0)
        ca_ctrl_c = sum(
            1
            for r in shoppers_rows
            if int(float(r["ProductRelated"])) > 0
            and int(float(r["Informational"])) == 0
            and r["Revenue"].strip().upper() == "TRUE"
        )
        p1 = ca_treat_c / max(1, ca_treat_n)
        p0 = ca_ctrl_c / max(1, ca_ctrl_n)
        p_pool = (ca_treat_c + ca_ctrl_c) / max(1, ca_treat_n + ca_ctrl_n)
        se = math.sqrt(max(1e-12, p_pool * (1.0 - p_pool) * (1.0 / max(1, ca_treat_n) + 1.0 / max(1, ca_ctrl_n))))
        z_content = (p1 - p0) / se

        ctrl_hill = [r for r in hill_rows if r["segment"].strip() == "No E-Mail"]
        ctrl_conv_rate = sum(int(r["conversion"]) for r in ctrl_hill) / max(1, len(ctrl_hill))
        req_n = compute_required_sample_size(ctrl_conv_rate if ctrl_conv_rate > 0 else 0.005726, 0.0025)

        cohort_session_sum = conn.execute("SELECT SUM(sessions) FROM vw_recurring_audience_cohort_funnel").fetchone()[0]
        summary = {
            "uci_online_shoppers_sessions": len(shoppers_rows),
            "hillstrom_campaign_journeys": len(hill_rows),
            "combined_verified_records": len(shoppers_rows) + len(hill_rows),
            "cohort_rows_materialized": len(cohort_rows),
            "cohort_session_conservation_ok": cohort_session_sum == len(shoppers_rows),
            "content_assisted_cro_test": {
                "treatment_n": ca_treat_n,
                "treatment_orders": ca_treat_c,
                "treatment_cvr_pct": round(p1 * 100.0, 4),
                "control_n": ca_ctrl_n,
                "control_orders": ca_ctrl_c,
                "control_cvr_pct": round(p0 * 100.0, 4),
                "abs_lift_pp": round((p1 - p0) * 100.0, 4),
                "z_stat": round(z_content, 4),
                "p_value": float(f"{normal_two_sided_p(z_content):.6e}"),
            },
            "tracking_gap_audit": {
                "bounce_exceeds_exit_anomalies": b_anom,
                "zero_duration_order_tag_gaps": z_anom,
                "utm_taxonomy_drift_sessions": u_anom,
                "high_intent_checkout_dropoffs": d_anom,
                "total_tracking_anomalies": total_anomalies,
            },
            "power_plan_mde_025pp": {
                "required_n_per_arm": req_n,
                "observed_control_n": len(ctrl_hill),
                "adequately_powered": len(ctrl_hill) >= req_n,
            },
        }
        (outputs_dir / "audience_readout_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
    finally:
        conn.close()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    out = run_audience_readout(root)
    print(json.dumps(out, indent=2))
