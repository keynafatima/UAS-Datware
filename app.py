import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# =========================================================
# Page Configuration
# =========================================================
st.set_page_config(
    page_title="Mining Data Warehouse Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# Styling
# =========================================================
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.3rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
        border-right: 1px solid #dbeafe;
    }

    .dashboard-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: #0f172a;
    }

    .dashboard-subtitle {
        color: #475569;
        font-size: 1rem;
        line-height: 1.65;
        margin-bottom: 1rem;
    }

    .section-note {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        line-height: 1.65;
        color: #334155;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.92rem;
        color: #475569;
    }

    .metric-translation {
        color: #64748b;
        font-size: 0.84rem;
        margin-top: -0.35rem;
        margin-bottom: 0.5rem;
    }

    .small-caption {
        color: #64748b;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .insight-box {
        background-color: #f8fafc;
        border-left: 5px solid #2563eb;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        line-height: 1.65;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .warning-box {
        background-color: #fff7ed;
        border-left: 5px solid #f97316;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        line-height: 1.65;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .good-box {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        line-height: 1.65;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .neutral-box {
        background-color: #f1f5f9;
        border-left: 5px solid #64748b;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        line-height: 1.65;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .sidebar-note {
        font-size: 0.86rem;
        color: #475569;
        line-height: 1.45;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
        margin-bottom: 0.7rem;
    }

    .term-pill {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 0.15rem 0.55rem;
        font-size: 0.82rem;
        margin: 0.1rem 0.15rem 0.1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Database Connection
# =========================================================
db = st.secrets["database"]

DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username=db["user"],
    password=db["password"],
    host=db["host"],
    port=int(db["port"]),
    database=db["dbname"],
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)


# =========================================================
# Dictionaries
# =========================================================
SUBJECT_LABELS = {
    "production": "Produksi (Production)",
    "equipment": "Alat Berat (Equipment)",
    "financial": "Keuangan/Biaya (Financial)",
}

REGION_LABELS = {
    "East": "East / Timur",
    "West": "West / Barat",
    "North": "North / Utara",
    "South": "South / Selatan",
    "Kalimantan": "Kalimantan",
    "Papua": "Papua",
    "Sumatera": "Sumatera",
    "Sulawesi": "Sulawesi",
    "Maluku": "Maluku",
}

METRIC_EXPLANATIONS = {
    "Produced Volume": "Volume produksi yang dihasilkan.",
    "Production Cost": "Total biaya produksi.",
    "Avg Cost per Volume": "Rata-rata biaya untuk menghasilkan satu satuan volume produksi.",
    "Operating Hours": "Total jam alat berat beroperasi.",
    "Downtime Hours": "Total jam alat berat berhenti/tidak beroperasi.",
    "Fuel Consumption": "Total konsumsi bahan bakar alat berat.",
    "Maintenance Cost": "Total biaya perawatan alat berat.",
    "Utilization Rate": "Tingkat pemanfaatan alat: jam operasi dibandingkan total waktu alat.",
    "Downtime Ratio": "Porsi jam downtime dibandingkan total waktu alat.",
    "Budgeted Cost": "Biaya yang direncanakan/dianggarkan.",
    "Actual Cost": "Biaya aktual yang benar-benar terjadi.",
    "Cost Variance": "Selisih actual cost dan budgeted cost. Nilai positif menunjukkan actual cost lebih besar dari budget.",
}


# =========================================================
# Data Loading
# =========================================================
@st.cache_data(ttl=600)
def load_monthly_data():
    return pd.read_sql("SELECT * FROM vw_dashboard_kpi_monthly;", engine)


@st.cache_data(ttl=600)
def load_equipment_daily_data():
    return pd.read_sql("SELECT * FROM vw_equipment_daily;", engine)


# =========================================================
# Helper Functions
# =========================================================
def format_number(value):
    if pd.isna(value):
        return "0"
    return f"{value:,.0f}"


def format_decimal(value, digits=2):
    if pd.isna(value):
        return "0.00"
    return f"{value:,.{digits}f}"


def format_percent(value):
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2%}"


def safe_sum(dataframe, column):
    if column in dataframe.columns and not dataframe.empty:
        return pd.to_numeric(dataframe[column], errors="coerce").sum()
    return 0


def safe_mean(dataframe, column):
    if column in dataframe.columns and not dataframe.empty:
        return pd.to_numeric(dataframe[column], errors="coerce").mean()
    return 0


def safe_nunique(dataframe, column):
    if column in dataframe.columns and not dataframe.empty:
        return dataframe[column].dropna().nunique()
    return 0


def available_columns(dataframe, columns):
    return [column for column in columns if column in dataframe.columns]


def subject_format(value):
    return SUBJECT_LABELS.get(value, value)


def region_format(value):
    return REGION_LABELS.get(value, value)


def label_or_all(values, label_map=None):
    if not values:
        return "Tidak ada"
    label_map = label_map or {}
    return ", ".join(label_map.get(value, str(value)) for value in values)


def create_period_column(dataframe):
    dataframe = dataframe.copy()
    dataframe["year"] = pd.to_numeric(dataframe["year"], errors="coerce").astype("Int64")
    dataframe["month"] = pd.to_numeric(dataframe["month"], errors="coerce").astype("Int64")
    dataframe = dataframe.sort_values(["year", "month"])
    dataframe["period"] = dataframe["year"].astype(str) + "-" + dataframe["month"].astype(str).str.zfill(2)
    dataframe["period_label"] = dataframe["month_name"].astype(str) + " " + dataframe["year"].astype(str)
    return dataframe


def plot_chart(fig, key, height=420, force_category=True):
    fig.update_layout(
        margin=dict(l=20, r=20, t=58, b=35),
        height=height,
        legend_title_text="",
        hovermode="x unified"
    )
    if force_category:
        fig.update_xaxes(type="category", title=None)
    st.plotly_chart(fig, use_container_width=True, key=key)


def show_empty_message(section_name):
    st.warning(f"Tidak ada data untuk bagian {section_name} berdasarkan filter yang dipilih.")


def metric_card(label, value, translation=None, help_text=None):
    st.metric(label, value, help=help_text)
    if translation:
        st.markdown(f"<div class='metric-translation'>{translation}</div>", unsafe_allow_html=True)


def interpretation_box(message, box_type="info"):
    css_class = {
        "info": "insight-box",
        "warning": "warning-box",
        "good": "good-box",
        "neutral": "neutral-box",
    }.get(box_type, "insight-box")
    st.markdown(f"<div class='{css_class}'>{message}</div>", unsafe_allow_html=True)


def time_series_interpretation(dataframe, time_label_col, metric_col, metric_label_id, unit_label="", is_percent=False):
    """Kritis: jangan menyimpulkan tren jika titik waktu hanya 1."""
    if dataframe.empty or metric_col not in dataframe.columns or time_label_col not in dataframe.columns:
        return

    temp = dataframe[[time_label_col, metric_col]].copy()
    temp[metric_col] = pd.to_numeric(temp[metric_col], errors="coerce")
    temp = temp.dropna(subset=[metric_col])

    if temp.empty:
        return

    number_of_periods = temp[time_label_col].nunique()
    total_value = temp[metric_col].sum()
    top_row = temp.loc[temp[metric_col].idxmax()]

    def metric_value(value):
        if is_percent:
            return format_percent(value)
        return f"{format_number(value)} {unit_label}".strip()

    if number_of_periods == 1:
        interpretation_box(
            f"<b>Interpretasi:</b> Data {metric_label_id} hanya tersedia untuk <b>1 periode</b>, yaitu "
            f"<b>{top_row[time_label_col]}</b> dengan nilai <b>{metric_value(top_row[metric_col])}</b>. "
            f"Karena hanya ada satu titik waktu, dashboard <b>tidak menyimpulkan tren naik/turun</b>. "
            f"Analisis yang lebih tepat adalah membandingkan metrik ini dengan region, site, atau alat tertentu.",
            box_type="neutral"
        )
        return

    low_row = temp.loc[temp[metric_col].idxmin()]
    first_value = temp.iloc[0][metric_col]
    last_value = temp.iloc[-1][metric_col]
    change = last_value - first_value
    change_pct = change / first_value if first_value else None
    top_share = top_row[metric_col] / total_value if total_value else 0

    if change > 0:
        trend_text = f"Nilai terakhir lebih tinggi dari nilai awal sebesar <b>{metric_value(change)}</b>"
        if change_pct is not None:
            trend_text += f" atau <b>{format_percent(change_pct)}</b>"
        trend_text += "."
    elif change < 0:
        trend_text = f"Nilai terakhir lebih rendah dari nilai awal sebesar <b>{metric_value(abs(change))}</b>"
        if change_pct is not None:
            trend_text += f" atau <b>{format_percent(abs(change_pct))}</b>"
        trend_text += "."
    else:
        trend_text = "Nilai awal dan nilai terakhir sama, sehingga tidak ada perubahan bersih pada periode terpilih."

    interpretation_box(
        f"<b>Interpretasi:</b> {metric_label_id} tertinggi terjadi pada <b>{top_row[time_label_col]}</b> sebesar "
        f"<b>{metric_value(top_row[metric_col])}</b>, menyumbang sekitar <b>{format_percent(top_share)}</b> dari total. "
        f"Nilai terendah terjadi pada <b>{low_row[time_label_col]}</b> sebesar <b>{metric_value(low_row[metric_col])}</b>. "
        f"{trend_text} Perubahan ini bersifat deskriptif dari data, sehingga penyebabnya tetap perlu ditelusuri melalui data operasional yang lebih detail.",
        box_type="info"
    )


def region_concentration_interpretation(dataframe, metric_col, metric_label_id, unit_label=""):
    if dataframe.empty or metric_col not in dataframe.columns:
        return

    temp = dataframe.groupby("region", as_index=False)[metric_col].sum()
    temp = temp.dropna(subset=[metric_col])
    if temp.empty:
        return

    top_row = temp.loc[temp[metric_col].idxmax()]
    total_value = temp[metric_col].sum()
    share = top_row[metric_col] / total_value if total_value else 0

    if share > 0.5:
        message = (
            f"Region <b>{top_row['region']}</b> menyumbang lebih dari separuh total {metric_label_id}, "
            f"yaitu <b>{format_percent(share)}</b>. Artinya metrik ini cukup terkonsentrasi pada satu wilayah."
        )
        box_type = "warning"
    else:
        message = (
            f"Region terbesar adalah <b>{top_row['region']}</b> dengan kontribusi <b>{format_percent(share)}</b>. "
            f"Kontribusi belum melewati 50%, sehingga distribusinya relatif tidak sepenuhnya terpusat pada satu wilayah."
        )
        box_type = "info"

    interpretation_box(
        f"<b>Interpretasi wilayah:</b> {message} Total {metric_label_id} pada region tersebut adalah "
        f"<b>{format_number(top_row[metric_col])} {unit_label}</b>. Analisis lanjutan perlu membedakan apakah nilai tinggi disebabkan oleh volume aktivitas yang besar atau oleh inefisiensi.",
        box_type=box_type
    )


def explain_equipment_condition(operating_hours, downtime_hours, maintenance_cost, fuel_consumption):
    total_time = operating_hours + downtime_hours
    utilization = operating_hours / total_time if total_time else 0
    downtime_ratio = downtime_hours / total_time if total_time else 0
    maintenance_per_operating_hour = maintenance_cost / operating_hours if operating_hours else 0
    fuel_per_operating_hour = fuel_consumption / operating_hours if operating_hours else 0

    if total_time == 0:
        interpretation_box(
            "<b>Interpretasi equipment:</b> Total waktu alat bernilai 0, sehingga utilization rate dan downtime ratio tidak dapat dihitung.",
            box_type="neutral"
        )
        return

    if downtime_ratio >= 0.30:
        status = "warning"
        ratio_sentence = "Porsi downtime sangat besar dalam data terfilter, sehingga ketersediaan alat perlu menjadi fokus evaluasi."
    elif downtime_ratio >= 0.10:
        status = "warning"
        ratio_sentence = "Porsi downtime cukup terlihat dalam data terfilter. Ini belum otomatis berarti buruk, tetapi perlu dibandingkan dengan target operasional."
    else:
        status = "good"
        ratio_sentence = "Porsi downtime relatif kecil dibandingkan total waktu alat pada data terfilter."

    interpretation_box(
        f"<b>Interpretasi equipment:</b> Total jam operasi adalah <b>{format_number(operating_hours)} jam</b>, "
        f"sedangkan downtime adalah <b>{format_number(downtime_hours)} jam</b>. "
        f"Dari kombinasi tersebut, utilization rate adalah <b>{format_percent(utilization)}</b> dan downtime ratio adalah <b>{format_percent(downtime_ratio)}</b>. "
        f"{ratio_sentence}<br><br>"
        f"Biaya maintenance per jam operasi adalah <b>{format_decimal(maintenance_per_operating_hour)}</b>, "
        f"sedangkan konsumsi bahan bakar per jam operasi adalah <b>{format_decimal(fuel_per_operating_hour)}</b>. "
        f"Jika downtime dan biaya maintenance sama-sama tinggi pada alat atau site tertentu, maka bagian tersebut layak dijadikan prioritas investigasi.",
        box_type=status
    )


def explain_financial_condition(total_budgeted_cost, total_actual_cost, total_cost_variance):
    variance_ratio = total_cost_variance / total_budgeted_cost if total_budgeted_cost else None

    if total_budgeted_cost == 0:
        interpretation_box(
            "<b>Interpretasi financial:</b> Budgeted cost bernilai 0, sehingga rasio variance terhadap budget tidak dapat dihitung. "
            "Dashboard hanya menampilkan nilai actual cost dan cost variance sebagai angka absolut.",
            box_type="neutral"
        )
        return

    if total_cost_variance > 0:
        status = "warning"
        message = (
            f"Actual cost lebih besar daripada budgeted cost sebesar <b>{format_number(total_cost_variance)}</b> "
            f"atau <b>{format_percent(variance_ratio)}</b> dari budget. Ini menunjukkan kondisi <b>over budget</b> pada data terfilter. "
            f"Perlu dicek apakah pembengkakan biaya terkonsentrasi pada bulan atau region tertentu."
        )
    elif total_cost_variance < 0:
        status = "good"
        message = (
            f"Actual cost lebih rendah daripada budgeted cost sebesar <b>{format_number(abs(total_cost_variance))}</b> "
            f"atau <b>{format_percent(abs(variance_ratio))}</b> dari budget. Ini terlihat efisien, tetapi tetap perlu dibandingkan dengan output produksi agar tidak keliru membaca penurunan biaya sebagai efisiensi."
        )
    else:
        status = "info"
        message = "Actual cost sama dengan budgeted cost, sehingga biaya berjalan sesuai anggaran pada data terfilter."

    interpretation_box(f"<b>Interpretasi financial:</b> {message}", box_type=status)


def monthly_chart(dataframe, x_col, y_col, title, key, chart_type="line"):
    if dataframe.empty:
        return
    if dataframe[x_col].nunique() <= 1 or chart_type == "bar":
        fig = px.bar(dataframe, x=x_col, y=y_col, text_auto=True, title=title)
    else:
        fig = px.line(dataframe, x=x_col, y=y_col, markers=True, title=title)
    plot_chart(fig, key, force_category=True)


def daily_chart(dataframe, date_col, y_col, title, key, chart_type="line"):
    if dataframe.empty:
        return

    temp = dataframe.copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col])
    if temp.empty:
        return

    temp = temp.sort_values(date_col)
    temp["date_label"] = temp[date_col].dt.strftime("%d %b %Y")

    if temp[date_col].nunique() <= 1 or chart_type == "bar":
        fig = px.bar(temp, x="date_label", y=y_col, text_auto=True, title=title)
        plot_chart(fig, key, force_category=True)
    else:
        fig = px.line(temp, x=date_col, y=y_col, markers=True, title=title)
        fig.update_xaxes(title=None)
        plot_chart(fig, key, force_category=False)


# =========================================================
# Load and Prepare Data
# =========================================================
monthly_df = load_monthly_data()

try:
    equipment_daily_df = load_equipment_daily_data()
except Exception as exc:
    st.error("View `vw_equipment_daily` belum bisa dibaca. Pastikan view tersebut sudah dibuat di Supabase.")
    st.exception(exc)
    st.stop()

monthly_numeric_cols = [
    "year", "month", "quarter",
    "total_produced_volume",
    "total_production_cost",
    "total_operating_hours",
    "total_downtime_hours",
    "total_fuel_consumption",
    "total_maintenance_cost",
    "avg_utilization_rate",
    "total_budgeted_cost",
    "total_actual_cost",
    "total_cost_variance",
]

daily_numeric_cols = [
    "year", "month", "quarter",
    "total_operating_hours",
    "total_downtime_hours",
    "total_fuel_consumption",
    "total_maintenance_cost",
    "utilization_rate",
    "downtime_ratio",
]

for col in monthly_numeric_cols:
    if col in monthly_df.columns:
        monthly_df[col] = pd.to_numeric(monthly_df[col], errors="coerce")

for col in daily_numeric_cols:
    if col in equipment_daily_df.columns:
        equipment_daily_df[col] = pd.to_numeric(equipment_daily_df[col], errors="coerce")

if "full_date" in equipment_daily_df.columns:
    equipment_daily_df["full_date"] = pd.to_datetime(equipment_daily_df["full_date"], errors="coerce")


# =========================================================
# Header
# =========================================================
st.markdown("<div class='dashboard-title'>Mining / Heavy Equipment Data Warehouse Dashboard</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='dashboard-subtitle'>
    Dashboard ini menampilkan hasil pengolahan <b>data warehouse</b> untuk aktivitas pertambangan dan alat berat.
    View bulanan <code>vw_dashboard_kpi_monthly</code> digunakan sebagai sumber utama dashboard agar Production, Equipment, dan Financial berada pada level analisis yang konsisten.
    View harian <code>vw_equipment_daily</code> tetap disediakan sebagai detail/drill-down pada Data View, bukan sebagai grafik utama.
    Istilah Inggris tetap ditampilkan karena umum dalam konteks data warehouse, tetapi selalu diberi padanan Bahasa Indonesia.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='section-note'>
    <b>Area analisis:</b><br>
    <span class='term-pill'>Production / Produksi</span> volume produksi dan biaya produksi.<br>
    <span class='term-pill'>Equipment / Alat Berat</span> jam operasi, downtime, bahan bakar, dan biaya maintenance.<br>
    <span class='term-pill'>Financial / Keuangan</span> anggaran biaya, biaya aktual, dan selisih biaya.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Sidebar Filters
# =========================================================
with st.sidebar:
    st.markdown("## Filter Dashboard")
    st.markdown(
        "<div class='sidebar-note'>Filter utama berlaku untuk seluruh dashboard. "
        "Grafik utama menggunakan view bulanan agar Production, Equipment, dan Financial dibaca pada level waktu yang sama.</div>",
        unsafe_allow_html=True
    )

    subject_options = sorted(monthly_df["subject_area"].dropna().unique().tolist())
    selected_subject = st.multiselect(
        "Area Analisis",
        subject_options,
        default=subject_options,
        format_func=subject_format,
        help="Production = Produksi, Equipment = Alat Berat, Financial = Keuangan/Biaya."
    )

    year_options = sorted(monthly_df["year"].dropna().astype(int).unique().tolist())
    selected_year = st.multiselect(
        "Tahun (Year)",
        year_options,
        default=year_options,
        help="Pilih tahun data yang ingin dianalisis."
    )

    region_options = sorted(monthly_df["region"].dropna().unique().tolist())
    selected_region = st.multiselect(
        "Wilayah Operasional (Region)",
        region_options,
        default=region_options,
        format_func=region_format,
        help="Pilih region/wilayah yang ingin dibandingkan."
    )

    st.divider()
    st.markdown("### Ringkasan Filter")
    st.write(f"Area dipilih: **{len(selected_subject)}** dari **{len(subject_options)}**")
    st.write(f"Tahun dipilih: **{len(selected_year)}** dari **{len(year_options)}**")
    st.write(f"Region dipilih: **{len(selected_region)}** dari **{len(region_options)}**")

    with st.expander("Panduan istilah"):
        st.markdown(
            """
            - **Produced Volume** = volume produksi.
            - **Production Cost** = biaya produksi.
            - **Operating Hours** = jam alat beroperasi.
            - **Downtime Hours** = jam alat berhenti/tidak beroperasi.
            - **Utilization Rate** = operating hours / (operating hours + downtime hours).
            - **Downtime Ratio** = downtime hours / (operating hours + downtime hours).
            - **Fuel Consumption** = konsumsi bahan bakar.
            - **Maintenance Cost** = biaya perawatan.
            - **Budgeted Cost** = biaya yang direncanakan.
            - **Actual Cost** = biaya aktual yang terjadi.
            - **Cost Variance** = actual cost - budgeted cost.
            """
        )


# =========================================================
# Apply Filters
# =========================================================
filtered_monthly_df = monthly_df[
    (monthly_df["subject_area"].isin(selected_subject)) &
    (monthly_df["year"].isin(selected_year)) &
    (monthly_df["region"].isin(selected_region))
].copy()

df_production = filtered_monthly_df[filtered_monthly_df["subject_area"] == "production"].copy()
df_financial = filtered_monthly_df[filtered_monthly_df["subject_area"] == "financial"].copy()
df_equipment_monthly = filtered_monthly_df[filtered_monthly_df["subject_area"] == "equipment"].copy()

filtered_equipment_daily = equipment_daily_df.copy()

if "year" in filtered_equipment_daily.columns:
    filtered_equipment_daily = filtered_equipment_daily[filtered_equipment_daily["year"].isin(selected_year)]

if "region" in filtered_equipment_daily.columns:
    filtered_equipment_daily = filtered_equipment_daily[filtered_equipment_daily["region"].isin(selected_region)]

if "equipment" not in selected_subject:
    filtered_equipment_daily = filtered_equipment_daily.iloc[0:0]
    df_equipment_monthly = df_equipment_monthly.iloc[0:0]


# =========================================================
# Executive KPI Summary
# =========================================================
st.subheader("Executive KPI Summary / Ringkasan KPI Utama")

total_produced_volume = safe_sum(df_production, "total_produced_volume")
total_production_cost = safe_sum(df_production, "total_production_cost")
total_operating_hours = safe_sum(df_equipment_monthly, "total_operating_hours")
total_downtime_hours = safe_sum(df_equipment_monthly, "total_downtime_hours")
total_actual_cost = safe_sum(df_financial, "total_actual_cost")

col1, col2, col3, col4 = st.columns(4)

with col1:
    metric_card("Produced Volume", format_number(total_produced_volume), "Volume Produksi", METRIC_EXPLANATIONS["Produced Volume"])

with col2:
    metric_card("Production Cost", format_number(total_production_cost), "Biaya Produksi", METRIC_EXPLANATIONS["Production Cost"])

with col3:
    metric_card("Downtime Hours", format_number(total_downtime_hours), "Jam Downtime Alat", METRIC_EXPLANATIONS["Downtime Hours"])

with col4:
    metric_card("Actual Cost", format_number(total_actual_cost), "Biaya Aktual", METRIC_EXPLANATIONS["Actual Cost"])

interpretation_box(
    f"<b>Ringkasan:</b> Berdasarkan filter yang dipilih, total produksi mencapai "
    f"<b>{format_number(total_produced_volume)}</b> dengan total biaya produksi "
    f"<b>{format_number(total_production_cost)}</b>. Total downtime alat berat tercatat "
    f"<b>{format_number(total_downtime_hours)} jam</b>, sedangkan total actual cost pada data financial adalah "
    f"<b>{format_number(total_actual_cost)}</b>. Seluruh KPI utama ini diambil dari view bulanan, sehingga level waktu antar-area tetap konsisten."
)

st.divider()


# =========================================================
# Tabs
# =========================================================
tab_overview, tab_prod, tab_eq, tab_fin, tab_data = st.tabs(
    ["Overview / Ringkasan", "Production / Produksi", "Equipment / Alat Berat", "Financial / Keuangan", "Data View / Tabel"]
)


# =========================================================
# Overview Tab
# =========================================================
with tab_overview:
    st.subheader("Executive Overview / Ringkasan Eksekutif")

    total_budgeted_cost = safe_sum(df_financial, "total_budgeted_cost")
    total_cost_variance = safe_sum(df_financial, "total_cost_variance")
    avg_prod_cost = total_production_cost / total_produced_volume if total_produced_volume else 0
    utilization_rate = total_operating_hours / (total_operating_hours + total_downtime_hours) if (total_operating_hours + total_downtime_hours) else 0

    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    with overview_col1:
        metric_card("Avg Cost / Volume", format_decimal(avg_prod_cost), "Rata-rata biaya per volume", METRIC_EXPLANATIONS["Avg Cost per Volume"])
    with overview_col2:
        metric_card("Utilization Rate", format_percent(utilization_rate), "Tingkat pemanfaatan alat", METRIC_EXPLANATIONS["Utilization Rate"])
    with overview_col3:
        metric_card("Budgeted Cost", format_number(total_budgeted_cost), "Biaya yang direncanakan", METRIC_EXPLANATIONS["Budgeted Cost"])
    with overview_col4:
        metric_card("Cost Variance", format_number(total_cost_variance), "Selisih biaya", METRIC_EXPLANATIONS["Cost Variance"])

    if total_cost_variance > 0:
        finance_sentence = "Actual cost berada di atas budget, sehingga perlu perhatian pada pengendalian biaya."
        box_type = "warning"
    elif total_cost_variance < 0:
        finance_sentence = "Actual cost berada di bawah budget. Ini terlihat baik, tetapi tetap perlu dicek apakah karena efisiensi atau karena aktivitas operasional lebih rendah."
        box_type = "good"
    else:
        finance_sentence = "Actual cost sama dengan budget, sehingga biaya relatif sesuai rencana."
        box_type = "info"

    interpretation_box(
        f"<b>Interpretasi umum:</b> Rata-rata biaya produksi per volume adalah <b>{format_decimal(avg_prod_cost)}</b>. "
        f"Utilization rate alat berat berdasarkan view bulanan adalah <b>{format_percent(utilization_rate)}</b>. "
        f"{finance_sentence}",
        box_type=box_type
    )

    st.markdown("### Komposisi Data Agregasi")
    subject_count = filtered_monthly_df.groupby("subject_area", as_index=False).size()
    subject_count = subject_count.rename(columns={"size": "total_rows"})
    if not subject_count.empty:
        subject_count["subject_label"] = subject_count["subject_area"].map(subject_format)

    comp_col1, comp_col2 = st.columns([1, 2])
    with comp_col1:
        if subject_count.empty:
            st.warning("Tidak ada data agregasi untuk filter saat ini.")
        else:
            st.dataframe(subject_count[["subject_label", "total_rows"]], use_container_width=True)
            st.caption("Jumlah baris ini adalah hasil agregasi bulanan, bukan jumlah data mentah.")
    with comp_col2:
        if not subject_count.empty:
            fig_subject = px.bar(
                subject_count,
                x="subject_label",
                y="total_rows",
                text="total_rows",
                title="Aggregated Rows by Subject Area / Baris Agregasi per Area"
            )
            fig_subject.update_traces(textposition="outside")
            plot_chart(fig_subject, "overview_subject_distribution")

    st.markdown("### Tren Utama Bulanan")
    trend_col1, trend_col2 = st.columns(2)

    with trend_col1:
        if not df_production.empty and "total_produced_volume" in df_production.columns:
            prod_monthly = df_production.groupby(["year", "month", "month_name"], as_index=False)["total_produced_volume"].sum()
            prod_monthly = create_period_column(prod_monthly)
            monthly_chart(
                prod_monthly,
                "period_label",
                "total_produced_volume",
                "Production Volume Trend / Tren Volume Produksi",
                "overview_production_trend"
            )
            time_series_interpretation(prod_monthly, "period_label", "total_produced_volume", "volume produksi")
        else:
            st.warning("Data production tidak tersedia untuk filter ini.")

    with trend_col2:
        if not df_equipment_monthly.empty and "total_downtime_hours" in df_equipment_monthly.columns:
            eq_monthly = df_equipment_monthly.groupby(["year", "month", "month_name"], as_index=False)["total_downtime_hours"].sum()
            eq_monthly = create_period_column(eq_monthly)
            monthly_chart(
                eq_monthly,
                "period_label",
                "total_downtime_hours",
                "Monthly Downtime Hours / Jam Downtime Bulanan",
                "overview_monthly_downtime_trend",
                chart_type="bar"
            )
            time_series_interpretation(eq_monthly, "period_label", "total_downtime_hours", "jam downtime", "jam")
        else:
            st.warning("Data equipment bulanan tidak tersedia untuk filter ini.")

    st.markdown("### Ringkasan per Region")
    region_col1, region_col2 = st.columns(2)

    with region_col1:
        if not df_production.empty and "total_produced_volume" in df_production.columns:
            prod_region = df_production.groupby("region", as_index=False)["total_produced_volume"].sum()
            fig_region_prod = px.bar(
                prod_region,
                x="region",
                y="total_produced_volume",
                text_auto=True,
                title="Produced Volume by Region / Volume Produksi per Wilayah"
            )
            plot_chart(fig_region_prod, "overview_region_production")
            region_concentration_interpretation(prod_region, "total_produced_volume", "volume produksi")
        else:
            st.warning("Data produksi per region tidak tersedia.")

    with region_col2:
        if not df_financial.empty and "total_actual_cost" in df_financial.columns:
            fin_region = df_financial.groupby("region", as_index=False)["total_actual_cost"].sum()
            fig_region_cost = px.bar(
                fin_region,
                x="region",
                y="total_actual_cost",
                text_auto=True,
                title="Actual Cost by Region / Biaya Aktual per Wilayah"
            )
            plot_chart(fig_region_cost, "overview_region_actual_cost")
            region_concentration_interpretation(fin_region, "total_actual_cost", "actual cost")
        else:
            st.warning("Data financial per region tidak tersedia.")

    st.markdown("### Cara Membaca Dashboard")
    st.markdown(
        """
        - **Production / Produksi** digunakan untuk melihat output produksi dan biaya produksinya.
        - **Equipment / Alat Berat** pada dashboard utama menggunakan view bulanan `vw_dashboard_kpi_monthly` agar konsisten dengan Production dan Financial.
        - **Financial / Keuangan** digunakan untuk membandingkan budgeted cost dengan actual cost.
        - Detail harian alat berat tetap tersedia pada Data View melalui `vw_equipment_daily`.

        Nilai `None` pada raw monthly view bukan berarti error. Hal itu terjadi karena view bulanan menggabungkan beberapa jenis data dalam satu tabel.
        """
    )


# =========================================================
# Production Tab
# =========================================================
with tab_prod:
    st.subheader("Production Performance / Performa Produksi")

    if df_production.empty:
        show_empty_message("Production")
    else:
        produced_volume = safe_sum(df_production, "total_produced_volume")
        production_cost = safe_sum(df_production, "total_production_cost")
        avg_cost_per_volume = production_cost / produced_volume if produced_volume else 0

        prod_metric1, prod_metric2, prod_metric3 = st.columns(3)
        with prod_metric1:
            metric_card("Produced Volume", format_number(produced_volume), "Volume produksi", METRIC_EXPLANATIONS["Produced Volume"])
        with prod_metric2:
            metric_card("Production Cost", format_number(production_cost), "Biaya produksi", METRIC_EXPLANATIONS["Production Cost"])
        with prod_metric3:
            metric_card("Avg Cost per Volume", format_decimal(avg_cost_per_volume), "Rata-rata biaya per volume", METRIC_EXPLANATIONS["Avg Cost per Volume"])

        interpretation_box(
            f"<b>Interpretasi produksi:</b> Total produced volume adalah <b>{format_number(produced_volume)}</b> "
            f"dengan production cost sebesar <b>{format_number(production_cost)}</b>. "
            f"Rata-rata biaya per volume adalah <b>{format_decimal(avg_cost_per_volume)}</b>. "
            f"Angka ini belum otomatis menunjukkan efisiensi; efisiensi lebih kuat jika volume naik sementara biaya per volume stabil atau turun."
        )

        prod_monthly = df_production.groupby(["year", "month", "month_name"], as_index=False).agg({
            "total_produced_volume": "sum",
            "total_production_cost": "sum"
        })
        prod_monthly = create_period_column(prod_monthly)

        monthly_chart(
            prod_monthly,
            "period_label",
            "total_produced_volume",
            "Monthly Produced Volume / Volume Produksi Bulanan",
            "production_monthly_volume"
        )
        time_series_interpretation(prod_monthly, "period_label", "total_produced_volume", "volume produksi")

        monthly_chart(
            prod_monthly,
            "period_label",
            "total_production_cost",
            "Monthly Production Cost / Biaya Produksi Bulanan",
            "production_monthly_cost",
            chart_type="bar"
        )
        time_series_interpretation(prod_monthly, "period_label", "total_production_cost", "biaya produksi")

        prod_region = df_production.groupby("region", as_index=False).agg({
            "total_produced_volume": "sum",
            "total_production_cost": "sum"
        })
        fig_region = px.bar(
            prod_region,
            x="region",
            y="total_produced_volume",
            title="Produced Volume by Region / Volume Produksi per Wilayah",
            text_auto=True
        )
        plot_chart(fig_region, "production_region_volume")
        region_concentration_interpretation(prod_region, "total_produced_volume", "volume produksi")


# =========================================================
# Equipment Tab
# =========================================================
with tab_eq:
    st.subheader("Equipment Usage and Downtime / Penggunaan dan Downtime Alat Berat")

    if df_equipment_monthly.empty:
        show_empty_message("Equipment")
    else:
        operating_hours = safe_sum(df_equipment_monthly, "total_operating_hours")
        downtime_hours = safe_sum(df_equipment_monthly, "total_downtime_hours")
        fuel_consumption = safe_sum(df_equipment_monthly, "total_fuel_consumption")
        maintenance_cost = safe_sum(df_equipment_monthly, "total_maintenance_cost")
        utilization_rate = operating_hours / (operating_hours + downtime_hours) if (operating_hours + downtime_hours) else 0
        downtime_ratio = downtime_hours / (operating_hours + downtime_hours) if (operating_hours + downtime_hours) else 0

        eq_metric1, eq_metric2, eq_metric3, eq_metric4, eq_metric5 = st.columns(5)
        with eq_metric1:
            metric_card("Operating Hours", format_number(operating_hours), "Jam operasi", METRIC_EXPLANATIONS["Operating Hours"])
        with eq_metric2:
            metric_card("Downtime Hours", format_number(downtime_hours), "Jam alat berhenti", METRIC_EXPLANATIONS["Downtime Hours"])
        with eq_metric3:
            metric_card("Utilization Rate", format_percent(utilization_rate), "Tingkat pemanfaatan", METRIC_EXPLANATIONS["Utilization Rate"])
        with eq_metric4:
            metric_card("Downtime Ratio", format_percent(downtime_ratio), "Rasio downtime", METRIC_EXPLANATIONS["Downtime Ratio"])
        with eq_metric5:
            metric_card("Maintenance Cost", format_number(maintenance_cost), "Biaya perawatan", METRIC_EXPLANATIONS["Maintenance Cost"])

        explain_equipment_condition(operating_hours, downtime_hours, maintenance_cost, fuel_consumption)

        st.markdown("### Tren Bulanan Equipment")
        eq_monthly = df_equipment_monthly.groupby(["year", "month", "month_name"], as_index=False).agg({
            "total_operating_hours": "sum",
            "total_downtime_hours": "sum",
            "total_fuel_consumption": "sum",
            "total_maintenance_cost": "sum"
        })
        eq_monthly = create_period_column(eq_monthly)

        eq_monthly["downtime_ratio"] = eq_monthly["total_downtime_hours"] / (
            eq_monthly["total_downtime_hours"] + eq_monthly["total_operating_hours"]
        )

        monthly_chart(
            eq_monthly,
            "period_label",
            "total_downtime_hours",
            "Monthly Downtime Hours / Jam Downtime Bulanan",
            "equipment_monthly_downtime",
            chart_type="bar"
        )
        time_series_interpretation(eq_monthly, "period_label", "total_downtime_hours", "jam downtime", "jam")

        monthly_chart(
            eq_monthly,
            "period_label",
            "total_operating_hours",
            "Monthly Operating Hours / Jam Operasi Bulanan",
            "equipment_monthly_operating"
        )
        time_series_interpretation(eq_monthly, "period_label", "total_operating_hours", "jam operasi", "jam")

        monthly_chart(
            eq_monthly,
            "period_label",
            "total_maintenance_cost",
            "Monthly Maintenance Cost / Biaya Maintenance Bulanan",
            "equipment_monthly_maintenance",
            chart_type="bar"
        )
        time_series_interpretation(eq_monthly, "period_label", "total_maintenance_cost", "biaya maintenance")

        monthly_chart(
            eq_monthly,
            "period_label",
            "downtime_ratio",
            "Monthly Downtime Ratio / Rasio Downtime Bulanan",
            "equipment_monthly_downtime_ratio"
        )
        time_series_interpretation(eq_monthly, "period_label", "downtime_ratio", "rasio downtime", is_percent=True)

        st.markdown("### Breakdown Equipment berdasarkan Region")

        region_equipment = df_equipment_monthly.groupby("region", as_index=False).agg({
            "total_downtime_hours": "sum",
            "total_operating_hours": "sum",
            "total_maintenance_cost": "sum"
        })

        region_equipment["downtime_ratio"] = region_equipment["total_downtime_hours"] / (
            region_equipment["total_downtime_hours"] + region_equipment["total_operating_hours"]
        )

        breakdown_col1, breakdown_col2 = st.columns(2)

        with breakdown_col1:
            fig_region_downtime = px.bar(
                region_equipment,
                x="region",
                y="total_downtime_hours",
                text_auto=True,
                title="Downtime Hours by Region / Jam Downtime per Wilayah"
            )
            plot_chart(fig_region_downtime, "equipment_region_downtime")
            region_concentration_interpretation(region_equipment, "total_downtime_hours", "jam downtime", "jam")

        with breakdown_col2:
            fig_region_ratio = px.bar(
                region_equipment,
                x="region",
                y="downtime_ratio",
                text_auto=".2%",
                title="Downtime Ratio by Region / Rasio Downtime per Wilayah"
            )
            plot_chart(fig_region_ratio, "equipment_region_downtime_ratio")

            if not region_equipment.empty:
                top_ratio_region = region_equipment.sort_values("downtime_ratio", ascending=False).iloc[0]
                interpretation_box(
                    f"<b>Interpretasi rasio downtime:</b> Region dengan downtime ratio tertinggi adalah "
                    f"<b>{top_ratio_region['region']}</b> sebesar <b>{format_percent(top_ratio_region['downtime_ratio'])}</b>. "
                    f"Rasio ini lebih adil daripada downtime absolut karena mempertimbangkan total waktu alat. "
                    f"Jika rasio tinggi, region tersebut perlu ditinjau dari sisi perawatan, jadwal operasi, atau kondisi alat.",
                    box_type="info"
                )

        st.markdown(
            """
            **Cara membaca grafik equipment / alat berat:**  
            - Grafik utama memakai `vw_dashboard_kpi_monthly`, sehingga level analisisnya konsisten dengan Production dan Financial.
            - **Downtime Hours / Jam Downtime** menunjukkan total waktu alat tidak beroperasi.
            - **Operating Hours / Jam Operasi** menunjukkan total waktu alat digunakan.
            - **Downtime Ratio / Rasio Downtime** membantu membaca proporsi waktu berhenti dibandingkan total waktu alat.
            - Detail harian per alat tetap dapat dicek pada tab **Data View / Equipment Daily Detail** jika dibutuhkan untuk investigasi lanjutan.
            """
        )


# =========================================================
# Financial Tab
# =========================================================
with tab_fin:
    st.subheader("Financial and Cost Variance Analysis / Analisis Keuangan dan Selisih Biaya")

    if df_financial.empty:
        show_empty_message("Financial")
    else:
        total_budgeted_cost = safe_sum(df_financial, "total_budgeted_cost")
        total_actual_cost = safe_sum(df_financial, "total_actual_cost")
        total_cost_variance = safe_sum(df_financial, "total_cost_variance")

        fin_metric1, fin_metric2, fin_metric3 = st.columns(3)
        with fin_metric1:
            metric_card("Budgeted Cost", format_number(total_budgeted_cost), "Biaya yang direncanakan", METRIC_EXPLANATIONS["Budgeted Cost"])
        with fin_metric2:
            metric_card("Actual Cost", format_number(total_actual_cost), "Biaya aktual", METRIC_EXPLANATIONS["Actual Cost"])
        with fin_metric3:
            metric_card("Cost Variance", format_number(total_cost_variance), "Selisih biaya", METRIC_EXPLANATIONS["Cost Variance"])

        explain_financial_condition(total_budgeted_cost, total_actual_cost, total_cost_variance)

        fin_monthly = df_financial.groupby(["year", "month", "month_name"], as_index=False).agg({
            "total_budgeted_cost": "sum",
            "total_actual_cost": "sum",
            "total_cost_variance": "sum"
        })
        fin_monthly = create_period_column(fin_monthly)

        monthly_chart(
            fin_monthly,
            "period_label",
            "total_cost_variance",
            "Monthly Cost Variance / Selisih Biaya Bulanan",
            "financial_monthly_variance"
        )
        time_series_interpretation(fin_monthly, "period_label", "total_cost_variance", "cost variance")

        fig_budget_actual = px.bar(
            fin_monthly,
            x="period_label",
            y=["total_budgeted_cost", "total_actual_cost"],
            barmode="group",
            title="Budgeted Cost vs Actual Cost / Anggaran vs Biaya Aktual"
        )
        plot_chart(fig_budget_actual, "financial_budget_vs_actual")

        st.markdown(
            """
            **Cara membaca grafik financial / keuangan:**  
            - **Budgeted Cost / Biaya Anggaran** adalah biaya yang direncanakan.  
            - **Actual Cost / Biaya Aktual** adalah biaya yang benar-benar terjadi.  
            - **Cost Variance / Selisih Biaya** adalah actual cost dikurangi budgeted cost.  
            - Jika actual cost lebih tinggi dari budgeted cost, terdapat indikasi over budget.  
            - Jika actual cost lebih rendah dari budgeted cost, biaya terlihat lebih hemat, tetapi tetap perlu dicek apakah target operasional juga tercapai.
            """
        )


# =========================================================
# Data View Tab
# =========================================================
with tab_data:
    st.subheader("Data View / Tampilan Data")

    st.markdown(
        """
        Bagian ini menampilkan data agregasi dari view bulanan dan data detail harian equipment.
        Grafik utama dashboard memakai data bulanan agar konsisten, sedangkan data harian disediakan sebagai drill-down untuk investigasi alat berat.
        """
    )

    data_tab1, data_tab2, data_tab3, data_tab4, data_tab5 = st.tabs(
        ["Production Data", "Equipment Monthly Data", "Financial Data", "Monthly Raw View", "Equipment Daily Detail"]
    )

    with data_tab1:
        production_cols = [
            "subject_area", "year", "month", "month_name", "quarter", "region",
            "total_produced_volume", "total_production_cost"
        ]
        available_cols = available_columns(df_production, production_cols)
        st.dataframe(df_production[available_cols], use_container_width=True)

    with data_tab2:
        equipment_monthly_cols = [
            "subject_area", "year", "month", "month_name", "quarter", "region",
            "total_operating_hours", "total_downtime_hours",
            "total_fuel_consumption", "total_maintenance_cost"
        ]
        available_cols = available_columns(df_equipment_monthly, equipment_monthly_cols)
        st.dataframe(df_equipment_monthly[available_cols], use_container_width=True)

    with data_tab3:
        financial_cols = [
            "subject_area", "year", "month", "month_name", "quarter", "region",
            "total_budgeted_cost", "total_actual_cost", "total_cost_variance"
        ]
        available_cols = available_columns(df_financial, financial_cols)
        st.dataframe(df_financial[available_cols], use_container_width=True)

    with data_tab4:
        st.dataframe(filtered_monthly_df, use_container_width=True)

    with data_tab5:
        equipment_daily_cols = [
            "full_date", "year", "month", "month_name", "quarter", "region", "site_name",
            "equipment_name", "equipment_type", "total_operating_hours", "total_downtime_hours",
            "total_fuel_consumption", "total_maintenance_cost", "utilization_rate", "downtime_ratio"
        ]
        available_cols = available_columns(filtered_equipment_daily, equipment_daily_cols)
        st.dataframe(filtered_equipment_daily[available_cols], use_container_width=True)

    st.caption(
        "Catatan: Monthly raw view menggabungkan production, equipment, dan financial dalam satu struktur tabel. "
        "Equipment daily detail digunakan sebagai data pendukung untuk melihat detail alat, bukan sebagai grafik utama dashboard."
    )
