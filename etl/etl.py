import os
import pandas as pd
from sqlalchemy import create_engine, text

# Daftar file sumber yang akan diproses dalam ETL.
# Format: (nama_file_csv, label_dataset, nama_tabel_staging)
# Data mentah dari file CSV ini nantinya akan dimuat ke tabel staging.
FILES = [
    ("dataset_alat_berat_dw.csv", "alat_berat", "stg_alat_berat"),
    ("dataset_production.csv", "production", "stg_production"),
    ("dataset_transaksi.csv", "transaksi", "stg_transaksi"),
]

# Membuat koneksi database PostgreSQL menggunakan SQLAlchemy
def _make_engine(db):
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['db']}"
    )
    return create_engine(url, pool_pre_ping=True)

# Membaca file schema.sql yang berisi struktur tabel data warehouse.
# Schema ini berisi definisi tabel staging, dimensi, dan fact.
def _read_sql_file():
    sql_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"schema.sql not found at {sql_path}")
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()

# Bagian data profiling.
# Fungsi ini digunakan untuk mengecek kondisi awal data CSV, seperti jumlah baris,
# nama kolom, tipe data, missing value, dan contoh data.
def profile_data(data_dir="/data"):
    """Print a quick profile of all source CSVs."""
    for fname, label, _ in FILES:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            print(f"missing: {path}")
            continue

        df = pd.read_csv(path)
        print(f"\n--- {label} ({path}) ---")
        print(f"rows={len(df)}, columns={len(df.columns)}")
        print("columns:", list(df.columns))
        print("dtypes:")
        print(df.dtypes)
        print("null values:")
        print(df.isna().sum()[df.isna().sum() > 0])
        print("sample:")
        print(df.head(3).to_dict(orient="records"))

# Fungsi utama untuk menjalankan seluruh proses ETL.
# Alurnya:
# 1. Membuat koneksi ke database
# 2. Membuat schema tabel
# 3. Meload data mentah CSV ke staging
# 4. Melakukan transformasi dan load ke tabel dimensi serta fact
def run_etl(db, data_dir="/data"):
    """Run full ETL: apply schema, load staging, transform dimensions, then load facts."""
    engine = _make_engine(db)

    # Menerapkan schema database dari file schema.sql.
    # Ini memastikan tabel staging, dimensi, dan fact sudah tersedia sebelum data dimuat.
    with engine.begin() as conn:
        conn.execute(text(_read_sql_file()))
    print("schema applied")
    
    # Tahap Load awal: data CSV dimasukkan ke tabel staging.
    load_staging(engine, data_dir)
    
    # Tahap Transform dan Load final: data staging diolah menjadi tabel dimensi dan fact.
    transform_and_load(engine)
    print("ETL finished.")

# Tahap Load ke Staging
# Fungsi ini membaca setiap file CSV, membersihkan nama kolom dari spasi,
# lalu memasukkan data mentah ke tabel staging yang sesuai.
def load_staging(engine, data_dir="/data"):
    """Load CSV files into staging tables."""
    for fname, _, table in FILES:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            print(f"skip missing {path}")
            continue

        print(f"loading {path} -> {table}")

        # Membaca data CSV sebagai string agar format data asli tetap aman saat masuk staging
        df = pd.read_csv(path, dtype=str)
        # Membersihkan nama kolom dari spasi di awal/akhir.
        df.columns = [c.strip() for c in df.columns]

        # Mengosongkan tabel staging sebelum data baru dimuat.
        # Ini dilakukan agar proses ETL bisa dijalankan ulang tanpa menumpuk data lama.
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY;"))

        # Memasukkan data CSV ke tabel staging.
        df.to_sql(table, engine, if_exists="append", index=False)
        print(f"loaded {len(df)} rows into {table}")


# Fungsi ini menghitung jumlah baris pada tabel tertentu untuk memastikan data sudah masuk.
def _dq_check_counts(engine, tables):
    checks = {}
    with engine.connect() as conn:
        for table in tables:
            checks[table] = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    print("DQ counts:", checks)
    return checks


def _exec(conn, sql):
    conn.execute(text(sql))

# Tahap Transform dan Load ke Data Warehouse.
# Data dari staging akan diubah menjadi struktur star schema:
# - Tabel dimensi: dim_date, dim_site, dim_material, dim_employee, dll.
# - Tabel fact: fact_production, fact_transaction, fact_equipment_usage.
def transform_and_load(engine):
    """Transform staging data into star schema dimensions and facts."""
    staging_counts = _dq_check_counts(
        engine, ["stg_alat_berat", "stg_production", "stg_transaksi"]
    )
    if all(v == 0 for v in staging_counts.values()):
        print("no data in staging, aborting transforms")
        return

    # Load tabel-tabel dimensi terlebih dahulu.
    # Dimensi harus dibuat lebih dulu karena fact table akan mengambil foreign key dari dimensi.
    with engine.begin() as conn:
        load_dim_date(conn)
        load_dim_site(conn)
        load_dim_material(conn)
        load_dim_employee(conn)
        load_dim_shift(conn)
        load_dim_project(conn)
        load_dim_account(conn)
        load_dim_equipment_scd2(conn)
        # Setelah dimensi tersedia, data fact dapat dimuat.
        load_fact_production(conn)
        load_fact_transaction(conn)
        load_fact_equipment_usage(conn)
    
    # Mengecek jumlah data setelah proses transformasi dan load selesai.
    _dq_check_counts(
        engine,
        [
            "dim_date",
            "dim_site",
            "dim_material",
            "dim_employee",
            "dim_shift",
            "dim_project",
            "dim_account",
            "dim_equipment",
            "fact_production",
            "fact_transaction",
            "fact_equipment_usage",
        ],
    )
    print("transforms and loads applied")


# Transformasi dimensi tanggal.
# Fungsi ini mengambil semua tanggal dari tabel staging transaksi, produksi, dan alat berat,
# lalu mengubahnya menjadi atribut tanggal seperti hari, bulan, kuartal, tahun, dan weekend.
def load_dim_date(conn):
    _exec(
        conn,
        """
        WITH raw_dates AS (
            SELECT CASE
                WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                ELSE NULL
            END AS full_date FROM stg_transaksi
            UNION
            SELECT CASE
                WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                ELSE NULL
            END AS full_date FROM stg_production
            UNION
            SELECT CASE
                WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                ELSE NULL
            END AS full_date FROM stg_alat_berat
        )
        INSERT INTO dim_date(date_key, full_date, day, month, quarter, year, day_name, month_name, is_weekend)
        SELECT DISTINCT
            to_char(full_date, 'YYYYMMDD')::int AS date_key,
            full_date,
            EXTRACT(day FROM full_date)::int,
            EXTRACT(month FROM full_date)::int,
            EXTRACT(quarter FROM full_date)::int,
            EXTRACT(year FROM full_date)::int,
            trim(to_char(full_date, 'Day')),
            trim(to_char(full_date, 'Month')),
            EXTRACT(isodow FROM full_date)::int IN (6, 7)
        FROM raw_dates
        WHERE full_date IS NOT NULL
        ON CONFLICT (date_key) DO NOTHING;
        """,
    )

# Transformasi dimensi site/lokasi.
# Site dibuat dari beberapa sumber data karena production, transaction, dan equipment
# bisa memiliki format atau ID lokasi yang berbeda.
def load_dim_site(conn):
    
    # Membuat dimensi site dari data production.
    # Natural key diberi prefix PRODUCTION agar tidak bentrok dengan site_id dari dataset lain.
    _exec(
        conn,
        """
        WITH src AS (
            SELECT
                'PRODUCTION:' || trim(site_id::text) AS site_nk,
                'PRODUCTION' AS source_system,
                site_id::bigint AS source_site_id,
                site_name,
                region,
                latitude,
                longitude
            FROM stg_production
            WHERE site_id::text ~ '^[0-9]+$'
        )
        INSERT INTO dim_site(site_nk, source_system, source_site_id, site_name, region, latitude, longitude)
        SELECT DISTINCT ON (site_nk)
            site_nk, source_system, source_site_id, site_name, region, latitude, longitude
        FROM src
        ORDER BY site_nk
        ON CONFLICT (site_nk) DO UPDATE SET
            site_name = EXCLUDED.site_name,
            region = EXCLUDED.region,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
        """,
    )
    
    # Membuat dimensi site dari data transaksi.
    # Prefix TRANSACTION digunakan agar site dari transaksi tidak tertukar dengan source lain.
    _exec(
        conn,
        """
        WITH src AS (
            SELECT
                'TRANSACTION:' || trim(site_id::text) AS site_nk,
                'TRANSACTION' AS source_system,
                site_id::bigint AS source_site_id,
                site_name,
                region,
                latitude,
                longitude
            FROM stg_transaksi
            WHERE site_id::text ~ '^[0-9]+$'
        )
        INSERT INTO dim_site(site_nk, source_system, source_site_id, site_name, region, latitude, longitude)
        SELECT DISTINCT ON (site_nk)
            site_nk, source_system, source_site_id, site_name, region, latitude, longitude
        FROM src
        ORDER BY site_nk
        ON CONFLICT (site_nk) DO UPDATE SET
            site_name = EXCLUDED.site_name,
            region = EXCLUDED.region,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
        """,
    )
    
    # Membuat dimensi site dari data alat berat.
    # Karena dataset equipment tidak memakai site_id numerik, natural key dibuat dengan hash md5
    # dari kombinasi nama lokasi, region, latitude, dan longitude.
    _exec(
        conn,
        """
        WITH src AS (
            SELECT
                'EQUIPMENT:' || md5(concat_ws('|', lower(trim(site_name)), lower(trim(region)), latitude::text, longitude::text)) AS site_nk,
                'EQUIPMENT' AS source_system,
                NULL::bigint AS source_site_id,
                site_name,
                region,
                latitude,
                longitude
            FROM stg_alat_berat
        )
        INSERT INTO dim_site(site_nk, source_system, source_site_id, site_name, region, latitude, longitude)
        SELECT DISTINCT ON (site_nk)
            site_nk, source_system, source_site_id, site_name, region, latitude, longitude
        FROM src
        ORDER BY site_nk
        ON CONFLICT (site_nk) DO UPDATE SET
            site_name = EXCLUDED.site_name,
            region = EXCLUDED.region,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
        """,
    )


# Transformasi dimensi material.
# Mengambil data material unik dari production dan mengubah ID-nya ke format angka. 
def load_dim_material(conn):
    _exec(
        conn,
        """
        INSERT INTO dim_material(material_id, material_name, material_type, unit_of_measure)
        SELECT DISTINCT ON (material_id)
            material_id::bigint,
            material_name,
            material_type,
            unit_of_measure
        FROM stg_production
        WHERE material_id::text ~ '^[0-9]+$'
        ORDER BY material_id
        ON CONFLICT (material_id) DO UPDATE SET
            material_name = EXCLUDED.material_name,
            material_type = EXCLUDED.material_type,
            unit_of_measure = EXCLUDED.unit_of_measure;
        """,
    )

# Transformasi dimensi employee.
# Data pegawai diambil dari production, lalu hire_date dikonversi menjadi tipe tanggal.
def load_dim_employee(conn):
    _exec(
        conn,
        """
        INSERT INTO dim_employee(employee_id, employee_name, position, department, status, hire_date)
        SELECT DISTINCT ON (employee_id)
            employee_id::bigint,
            employee_name,
            position,
            department,
            status,
            CASE
                WHEN trim(hire_date) ~ '^[0-9]{8}$' THEN to_date(trim(hire_date), 'YYYYMMDD')
                WHEN trim(hire_date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(hire_date), 'YYYY-MM-DD')
                ELSE NULL
            END AS hire_date
        FROM stg_production
        WHERE employee_id::text ~ '^[0-9]+$'
        ORDER BY employee_id
        ON CONFLICT (employee_id) DO UPDATE SET
            employee_name = EXCLUDED.employee_name,
            position = EXCLUDED.position,
            department = EXCLUDED.department,
            status = EXCLUDED.status,
            hire_date = EXCLUDED.hire_date;
        """,
    )

# Transformasi dimensi shift.
# Mengambil data shift unik dan mengubah jam mulai/selesai menjadi tipe time.
# Data shift digunakan untuk menganalisis produksi berdasarkan jam kerja.
def load_dim_shift(conn):
    _exec(
        conn,
        """
        INSERT INTO dim_shift(shift_id, shift_name, start_time, end_time)
        SELECT DISTINCT ON (shift_id)
            shift_id::bigint,
            shift_name,
            start_time::time,
            end_time::time
        FROM stg_production
        WHERE shift_id::text ~ '^[0-9]+$'
        ORDER BY shift_id
        ON CONFLICT (shift_id) DO UPDATE SET
            shift_name = EXCLUDED.shift_name,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time;
        """,
    )

# Transformasi dimensi project.
# Mengambil data project unik dari transaksi dan mengubah tanggal project menjadi tipe date.
def load_dim_project(conn):
    _exec(
        conn,
        """
        INSERT INTO dim_project(project_id, project_name, project_manager, status, start_date, end_date)
        SELECT DISTINCT ON (project_id)
            project_id::bigint,
            project_name,
            project_manager,
            status,
            CASE
                WHEN trim(start_date) ~ '^[0-9]{8}$' THEN to_date(trim(start_date), 'YYYYMMDD')
                WHEN trim(start_date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(start_date), 'YYYY-MM-DD')
                ELSE NULL
            END AS start_date,
            CASE
                WHEN trim(end_date) ~ '^[0-9]{8}$' THEN to_date(trim(end_date), 'YYYYMMDD')
                WHEN trim(end_date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(end_date), 'YYYY-MM-DD')
                ELSE NULL
            END AS end_date
        FROM stg_transaksi
        WHERE project_id::text ~ '^[0-9]+$'
        ORDER BY project_id
        ON CONFLICT (project_id) DO UPDATE SET
            project_name = EXCLUDED.project_name,
            project_manager = EXCLUDED.project_manager,
            status = EXCLUDED.status,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date;
        """,
    )

# Transformasi dimensi account.
# Mengambil data akun biaya unik dari transaksi dan mengubah account_id menjadi angka.
# Data account digunakan untuk mengelompokkan biaya berdasarkan jenis akun dan kategori budget.
def load_dim_account(conn):
    _exec(
        conn,
        """
        INSERT INTO dim_account(account_id, account_name, account_type, budget_category)
        SELECT DISTINCT ON (account_id)
            account_id::bigint,
            account_name,
            account_type,
            budget_category
        FROM stg_transaksi
        WHERE account_id::text ~ '^[0-9]+$'
        ORDER BY account_id
        ON CONFLICT (account_id) DO UPDATE SET
            account_name = EXCLUDED.account_name,
            account_type = EXCLUDED.account_type,
            budget_category = EXCLUDED.budget_category;
        """,
    )

# Transformasi dimensi equipment dengan konsep SCD Type 2.
# SCD Type 2 digunakan agar perubahan atribut equipment tetap memiliki histori.
# Jika data equipment berubah, record lama ditutup dan record baru dibuat sebagai versi terbaru
def load_dim_equipment_scd2(conn):
    # Mengambil data equipment unik dari staging alat berat.
    # equipment_nk dibuat dari hash nama equipment dan model agar bisa menjadi natural key.
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT
                md5(concat_ws('|', lower(trim(equipment_name)), lower(trim(model)))) AS equipment_nk,
                equipment_name,
                equipment_type,
                manufacture,
                model,
                capacity,
                CASE
                    WHEN trim(purchase_date) ~ '^[0-9]{8}$' THEN to_date(trim(purchase_date), 'YYYYMMDD')
                    WHEN trim(purchase_date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(purchase_date), 'YYYY-MM-DD')
                    ELSE NULL
                END AS purchase_date
            FROM stg_alat_berat
            WHERE equipment_name IS NOT NULL AND model IS NOT NULL
            """
        )
    ).fetchall()

    for r in rows:
        item = r._mapping
        current = conn.execute(
            text(
                """
                SELECT equipment_sk, equipment_type, manufacture, capacity, purchase_date
                FROM dim_equipment
                WHERE equipment_nk = :equipment_nk AND is_current = true
                """
            ),
            {"equipment_nk": item["equipment_nk"]},
        ).fetchone()

        params = dict(item)
        if current is None:
            conn.execute(
                text(
                    """
                    INSERT INTO dim_equipment(
                        equipment_nk, equipment_name, equipment_type, manufacture, model,
                        capacity, purchase_date, effective_from, is_current
                    ) VALUES (
                        :equipment_nk, :equipment_name, :equipment_type, :manufacture, :model,
                        :capacity, :purchase_date, CURRENT_TIMESTAMP, true
                    )
                    """
                ),
                params,
            )
            continue

        cur = current._mapping
        
        # Mengecek apakah ada perubahan pada atribut equipment.
        # Jika ada perubahan, maka SCD Type 2 akan membuat versi historis.
        changed = (
            str(cur["equipment_type"]) != str(item["equipment_type"])
            or str(cur["manufacture"]) != str(item["manufacture"])
            or str(cur["capacity"]) != str(item["capacity"])
            or str(cur["purchase_date"]) != str(item["purchase_date"])
        )

        if changed:
            conn.execute(
                text(
                    """
                    UPDATE dim_equipment
                    SET effective_to = CURRENT_TIMESTAMP, is_current = false
                    WHERE equipment_sk = :equipment_sk
                    """
                ),
                {"equipment_sk": cur["equipment_sk"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO dim_equipment(
                        equipment_nk, equipment_name, equipment_type, manufacture, model,
                        capacity, purchase_date, effective_from, is_current
                    ) VALUES (
                        :equipment_nk, :equipment_name, :equipment_type, :manufacture, :model,
                        :capacity, :purchase_date, CURRENT_TIMESTAMP, true
                    )
                    """
                ),
                params,
            )

# Transformasi dan load fact production.
# Mengubah data produksi menjadi fact table: parsing tanggal, join ke dimensi, casting angka, dan hitung production_cost.
# production_cost dihitung dari produced_volume * unit_cost.
def load_fact_production(conn):
    _exec(
        conn,
        """
        WITH p AS (
            SELECT *,
                CASE
                    WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                    WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                    ELSE NULL
                END AS full_date
            FROM stg_production
        )
        INSERT INTO fact_production(
            production_id, date_key, site_sk, material_sk, employee_sk, shift_sk,
            produced_volume, unit_cost, quantity, production_cost
        )
        SELECT
            p.production_id::bigint,
            to_char(p.full_date, 'YYYYMMDD')::int,
            s.site_sk,
            m.material_sk,
            e.employee_sk,
            sh.shift_sk,
            p.produced_volume::numeric,
            p.unit_cost::numeric,
            p.quantity::numeric,
            p.produced_volume::numeric * p.unit_cost::numeric AS production_cost
        FROM p
        JOIN dim_site s ON s.site_nk = 'PRODUCTION:' || trim(p.site_id::text)
        JOIN dim_material m ON m.material_id = p.material_id::bigint
        JOIN dim_employee e ON e.employee_id = p.employee_id::bigint
        JOIN dim_shift sh ON sh.shift_id = p.shift_id::bigint
        WHERE p.full_date IS NOT NULL
        ON CONFLICT (production_id) DO NOTHING;
        """,
    )

# Transformasi dan load fact transaction.
# Mengubah data transaksi menjadi fact table: parsing tanggal, join ke dimensi, casting biaya, dan hitung cost_variance.
def load_fact_transaction(conn):
    _exec(
        conn,
        """
        WITH t AS (
            SELECT *,
                CASE
                    WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                    WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                    ELSE NULL
                END AS full_date
            FROM stg_transaksi
        )
        INSERT INTO fact_transaction(
            transaction_id, date_key, site_sk, project_sk, account_sk,
            variance_status, budgeted_cost, actual_cost, cost, cost_variance
        )
        SELECT
            t.id::bigint,
            to_char(t.full_date, 'YYYYMMDD')::int,
            s.site_sk,
            p.project_sk,
            a.account_sk,
            t.variance,
            t.budgeted_cost::numeric,
            t.actual_cost::numeric,
            t.cost::numeric,
            t.actual_cost::numeric - t.budgeted_cost::numeric AS cost_variance
        FROM t
        JOIN dim_site s ON s.site_nk = 'TRANSACTION:' || trim(t.site_id::text)
        JOIN dim_project p ON p.project_id = t.project_id::bigint
        JOIN dim_account a ON a.account_id = t.account_id::bigint
        WHERE t.full_date IS NOT NULL
        ON CONFLICT (transaction_id) DO NOTHING;
        """,
    )

# Transformasi dan load fact equipment usage.
# Mengubah data pemakaian alat berat menjadi fact table: parsing tanggal, buat key lokasi/equipment, join dimensi, dan hitung utilization_rate.
def load_fact_equipment_usage(conn):
    _exec(
        conn,
        """
        WITH eu AS (
            SELECT *,
                CASE
                    WHEN trim(date) ~ '^[0-9]{8}$' THEN to_date(trim(date), 'YYYYMMDD')
                    WHEN trim(date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(trim(date), 'YYYY-MM-DD')
                    ELSE NULL
                END AS full_date,
                'EQUIPMENT:' || md5(concat_ws('|', lower(trim(site_name)), lower(trim(region)), latitude::text, longitude::text)) AS site_nk,
                md5(concat_ws('|', lower(trim(equipment_name)), lower(trim(model)))) AS equipment_nk
            FROM stg_alat_berat
        )
        INSERT INTO fact_equipment_usage(
            equipment_usage_id, date_key, site_sk, equipment_sk,
            operating_hours, downtime_hours, fuel_consumption, maintenance_cost, utilization_rate
        )
        SELECT
            eu.equipment_usage_id::bigint,
            to_char(eu.full_date, 'YYYYMMDD')::int,
            s.site_sk,
            eq.equipment_sk,
            eu.operating_hours::numeric,
            eu.downtime_hours::numeric,
            eu.fuel_consumption::numeric,
            eu.maintenance_cost::numeric,
            CASE
                WHEN (eu.operating_hours::numeric + eu.downtime_hours::numeric) = 0 THEN NULL
                ELSE eu.operating_hours::numeric / (eu.operating_hours::numeric + eu.downtime_hours::numeric)
            END AS utilization_rate
        FROM eu
        JOIN dim_site s ON s.site_nk = eu.site_nk
        JOIN dim_equipment eq ON eq.equipment_nk = eu.equipment_nk AND eq.is_current = true
        WHERE eu.full_date IS NOT NULL
        ON CONFLICT (equipment_usage_id) DO NOTHING;
        """,
    )
