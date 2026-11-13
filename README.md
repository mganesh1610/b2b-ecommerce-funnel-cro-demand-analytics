# Omnichannel Digital Demand, Web Funnel (`Visit -> Lead -> Order`), CRO Experimentation & AOP Investment Sizing Engine

An end-to-end digital marketing analytics, customer journey attribution, statistical CRO/A/B measurement, web tracking-gap governance, and Annual Operating Plan (`AOP`) investment-sizing platform built in **Python 3**, **SQL (`SQL Joins & CTEs`)**, **R (`stats::prop.test`, `p.adjust`)**, and self-serve **Tableau / Power BI / Looker / Advanced Excel** reporting marts.

---

## 1. Business & Analytical Capabilities

1. **Full-Funnel Customer Journey (`Visit -> Lead -> Order`) & Net-New Customer Attribution:**
   - Models **12,330 web visitor sessions** and **64,000 randomized multichannel customer journeys** (**76,330 verified public records**) across **Paid Search, Email Marketing, SEO / GEO Organic, Paid Social, eCommerce Direct, and Marketplaces & Syndication**.
   - Quantifies stage-by-stage progression (`Visit -> Engaged Lead -> Completed Order`), isolates **Net-New Customer (`New_Visitor` / `newbie = 1`)** revenue vs. repeat eCommerce demand, and compares heuristic **Last-Touch** against **Exact 6-Channel Coalition Shapley Value** and **First-Order Markov Chain Removal-Effect** attribution (`$0.00` coalition revenue drift).
2. **Statistical CRO & Multi-Arm A/B Measurement Plans & Readouts:**
   - Computes pre-launch Minimum Detectable Effect (`MDE = 0.25 pp`, `80%` power, two-sided `alpha = 0.05`, `n = 17,398` required per arm) and delivers decision-ready readouts using **Two-Proportion Z-tests**, **Wilson-Newcombe 95% Confidence Intervals**, **Holm-Bonferroni multiplicity correction**, and **Welch's two-sample spend t-tests** (with a companion `R` verification script).
3. **Proactive Web Analytics (`GA4` / `Adobe Analytics`) Tracking-Gap & Funnel Risk Diagnostics:**
   - Audits session telemetry to surface **`280` UTM taxonomy drift sessions**, **`173` bounce-vs-exit instrumentation mismatches**, **`91` high-intent checkout drop-offs**, and **`3` zero-duration order-tag firing gaps** with prioritized remediation steps.
4. **Behavioral Audience Segmentation & `AOP` Investment Case Sizing:**
   - Segments visitors into 4 actionable cohorts (`High-Intent Net-New Buyers`, `High-Value Repeat eCommerce`, `Technical Content & Nurture Leads`, `High-Bounce & Early Discovery Traffic`) and optimizes a **`$1.20M` Annual Operating Plan (`AOP`)** budget via diminishing-returns Hill elasticity (`gamma = 0.78`), projecting a **`+13.29%` (`+$83.2K`) attributed revenue lift** under exact budget conservation.

---

## 2. Verified Public Datasets & Provenance

| Dataset | Scale | Direct URL | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **UCI Online Shoppers Purchasing Intention Dataset** (DOI `10.24432/C5F88Q`, CC BY 4.0) | `12,330` web sessions × `18` cols | `https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip` | `2972e6184d3ad7beaaa831d9fc2b059dc3ee29df69d1ec593c466a5cd8485d14` |
| **Kevin Hillstrom MineThatData Multi-Channel Marketing Dataset** | `64,000` customer journeys × `12` cols | `http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv` | `0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece` |

- **Backup Public Datasets:** Olist Marketing Qualified Leads & E-Commerce Funnel Dataset (`https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist`) and Google Merchandise Store GA4 Public BigQuery Dataset (`https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset`).

---

## 3. Verified Execution Highlights

| Metric | Verified Result |
| :--- | :---: |
| Combined SHA-256 Verified Web & Campaign Records | `76,330` |
| Web Funnel Progression (`Visits -> Engaged Leads -> Orders`) | `12,330 -> 9,942 (80.63%) -> 1,908 (15.47% CVR)` |
| Net-New Customer Orders (`New_Visitor` Purchases) | `422` |
| Technical Content Assisted vs. Product-Only CRO Lift | `+8.34 pp` (`23.68%` vs. `15.34%`, `+54.37%` rel. lift, `Z = 9.79`) |
| Net-New Customer Lifecycle Email vs. Holdout Lift | `+0.63 pp` (`+169.26%` rel. lift, `Z = 6.02`, Holm `p = 3.57e-9`) |
| Pooled Digital Visit-to-Lead Lift | `+6.09 pp` (`+57.35%` rel. lift, `Z = 20.51`) |
| Tracking-Gap Anomalies Flagged (`UTM` + `Bounce/Exit` + `Checkout` + `Order Tag`) | `547` (`280 + 173 + 91 + 3`) |
| Projected `$1.20M` AOP Reallocation Revenue Lift | `+13.29%` (`+$83,239.60`, `$0.00` budget drift) |
| Automated SQL & Statistical Quality Gates / Unit Tests | `12/12 (100%)` / `5/5 Passed` |

---

## 4. Quick Start

```bash
python3 src/digital_demand_funnel_cro_engine.py
python3 tests/test_digital_demand_engine.py
Rscript r/cro_ab_statistical_readout.R
```

## 5. Repository Structure

```text
b2b-ecommerce-funnel-cro-demand-analytics/
├── README.md
├── docs/
│   └── schema_and_methodology.md
├── outputs/
│   ├── audience_segment_sizing_mart.csv
│   ├── channel_funnel_attribution_aop_mart.csv
│   ├── cro_ab_measurement_readout.csv
│   ├── digital_demand_validation_summary.json
│   └── tracking_gap_risk_audit.csv
├── r/
│   └── cro_ab_statistical_readout.R
├── sql/
│   └── funnel_attribution_and_aop_views.sql
├── src/
│   └── digital_demand_funnel_cro_engine.py
└── tests/
    └── test_digital_demand_engine.py
```
