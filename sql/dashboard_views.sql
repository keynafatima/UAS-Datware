```sql
-- =========================================================
-- Dashboard Semantic Views for PT XYZ Mining Data Warehouse
-- Target DB: PostgreSQL (dw)
-- Run after: docker compose run --rm etl run
-- Command example:
-- docker compose exec -T db psql -U dw_user -d dw < sql/dashboard_views.sql
-- =========================================================

DROP VIEW IF EXISTS vw_dashboard_kpi_monthly;
DROP VIEW IF EXISTS vw_dashboard_production_monthly;
DROP VIEW IF EXISTS vw_dashboard_equipment_monthly;
DROP VIEW IF EXISTS vw_dashboard_financial_monthly;

-- 1) Production mart: volume, cost, material, operator, shift, site, time

CREATE OR REPLACE VIEW vw_dashboard_production_monthly AS
SELECT
    f.production_sk,
    f.production_id,
    d.full_date,
    d.date_key,
    d.day,
    d.month,
    d.month_name,
    d.quarter,
    d.year,
    d.day_name,
    d.is_weekend,
    s.site_name,
    s.region,
    s.latitude,
    s.longitude,
    m.material_name,
    m.material_type,
    m.unit_of_measure,
    e.employee_name,
    e.position,
    e.department,
    sh.shift_name,
    sh.start_time,
    sh.end_time,
    f.produced_volume,
    f.unit_cost,
    f.quantity,
    f.production_cost,
    CASE
        WHEN f.produced_volume IS NULL OR f.produced_volume = 0 THEN NULL
        ELSE f.production_cost / f.produced_volume
    END AS cost_per_volume
FROM fact_production f
LEFT JOIN dim_date d ON d.date_key = f.date_key
LEFT JOIN dim_site s ON s.site_sk = f.site_sk
LEFT JOIN dim_material m ON m.material_sk = f.material_sk
LEFT JOIN dim_employee e ON e.employee_sk = f.employee_sk
LEFT JOIN dim_shift sh ON sh.shift_sk = f.shift_sk;

-- 2) Equipment mart: operating hours, downtime, fuel, maintenance, utilization

CREATE OR REPLACE VIEW vw_dashboard_equipment_monthly AS
SELECT
    f.equipment_usage_sk,
    f.equipment_usage_id,
    d.full_date,
    d.date_key,
    d.day,
    d.month,
    d.month_name,
    d.quarter,
    d.year,
    d.day_name,
    d.is_weekend,
    s.site_name,
    s.region,
    s.latitude,
    s.longitude,
    e.equipment_name,
    e.equipment_type,
    e.manufacture,
    e.model,
    e.capacity,
    e.purchase_date,
    e.is_current,
    f.operating_hours,
    f.downtime_hours,
    f.fuel_consumption,
    f.maintenance_cost,
    f.utilization_rate,
    CASE
        WHEN (COALESCE(f.operating_hours, 0) + COALESCE(f.downtime_hours, 0)) = 0 THEN NULL
        ELSE f.downtime_hours / (COALESCE(f.operating_hours, 0) + COALESCE(f.downtime_hours, 0))
    END AS downtime_rate,
    CASE
        WHEN f.operating_hours IS NULL OR f.operating_hours = 0 THEN NULL
        ELSE f.fuel_consumption / f.operating_hours
    END AS fuel_per_operating_hour,
    CASE
        WHEN f.operating_hours IS NULL OR f.operating_hours = 0 THEN NULL
        ELSE f.maintenance_cost / f.operating_hours
    END AS maintenance_cost_per_hour
FROM fact_equipment_usage f
LEFT JOIN dim_date d ON d.date_key = f.date_key
LEFT JOIN dim_site s ON s.site_sk = f.site_sk
LEFT JOIN dim_equipment e ON e.equipment_sk = f.equipment_sk;

-- 3) Financial mart: budget vs actual, variance, project, account, site, time
-- This view maps the implemented fact_transaction table to the mission's fact_financials concept.

CREATE OR REPLACE VIEW vw_dashboard_financial_monthly AS
SELECT
    f.transaction_sk AS financial_sk,
    f.transaction_id AS financial_id,
    d.full_date,
    d.date_key,
    d.day,
    d.month,
    d.month_name,
    d.quarter,
    d.year,
    d.day_name,
    d.is_weekend,
    s.site_name,
    s.region,
    s.latitude,
    s.longitude,
    p.project_name,
    p.project_manager,
    p.status AS project_status,
    p.start_date AS project_start_date,
    p.end_date AS project_end_date,
    a.account_name,
    a.account_type,
    a.budget_category,
    f.variance_status,
    f.budgeted_cost,
    f.actual_cost,
    f.cost,
    f.cost_variance,
    CASE
        WHEN f.budgeted_cost IS NULL OR f.budgeted_cost = 0 THEN NULL
        ELSE f.actual_cost / f.budgeted_cost
    END AS budget_realization_ratio,
    CASE
        WHEN f.budgeted_cost IS NULL OR f.budgeted_cost = 0 THEN NULL
        ELSE f.cost_variance / f.budgeted_cost
    END AS variance_ratio
FROM fact_transaction f
LEFT JOIN dim_date d ON d.date_key = f.date_key
LEFT JOIN dim_site s ON s.site_sk = f.site_sk
LEFT JOIN dim_project p ON p.project_sk = f.project_sk
LEFT JOIN dim_account a ON a.account_sk = f.account_sk;

-- 4) Monthly KPI helper for executive dashboard cards/trends

CREATE OR REPLACE VIEW vw_dashboard_kpi_monthly AS
SELECT
    'production' AS subject_area,
    year,
    month,
    month_name,
    quarter,
    region,
    SUM(produced_volume) AS total_produced_volume,
    SUM(production_cost) AS total_production_cost,
    NULL::numeric AS total_operating_hours,
    NULL::numeric AS total_downtime_hours,
    NULL::numeric AS total_fuel_consumption,
    NULL::numeric AS total_maintenance_cost,
    NULL::numeric AS avg_utilization_rate,
    NULL::numeric AS total_budgeted_cost,
    NULL::numeric AS total_actual_cost,
    NULL::numeric AS total_cost_variance
FROM vw_dashboard_production_monthly
GROUP BY year, month, month_name, quarter, region

UNION ALL

SELECT
    'equipment' AS subject_area,
    year,
    month,
    month_name,
    quarter,
    region,
    NULL::numeric AS total_produced_volume,
    NULL::numeric AS total_production_cost,
    SUM(operating_hours) AS total_operating_hours,
    SUM(downtime_hours) AS total_downtime_hours,
    SUM(fuel_consumption) AS total_fuel_consumption,
    SUM(maintenance_cost) AS total_maintenance_cost,
    AVG(utilization_rate) AS avg_utilization_rate,
    NULL::numeric AS total_budgeted_cost,
    NULL::numeric AS total_actual_cost,
    NULL::numeric AS total_cost_variance
FROM vw_dashboard_equipment_monthly
GROUP BY year, month, month_name, quarter, region

UNION ALL

SELECT
    'financial' AS subject_area,
    year,
    month,
    month_name,
    quarter,
    region,
    NULL::numeric AS total_produced_volume,
    NULL::numeric AS total_production_cost,
    NULL::numeric AS total_operating_hours,
    NULL::numeric AS total_downtime_hours,
    NULL::numeric AS total_fuel_consumption,
    NULL::numeric AS total_maintenance_cost,
    NULL::numeric AS avg_utilization_rate,
    SUM(budgeted_cost) AS total_budgeted_cost,
    SUM(actual_cost) AS total_actual_cost,
    SUM(cost_variance) AS total_cost_variance
FROM vw_dashboard_financial_monthly
GROUP BY year, month, month_name, quarter, region;
```
