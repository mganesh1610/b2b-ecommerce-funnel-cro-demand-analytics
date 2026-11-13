# Schema & Analytical Methodology

## 1. Relational Warehouse Schema (`SQLite` / `BigQuery` / `Snowflake` Compatible)

- `channel_taxonomy` (`traffic_type` PK, `channel_name`, `channel_group`, `planned_cpa_usd`): Maps raw web session `TrafficType` (`1..20`) into 6 standardized digital demand channels (`Paid Search`, `Email Marketing`, `SEO / GEO Organic`, `Paid Social`, `eCommerce Direct`, `Marketplaces & Syndication`).
- `web_sessions` (`12,330` rows): Session-level web analytics metrics (`administrative`, `informational`, `product_related` counts & durations, `bounce_rates`, `exit_rates`, `page_values`, `visitor_type`, `revenue_flag`, `estimated_order_value_usd`).
- `campaign_journeys` (`64,000` rows): Customer-level multi-arm experiment assignments (`recency`, `history_segment`, `history_spend`, `newbie`, `channel`, `segment`, `visit`, `conversion`, `spend`).
- `vw_channel_funnel_readout`: Multi-CTE SQL view computing `Visit -> Engaged Lead -> Order` conversion rates, net-new customer conversion, and attributed revenue by channel.
- `vw_tracking_gap_diagnostics`: Automated tracking-quality SQL view isolating `BounceRates > ExitRates` tag mismatches, zero-duration order-tag gaps, UTM taxonomy drift, and high-intent checkout drop-offs.

## 2. Mathematical & Statistical Formulations

1. **Exact Coalition Shapley Value Attribution ($N = 6$ Channels):**
   $$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(|N| - |S| - 1)!}{|N|!} \left[v(S \cup \{i\}) - v(S)\right], \quad \sum_{i \in N} \phi_i(v) = v(N)$$

2. **First-Order Markov Removal Effect ($RE_i$):**
   $$RE_i = v(N) - v(N \setminus \{i\}), \quad \widehat{R}_i^{\text{Markov}} = v(N) \cdot \frac{RE_i}{\sum_{j \in N} RE_j}$$

3. **Two-Proportion Power Sample Size, Z-Test, Wilson-Newcombe 95% CI & Holm Multiplicity:**
   $$n_{\text{arm}} = \left\lceil \frac{\left(z_{1-\alpha/2}\sqrt{2\bar{p}(1-\bar{p})} + z_{1-\beta}\sqrt{p_0(1-p_0) + p_1(1-p_1)}\right)^2}{(p_1 - p_0)^2} \right\rceil$$
   $$p_{(k)}^{\text{Holm}} = \min\left(1,\; \max_{j \le k} (m - j + 1)\,p_{(j)}\right)$$

4. **Annual Operating Plan (`AOP`) Diminishing-Returns Hill Reallocation:**
   $$\widehat{R}_c(B_c) = \phi_c \cdot \left(\frac{B_c}{B_c^0}\right)^{\gamma}, \quad \gamma = 0.78, \quad \sum_{c \in N} B_c^* = \sum_{c \in N} B_c^0 = \$1,200,000$$
