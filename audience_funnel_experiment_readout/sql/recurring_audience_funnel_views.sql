-- Mode / Tableau-ready recurring audience engagement cohort & telemetry audit SQL views
-- Built using SQL Joins & CTEs and Window Functions for self-serve BI scorecards.

-- View 1: Monthly & Visitor-Cohort Funnel Progression + Rolling Month Share
CREATE VIEW IF NOT EXISTS vw_recurring_audience_cohort_funnel AS
WITH cohort_base AS (
    SELECT
        month_name,
        visitor_type,
        channel_name,
        COUNT(*) AS sessions,
        SUM(engaged_lead) AS engaged_leads,
        SUM(revenue_flag) AS completed_orders,
        SUM(is_content_assisted) AS content_assisted_sessions,
        SUM(CASE WHEN is_content_assisted = 1 AND revenue_flag = 1 THEN 1 ELSE 0 END) AS content_assisted_orders,
        ROUND(AVG(bounce_rate), 5) AS avg_bounce_rate,
        ROUND(AVG(exit_rate), 5) AS avg_exit_rate
    FROM stg_web_sessions
    GROUP BY month_name, visitor_type, channel_name
),
totals AS (
    SELECT
        month_name,
        SUM(sessions) AS month_total_sessions
    FROM cohort_base
    GROUP BY month_name
)
SELECT
    c.month_name,
    c.visitor_type,
    c.channel_name,
    c.sessions,
    ROUND(100.0 * c.sessions / t.month_total_sessions, 2) AS month_traffic_share_pct,
    c.engaged_leads,
    ROUND(100.0 * c.engaged_leads / c.sessions, 2) AS visit_to_lead_pct,
    c.completed_orders,
    ROUND(100.0 * c.completed_orders / c.sessions, 2) AS visit_to_order_cvr_pct,
    c.content_assisted_sessions,
    c.content_assisted_orders,
    c.avg_bounce_rate,
    c.avg_exit_rate
FROM cohort_base AS c
JOIN totals AS t
    ON c.month_name = t.month_name;

-- View 2: Telemetry Tracking-Gap & Instrumentation Anomaly Breakdown by Channel
CREATE VIEW IF NOT EXISTS vw_telemetry_tracking_gap_audit AS
SELECT
    channel_name,
    COUNT(*) AS audited_sessions,
    SUM(CASE WHEN bounce_rate > exit_rate + 1e-6 THEN 1 ELSE 0 END) AS bounce_exceeds_exit_anomalies,
    SUM(CASE WHEN revenue_flag = 1 AND total_duration <= 0.0 THEN 1 ELSE 0 END) AS zero_duration_order_tag_gaps,
    SUM(CASE WHEN traffic_type IN (6, 13, 20) AND page_values = 0.0 AND revenue_flag = 0 AND bounce_rate > 0.15 THEN 1 ELSE 0 END) AS utm_taxonomy_drift_sessions,
    SUM(CASE WHEN page_values >= 25.0 AND revenue_flag = 0 AND exit_rate >= 0.04 THEN 1 ELSE 0 END) AS high_intent_checkout_dropoffs
FROM stg_web_sessions
GROUP BY channel_name;
