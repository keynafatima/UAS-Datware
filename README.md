# Mining / Heavy Equipment Data Warehouse Dashboard

Project ini merupakan implementasi data warehouse untuk analisis aktivitas pertambangan dan penggunaan alat berat. Sistem ini mencakup proses ETL, penyimpanan data ke PostgreSQL/Supabase, pembentukan star schema, pembuatan semantic views untuk kebutuhan dashboard, serta visualisasi data menggunakan Streamlit.

Dashboard ini digunakan untuk menganalisis tiga area utama:

* **Production / Produksi**: volume produksi dan biaya produksi.
* **Equipment / Alat Berat**: jam operasi, downtime, konsumsi bahan bakar, utilization rate, dan biaya maintenance.
* **Financial / Keuangan**: budgeted cost, actual cost, dan cost variance.

## Tech Stack

Project ini menggunakan teknologi berikut:

* Python
* Pandas
* SQLAlchemy
* PostgreSQL / Supabase
* Streamlit
* Plotly
* Docker, opsional untuk PostgreSQL lokal

Pada versi final project ini, database utama menggunakan **Supabase PostgreSQL**, sehingga Docker tidak wajib digunakan untuk menjalankan dashboard.

## Project Structure

Struktur folder project yang disarankan:

```text
Project-UAS-1/
├── app.py
├── run_supabase_etl.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
├── .streamlit/
│   └── secrets.toml
├── data/
│   ├── dataset_alat_berat_dw.csv
│   ├── dataset_production.csv
│   └── dataset_transaksi.csv
├── etl/
│   ├── __init__.py
│   └── etl.py
├── sql/
│   ├── schema.sql
│   └── dashboard_views.sql
└── data_backup_before_2024_2025_alignment/
    ├── dataset_alat_berat_dw.csv
    ├── dataset_production.csv
    └── dataset_transaksi.csv
```

Keterangan file dan folder:

* `app.py` berisi aplikasi dashboard Streamlit.
* `run_supabase_etl.py` digunakan untuk menjalankan proses ETL ke database Supabase.
* `etl/etl.py` berisi logic Extract, Transform, dan Load.
* `sql/schema.sql` berisi struktur tabel staging, dimension, dan fact.
* `sql/dashboard_views.sql` berisi semantic views untuk kebutuhan dashboard.
* `data/` berisi dataset CSV sebagai sumber data.
* `.env` digunakan untuk konfigurasi koneksi database saat menjalankan ETL.
* `.streamlit/secrets.toml` digunakan untuk konfigurasi koneksi database pada Streamlit.
* `data_backup_before_2024_2025_alignment/` berisi backup dataset sebelum standardisasi periode data.

Folder backup bersifat opsional untuk repository final. Folder ini boleh disimpan di lokal saja dan tidak wajib diupload ke GitHub.

## Data Warehouse Design

Project ini menggunakan pendekatan **star schema** yang terdiri dari tabel dimensi dan tabel fakta.

### Dimension Tables

Tabel dimensi yang digunakan:

* `dim_date`
* `dim_site`
* `dim_material`
* `dim_employee`
* `dim_shift`
* `dim_project`
* `dim_account`
* `dim_equipment`

### Fact Tables

Tabel fakta yang digunakan:

* `fact_production`
* `fact_equipment_usage`
* `fact_transaction`

### Staging Tables

Tabel staging yang digunakan:

* `stg_alat_berat`
* `stg_production`
* `stg_transaksi`

Staging table digunakan sebagai area penampungan data mentah dari CSV sebelum ditransformasikan ke tabel dimensi dan fakta.

## ETL Process

Proses ETL pada project ini terdiri dari beberapa tahap:

1. **Extract**
   Data diambil dari file CSV pada folder `data/`.

2. **Load to Staging**
   Data CSV dimuat ke staging table di PostgreSQL/Supabase.

3. **Transform**
   Data dibersihkan, disesuaikan, dan dipetakan ke tabel dimensi dan fakta.

4. **Load to Data Warehouse**
   Hasil transformasi dimuat ke star schema, yaitu tabel dimensi dan tabel fakta.

ETL menghasilkan data warehouse yang dapat digunakan untuk analisis produksi, alat berat, dan keuangan.

## Dashboard Semantic Views

Semantic views yang digunakan untuk dashboard:

* `vw_dashboard_production_monthly`
* `vw_dashboard_equipment_monthly`
* `vw_dashboard_financial_monthly`
* `vw_dashboard_kpi_monthly`
* `vw_equipment_daily`

Penjelasan:

* `vw_dashboard_production_monthly` digunakan sebagai view pendukung untuk data produksi.
* `vw_dashboard_equipment_monthly` digunakan sebagai view pendukung untuk data penggunaan alat berat.
* `vw_dashboard_financial_monthly` digunakan sebagai view pendukung untuk data keuangan.
* `vw_dashboard_kpi_monthly` digunakan sebagai view utama untuk dashboard bulanan.
* `vw_equipment_daily` digunakan sebagai detail tambahan untuk analisis equipment secara harian.

Dashboard utama menggunakan `vw_dashboard_kpi_monthly` agar visualisasi lebih ringkas, konsisten, dan mudah dibaca secara bulanan. View `vw_equipment_daily` tetap disediakan sebagai data detail atau drill-down, tetapi bukan sumber utama grafik dashboard.

## Data Period Standardization

Dataset awal memiliki cakupan waktu yang berbeda antar subject area. Agar production, equipment, dan financial dapat dianalisis dalam periode yang konsisten, tanggal pada dataset distandardisasi ke rentang historis:

```text
2024-01-01 sampai 2025-12-31
```

Standardisasi ini dilakukan pada atribut waktu seperti:

* `date`
* `time_id`
* `day`
* `month`
* `year`
* `day_name`

Nilai bisnis seperti produced volume, operating hours, downtime hours, fuel consumption, maintenance cost, budgeted cost, actual cost, dan cost variance tetap dipertahankan.

Tujuan standardisasi ini adalah agar metrik production, equipment, dan financial dapat dianalisis dalam periode yang sama dan tidak menghasilkan interpretasi lintas waktu yang keliru.

## Setup Project

### 1. Clone Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Buat Virtual Environment

Untuk Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Untuk macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Isi minimal `requirements.txt`:

```txt
streamlit
pandas
plotly
sqlalchemy
psycopg2-binary
python-dotenv
```

## Database Configuration

Project ini dapat menggunakan PostgreSQL lokal atau Supabase. Untuk versi final dan deployment, Supabase lebih disarankan karena database dapat diakses secara online tanpa menjalankan Docker lokal.

### Environment Variable untuk ETL

Buat file `.env` di root project:

```env
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=postgres
```

Jika menggunakan Supabase connection pooler, isi `DB_USER`, `DB_HOST`, dan `DB_PORT` sesuai connection string dari Supabase.

### Streamlit Secrets

Buat folder `.streamlit`, lalu buat file `secrets.toml` di dalamnya:

```toml
[database]
user = "your_database_user"
password = "your_database_password"
host = "your_database_host"
port = 5432
dbname = "postgres"
```

File `.env` dan `.streamlit/secrets.toml` tidak boleh diupload ke GitHub karena berisi credential database.

Tambahkan ke `.gitignore`:

```gitignore
.env
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
data_backup_before_2024_2025_alignment/
```

## Database Setup

### 1. Jalankan Schema

Jalankan isi file berikut di Supabase SQL Editor atau PostgreSQL client:

```text
sql/schema.sql
```

File ini akan membuat tabel staging, dimension, dan fact.

### 2. Jalankan ETL

Setelah schema dibuat, jalankan ETL:

```bash
python run_supabase_etl.py
```

ETL akan melakukan proses:

1. Membaca data dari CSV.
2. Memuat data ke staging table.
3. Membentuk dimension table.
4. Membentuk fact table.
5. Menghasilkan data warehouse yang siap digunakan dashboard.

Jika ETL berhasil, output akan menunjukkan bahwa staging, dimension, dan fact table sudah terisi.

### 3. Jalankan Dashboard Views

Setelah ETL selesai, jalankan isi file berikut di Supabase SQL Editor:

```text
sql/dashboard_views.sql
```

File ini akan membuat view:

```text
vw_dashboard_production_monthly
vw_dashboard_equipment_monthly
vw_dashboard_financial_monthly
vw_dashboard_kpi_monthly
vw_equipment_daily
```

## Validation Query

Setelah ETL dan dashboard views berhasil dijalankan, lakukan validasi data.

### 1. Cek Cakupan Tanggal Setiap Subject Area

```sql
SELECT
  'production' AS subject_area,
  MIN(d.full_date) AS start_date,
  MAX(d.full_date) AS end_date,
  COUNT(*) AS total_rows
FROM fact_production f
JOIN dim_date d ON f.date_key = d.date_key

UNION ALL

SELECT
  'equipment' AS subject_area,
  MIN(d.full_date) AS start_date,
  MAX(d.full_date) AS end_date,
  COUNT(*) AS total_rows
FROM fact_equipment_usage f
JOIN dim_date d ON f.date_key = d.date_key

UNION ALL

SELECT
  'financial' AS subject_area,
  MIN(d.full_date) AS start_date,
  MAX(d.full_date) AS end_date,
  COUNT(*) AS total_rows
FROM fact_transaction f
JOIN dim_date d ON f.date_key = d.date_key;
```

Target hasil:

```text
production   2024-01-01   2025-12-31
equipment    2024-01-01   2025-12-31
financial    2024-01-01   2025-12-31
```

### 2. Cek View Dashboard Utama

```sql
SELECT
  subject_area,
  MIN(year) AS min_year,
  MAX(year) AS max_year,
  COUNT(*) AS total_aggregated_rows
FROM vw_dashboard_kpi_monthly
GROUP BY subject_area
ORDER BY subject_area;
```

Target hasil minimal:

```text
production   2024   2025
equipment    2024   2025
financial    2024   2025
```

### 3. Cek Detail Equipment Daily

```sql
SELECT
  MIN(full_date) AS start_date,
  MAX(full_date) AS end_date,
  COUNT(*) AS total_daily_rows
FROM vw_equipment_daily;
```

Target rentang tanggal:

```text
2024-01-01 sampai 2025-12-31
```

### 4. Cek Tidak Ada View Lama yang Tidak Relevan

```sql
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name ILIKE '%tableau%'
ORDER BY table_name;
```

Target hasil:

```text
0 rows
```

## Run Streamlit Dashboard

Jalankan dashboard dengan command:

```bash
streamlit run app.py
```

Dashboard akan terbuka di browser melalui alamat lokal, biasanya:

```text
http://localhost:8501
```

Jika dashboard masih menampilkan data lama, bersihkan cache terlebih dahulu:

```bash
streamlit cache clear
streamlit run app.py
```

## Dashboard Features

### 1. Overview / Ringkasan

Menampilkan ringkasan KPI utama:

* Produced Volume / Volume Produksi
* Production Cost / Biaya Produksi
* Downtime Hours / Jam Downtime
* Actual Cost / Biaya Aktual
* Utilization Rate / Tingkat Pemanfaatan Alat
* Cost Variance / Selisih Biaya

Overview digunakan untuk membaca kondisi umum production, equipment, dan financial dalam periode yang dipilih.

### 2. Production / Produksi

Menampilkan analisis produksi bulanan:

* Total produced volume
* Total production cost
* Average cost per volume
* Monthly produced volume trend
* Monthly production cost trend
* Produced volume by region

Bagian ini membantu melihat apakah peningkatan volume produksi juga diikuti efisiensi biaya produksi.

### 3. Equipment / Alat Berat

Menampilkan analisis alat berat secara bulanan:

* Operating hours
* Downtime hours
* Utilization rate
* Downtime ratio
* Fuel consumption
* Maintenance cost
* Monthly downtime trend
* Monthly operating hours trend
* Monthly maintenance cost trend

Data harian equipment tetap tersedia pada Data View melalui `vw_equipment_daily`.

### 4. Financial / Keuangan

Menampilkan analisis keuangan:

* Budgeted cost
* Actual cost
* Cost variance
* Monthly cost variance trend
* Budgeted cost vs actual cost

Bagian ini digunakan untuk melihat apakah actual cost berada di atas atau di bawah budgeted cost.

### 5. Data View / Tabel

Menampilkan data dalam bentuk tabel:

* Production Data
* Equipment Monthly Data
* Equipment Daily Detail
* Financial Data
* Monthly Raw View

Data View disediakan agar pengguna dapat melihat data agregasi dan detail yang digunakan oleh dashboard.

## Important Notes

* Dashboard utama menggunakan view bulanan agar visualisasi lebih rapi dan mudah dibaca.
* View harian equipment digunakan sebagai data detail tambahan, bukan sebagai sumber grafik utama.
* Grafik harian untuk rentang dua tahun dapat menjadi terlalu padat, sehingga grafik utama equipment dibuat dalam bentuk bulanan.
* Nilai `None` pada monthly raw view bukan error. Hal tersebut terjadi karena view utama menggabungkan beberapa subject area dalam satu struktur tabel. Kolom yang tidak relevan untuk subject area tertentu akan bernilai kosong.
* Manual SQL query tidak disediakan pada dashboard deploy untuk menjaga keamanan database.
* Nama view sudah disesuaikan ke konteks dashboard/Streamlit dan tidak lagi menggunakan istilah tools visualisasi tertentu.

## Docker Notes

Pada versi awal, Docker dapat digunakan untuk menjalankan PostgreSQL lokal. Namun pada versi final, project ini menggunakan Supabase sebagai database utama.

Flow final project:

```text
CSV → Python ETL → Supabase PostgreSQL → Streamlit Dashboard
```

Karena itu, Docker bersifat opsional. Dashboard tetap dapat berjalan tanpa Docker selama Supabase sudah berisi data dan file `.env` serta `.streamlit/secrets.toml` sudah benar.

Jika ingin memeriksa penggunaan storage Docker:

```bash
docker system df -v
```

Jika ingin melihat image yang tersimpan:

```bash
docker images -a
```

Jika ingin melihat volume Docker:

```bash
docker volume ls
```

Jika data sudah aman di Supabase dan Docker lokal tidak digunakan lagi, Docker container dan volume lokal dapat dihapus sesuai kebutuhan.

## Deployment Notes

Jika dashboard dideploy menggunakan Streamlit Community Cloud:

1. Upload source code ke GitHub.
2. Jangan upload `.env` dan `.streamlit/secrets.toml`.
3. Masukkan database secrets melalui menu Streamlit Cloud.
4. Pastikan database Supabase aktif dan dapat diakses dari internet.
5. Pastikan `requirements.txt` sudah lengkap.
6. Pastikan `app.py` membaca view `vw_dashboard_kpi_monthly`.

Contoh secrets di Streamlit Cloud:

```toml
[database]
user = "your_database_user"
password = "your_database_password"
host = "your_database_host"
port = 5432
dbname = "postgres"
```

## Troubleshooting

### 1. Error: `relation "vw_dashboard_kpi_monthly" does not exist`

Artinya view dashboard utama belum dibuat atau nama view di database tidak sesuai dengan nama yang dipanggil di `app.py`.

Solusi:

* Jalankan ulang `sql/dashboard_views.sql`.
* Pastikan `app.py` membaca `vw_dashboard_kpi_monthly`.

### 2. Error: `relation "vw_equipment_daily" does not exist`

Artinya view detail equipment harian belum dibuat.

Solusi:

* Pastikan query pembuatan `vw_equipment_daily` sudah ada di `sql/dashboard_views.sql`.
* Jalankan ulang file view di Supabase SQL Editor.

### 3. Error: `password authentication failed`

Artinya credential database salah.

Solusi:

* Cek kembali `.env` untuk ETL.
* Cek kembali `.streamlit/secrets.toml` untuk dashboard.
* Pastikan user, password, host, port, dan dbname sesuai dengan Supabase.

### 4. Error: data dashboard masih data lama

Streamlit mungkin masih menyimpan cache.

Solusi:

```bash
streamlit cache clear
streamlit run app.py
```

### 5. Data tidak muncul setelah ETL

Cek isi fact table:

```sql
SELECT COUNT(*) FROM fact_production;
SELECT COUNT(*) FROM fact_equipment_usage;
SELECT COUNT(*) FROM fact_transaction;
```

Lalu cek view utama:

```sql
SELECT subject_area, COUNT(*)
FROM vw_dashboard_kpi_monthly
GROUP BY subject_area;
```

### 6. Ada nama view lama yang masih muncul

Cek dengan query:

```sql
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name ILIKE '%tableau%'
ORDER BY table_name;
```

Jika masih ada hasil, rename atau hapus view tersebut sesuai kebutuhan agar naming project tetap konsisten.

## Author

Project ini dibuat sebagai implementasi Data Warehouse untuk analisis mining dan heavy equipment menggunakan ETL, PostgreSQL/Supabase, dan Streamlit Dashboard.
