# ETL + Data Warehouse Project

Project ini membuat pipeline ETL Dockerized untuk memuat 3 CSV ke PostgreSQL dan membentuk star schema untuk analisis produksi, transaksi biaya, dan penggunaan alat berat.

## Struktur folder wajib

```text
project-root/
├── data/
│   ├── dataset_alat_berat_dw.csv
│   ├── dataset_production.csv
│   └── dataset_transaksi.csv
├── etl/
│   ├── __init__.py
│   ├── etl.py
│   ├── main.py
│   └── requirements.txt
├── sql/
│   └── schema.sql
├── Dockerfile.etl
└── docker-compose.yml
```

## Cara menjalankan

```bash
docker compose up -d db
docker compose run --rm etl profile
docker compose run --rm etl run
```

Jika sebelumnya database sudah pernah dibuat dengan schema lama, reset volume dulu:

```bash
docker compose down -v
docker compose up -d db
docker compose run --rm etl run
```

## Output DW

Dimensions:
- `dim_date`
- `dim_site`
- `dim_material`
- `dim_employee`
- `dim_shift`
- `dim_project`
- `dim_account`
- `dim_equipment` dengan SCD Type 2

Facts:
- `fact_production`
- `fact_transaction`
- `fact_equipment_usage`

## Query validasi cepat

```sql
SELECT 'stg_production' AS table_name, COUNT(*) FROM stg_production
UNION ALL SELECT 'stg_transaksi', COUNT(*) FROM stg_transaksi
UNION ALL SELECT 'stg_alat_berat', COUNT(*) FROM stg_alat_berat
UNION ALL SELECT 'fact_production', COUNT(*) FROM fact_production
UNION ALL SELECT 'fact_transaction', COUNT(*) FROM fact_transaction
UNION ALL SELECT 'fact_equipment_usage', COUNT(*) FROM fact_equipment_usage;
```

```sql
SELECT d.year, d.month, s.region, SUM(f.production_cost) AS total_production_cost
FROM fact_production f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_site s ON s.site_sk = f.site_sk
GROUP BY d.year, d.month, s.region
ORDER BY d.year, d.month, s.region;
```
