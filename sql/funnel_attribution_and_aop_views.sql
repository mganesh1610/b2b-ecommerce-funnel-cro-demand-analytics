-- =============================================================================
-- Full-Funnel Digital Demand, Customer Journey (Visit -> Lead -> Order),
-- Net-New Customer Attribution & Tracking-Gap Diagnostic SQL Views
-- Compatible with SQLite, PostgreSQL, Snowflake, and BigQuery (SQL Joins & CTEs)
-- =============================================================================

DROP VIEW IF EXISTS vw_channel_funnel_readout;
CREATE VIEW vw_channel_funnel_readout AS
WITH session_enriched AS (
    SELECT
        s.session_id,
        s.month,
        s.traffic_type,
        t.channel_name,
        t.channel_group,
        t.planned_cpa_usd,
        s.visitor_type,
        CASE WHEN s.visitor_type = 'New_Visitor' THEN 1 ELSE 0 END AS is_net_new_visitor,
        s.administrative_duration + s.informational_duration + s.product_related_duration AS total_session_sec,
        s.informational,
        s.product_related,
        s.bounce_rates,
        s.exit_rates,
        s.page_values,
        CASE
            WHEN (s.product_related >= 5 OR s.informational >= 2 OR s.page_values > 0.0)
                 AND s.bounce_rates < 0.05
            THEN 1 ELSE 0
        END AS is_engaged_lead,
        s.revenue_flag AS is_order,
        s.estimated_order_value_usd
    FROM web_sessions s
    INNER JOIN channel_taxonomy t
        ON s.traffic_type = t.traffic_type
),
channel_agg AS (
    SELECT
        channel_name,
        channel_group,
        COUNT(*) AS total_visits,
        SUM(is_net_new_visitor) AS net_new_visits,
        SUM(is_engaged_lead) AS engaged_leads,
        SUM(is_order) AS completed_orders,
        SUM(CASE WHEN is_net_new_visitor = 1 AND is_order = 1 THEN 1 ELSE 0 END) AS net_new_orders,
        ROUND(AVG(bounce_rates) * 100.0, 2) AS avg_bounce_rate_pct,
        ROUND(AVG(exit_rates) * 100.0, 2) AS avg_exit_rate_pct,
        ROUND(AVG(total_session_sec), 2) AS avg_session_duration_sec,
        ROUND(SUM(estimated_order_value_usd), 2) AS attributed_revenue_usd,
        ROUND(SUM(CASE WHEN is_net_new_visitor = 1 THEN estimated_order_value_usd ELSE 0.0 END), 2) AS net_new_revenue_usd
    FROM session_enriched
    GROUP BY channel_name, channel_group
)
SELECT
    channel_name,
    channel_group,
    total_visits,
    net_new_visits,
    engaged_leads,
    completed_orders,
    net_new_orders,
    ROUND(engaged_leads * 100.0 / NULLIF(total_visits, 0), 2) AS visit_to_lead_rate_pct,
    ROUND(completed_orders * 100.0 / NULLIF(engaged_leads, 0), 2) AS lead_to_order_rate_pct,
    ROUND(completed_orders * 100.0 / NULLIF(total_visits, 0), 2) AS visit_to_order_cvr_pct,
    ROUND(net_new_orders * 100.0 / NULLIF(net_new_visits, 0), 2) AS net_new_cvr_pct,
    avg_bounce_rate_pct,
    avg_exit_rate_pct,
    avg_session_duration_sec,
    attributed_revenue_usd,
    net_new_revenue_usd
FROM channel_agg
ORDER BY attributed_revenue_usd DESC;

DROP VIEW IF EXISTS vw_tracking_gap_diagnostics;
CREATE VIEW vw_tracking_gap_diagnostics AS
WITH flagged_sessions AS (
    SELECT
        s.session_id,
        t.channel_name,
        CASE WHEN s.bounce_rates > s.exit_rates + 0.0001 THEN 1 ELSE 0 END AS bounce_exceeds_exit_anomaly,
        CASE WHEN s.revenue_flag = 1 AND (s.administrative_duration + s.informational_duration + s.product_related_duration) <= 0.0 THEN 1 ELSE 0 END AS zero_duration_order_tag_gap,
        CASE WHEN s.traffic_type >= 14 THEN 1 ELSE 0 END AS unmapped_utm_taxonomy_drift,
        CASE WHEN s.product_related >= 10 AND s.exit_rates >= 0.10 AND s.revenue_flag = 0 THEN 1 ELSE 0 END AS high_intent_checkout_dropoff,
        s.estimated_order_value_usd
    FROM web_sessions s
    LEFT JOIN channel_taxonomy t
        ON s.traffic_type = t.traffic_type
)
SELECT
    channel_name,
    COUNT(*) AS audited_sessions,
    SUM(bounce_exceeds_exit_anomaly) AS bounce_exceeds_exit_count,
    SUM(zero_duration_order_tag_gap) AS zero_duration_order_tag_gaps,
    SUM(unmapped_utm_taxonomy_drift) AS utm_taxonomy_drift_sessions,
    SUM(high_intent_checkout_dropoff) AS high_intent_checkout_dropoffs
FROM flagged_sessions
GROUP BY channel_name
ORDER BY audited_sessions DESC;
