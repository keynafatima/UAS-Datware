import os
from dotenv import load_dotenv

# Ganti import ini sesuai lokasi file ETL kamu
# Misalnya kalau file ETL kamu ada di etl/etl.py:
from etl.etl import run_etl

load_dotenv()

db = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "db": os.getenv("DB_NAME"),
}

run_etl(db, data_dir="data")