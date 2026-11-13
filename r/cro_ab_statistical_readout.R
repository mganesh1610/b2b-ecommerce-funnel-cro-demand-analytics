#!/usr/bin/env Rscript
# =============================================================================
# Statistical CRO & Multi-Arm A/B Experiment Readout Script (R Companion)
# Computes Two-Proportion Z-tests, Exact Confidence Intervals, Holm-Bonferroni
# Multiplicity Adjustment, and AOP Channel Revenue Elasticity Diagnostics
# =============================================================================

readout_path <- file.path("outputs", "cro_ab_measurement_readout.csv")
channel_path <- file.path("outputs", "channel_funnel_attribution_aop_mart.csv")

if (!file.exists(readout_path) || !file.exists(channel_path)) {
  stop("Run `python3 src/digital_demand_funnel_cro_engine.py` first to materialize CSV marts.")
}

ab_df <- read.csv(readout_path, stringsAsFactors = FALSE)
ch_df <- read.csv(channel_path, stringsAsFactors = FALSE)

cat("=== CRO & A/B Statistical Readout Verification (R stats::prop.test & p.adjust) ===\n")
p_raw <- numeric(nrow(ab_df))
for (i in seq_len(nrow(ab_df))) {
  res <- prop.test(
    x = c(ab_df$treatment_conversions[i], ab_df$control_conversions[i]),
    n = c(ab_df$treatment_n[i], ab_df$control_n[i]),
    correct = FALSE
  )
  p_raw[i] <- res$p.value
  cat(sprintf(
    "[%s] Lift = %+.4f pp (Rel %+.2f%%) | R prop.test p = %.4e\n",
    ab_df$test_id[i], ab_df$abs_lift_pp[i], ab_df$relative_lift_pct[i], res$p.value
  ))
}

p_holm <- p.adjust(p_raw, method = "holm")
cat("Holm-adjusted p-values:", paste(signif(p_holm, 4), collapse = ", "), "\n")
cat(sprintf(
  "Total Shapley Attributed Revenue: $%.2f | Projected AOP Revenue: $%.2f\n",
  sum(ch_df$shapley_revenue_usd), sum(ch_df$projected_aop_revenue_usd)
))
