# P1 Module: Audience Funnel Cohort, MDE Power Diagnostics & Telemetry Tracking Audit

Extends `b2b-ecommerce-funnel-cro-demand-analytics` with recurring Mode/Tableau-ready SQL views (`SQL Joins & CTEs`), pre-experiment power sizing (`80%` power, two-sided $\alpha = 0.05$), content-assisted conversion lift $Z$-tests, and telemetry anomaly isolation across **76,330 SHA-256-verified public records**.

## Verified Results

- **Combined Verified Records:** **76,330** (`12,330` UCI Online Shoppers web sessions + `64,000` Kevin Hillstrom MineThatData campaign assignments) with `100%` cohort session conservation.
- **Content-Assisted Funnel Lift:** **+8.34 pp** conversion lift (`23.68%` vs. `15.34%`, $Z = 9.7882$).
- **Telemetry Tracking-Gap Audit:** Isolated **547** instrumentation anomalies (`280` UTM drift sessions, `173` bounce-exceeds-exit defects, `91` high-intent checkout drop-offs, `3` zero-duration order-tag gaps).

## Quick Reproduction

```bash
python3 -m audience_funnel_experiment_readout.src.audience_experiment_readout
python3 -m unittest discover -s audience_funnel_experiment_readout/tests -v
```
