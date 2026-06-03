-- =========================================================
-- Data Warehouse Schema: Mining / Heavy Equipment DW
-- Mode: development full-refresh schema
-- Note: this rebuilds dimensional and fact tables for a clean ETL run.
-- =========================================================

-- Drop facts first because they depend on dimensions
DROP TABLE IF EXISTS fact_equipment_usage CASCADE;
DROP TABLE IF EXISTS fact_production CASCADE;
DROP TABLE IF EXISTS fact_transaction CASCADE;

DROP TABLE IF EXISTS dim_equipment CASCADE;
DROP TABLE IF EXISTS dim_account CASCADE;
DROP TABLE IF EXISTS dim_project CASCADE;
DROP TABLE IF EXISTS dim_shift CASCADE;
DROP TABLE IF EXISTS dim_employee CASCADE;
DROP TABLE IF EXISTS dim_material CASCADE;
DROP TABLE IF EXISTS dim_site CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

DROP TABLE IF EXISTS stg_transaksi;
DROP TABLE IF EXISTS stg_production;
DROP TABLE IF EXISTS stg_alat_berat;

-- =========================================================
-- 1) Staging tables: raw copies from CSV
-- =========================================================
CREATE TABLE stg_transaksi (
  id bigint,
  time_id bigint,
  site_id bigint,
  project_id bigint,
  account_id bigint,
  variance text,
  budgeted_cost numeric,
  actual_cost numeric,
  created_at text,
  created_by text,
  date text,
  day int,
  day_name text,
  month int,
  year int,
  site_name text,
  region text,
  latitude numeric,
  longitude numeric,
  project_name text,
  project_manager text,
  status text,
  start_date text,
  end_date text,
  account_name text,
  account_type text,
  budget_category text,
  cost numeric
);

CREATE TABLE stg_production (
  production_id bigint,
  time_id bigint,
  site_id bigint,
  material_id bigint,
  employee_id bigint,
  shift_id bigint,
  produced_volume numeric,
  unit_cost numeric,
  date text,
  day int,
  month int,
  year int,
  day_name text,
  site_name text,
  region text,
  latitude numeric,
  longitude numeric,
  material_name text,
  material_type text,
  unit_of_measure text,
  quantity numeric,
  employee_name text,
  position text,
  department text,
  status text,
  hire_date text,
  shift_name text,
  start_time text,
  end_time text
);

CREATE TABLE stg_alat_berat (
  equipment_usage_id bigint,
  time_id bigint,
  date text,
  day int,
  day_name text,
  month int,
  year int,
  site_name text,
  region text,
  latitude numeric,
  longitude numeric,
  equipment_name text,
  equipment_type text,
  manufacture text,
  model text,
  capacity numeric,
  purchase_date text,
  operating_hours numeric,
  downtime_hours numeric,
  fuel_consumption numeric,
  maintenance_cost numeric,
  created_at text,
  created_by text
);

-- =========================================================
-- 2) Dimensions
-- =========================================================
CREATE TABLE dim_date (
  date_key int PRIMARY KEY,              -- YYYYMMDD
  full_date date UNIQUE NOT NULL,
  day int,
  month int,
  quarter int,
  year int,
  day_name text,
  month_name text,
  is_weekend boolean
);

-- site_nk prevents collision between different source systems that reuse same site_id.
CREATE TABLE dim_site (
  site_sk serial PRIMARY KEY,
  site_nk text UNIQUE NOT NULL,
  source_system text NOT NULL,
  source_site_id bigint,
  site_name text,
  region text,
  latitude numeric,
  longitude numeric
);

CREATE TABLE dim_material (
  material_sk serial PRIMARY KEY,
  material_id bigint UNIQUE NOT NULL,
  material_name text,
  material_type text,
  unit_of_measure text
);

CREATE TABLE dim_employee (
  employee_sk serial PRIMARY KEY,
  employee_id bigint UNIQUE NOT NULL,
  employee_name text,
  position text,
  department text,
  status text,
  hire_date date
);

CREATE TABLE dim_shift (
  shift_sk serial PRIMARY KEY,
  shift_id bigint UNIQUE NOT NULL,
  shift_name text,
  start_time time,
  end_time time
);

CREATE TABLE dim_project (
  project_sk serial PRIMARY KEY,
  project_id bigint UNIQUE NOT NULL,
  project_name text,
  project_manager text,
  status text,
  start_date date,
  end_date date
);

CREATE TABLE dim_account (
  account_sk serial PRIMARY KEY,
  account_id bigint UNIQUE NOT NULL,
  account_name text,
  account_type text,
  budget_category text
);

CREATE TABLE dim_equipment (
  equipment_sk serial PRIMARY KEY,
  equipment_nk text NOT NULL,
  equipment_name text,
  equipment_type text,
  manufacture text,
  model text,
  capacity numeric,
  purchase_date date,
  effective_from timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  effective_to timestamp,
  is_current boolean NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX uq_dim_equipment_current
ON dim_equipment(equipment_nk)
WHERE is_current = true;

-- =========================================================
-- 3) Fact tables
-- =========================================================
CREATE TABLE fact_production (
  production_sk serial PRIMARY KEY,
  production_id bigint UNIQUE NOT NULL,
  date_key int REFERENCES dim_date(date_key),
  site_sk int REFERENCES dim_site(site_sk),
  material_sk int REFERENCES dim_material(material_sk),
  employee_sk int REFERENCES dim_employee(employee_sk),
  shift_sk int REFERENCES dim_shift(shift_sk),
  produced_volume numeric,
  unit_cost numeric,
  quantity numeric,
  production_cost numeric
);

CREATE TABLE fact_transaction (
  transaction_sk serial PRIMARY KEY,
  transaction_id bigint UNIQUE NOT NULL,
  date_key int REFERENCES dim_date(date_key),
  site_sk int REFERENCES dim_site(site_sk),
  project_sk int REFERENCES dim_project(project_sk),
  account_sk int REFERENCES dim_account(account_sk),
  variance_status text,
  budgeted_cost numeric,
  actual_cost numeric,
  cost numeric,
  cost_variance numeric
);

CREATE TABLE fact_equipment_usage (
  equipment_usage_sk serial PRIMARY KEY,
  equipment_usage_id bigint UNIQUE NOT NULL,
  date_key int REFERENCES dim_date(date_key),
  site_sk int REFERENCES dim_site(site_sk),
  equipment_sk int REFERENCES dim_equipment(equipment_sk),
  operating_hours numeric,
  downtime_hours numeric,
  fuel_consumption numeric,
  maintenance_cost numeric,
  utilization_rate numeric
);
