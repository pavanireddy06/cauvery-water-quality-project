from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Cauvery River | Water Quality Assessment",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "processed" / "cauvery_analysis_data.csv"

PARAMETERS = {
    "pH": "pH",
    "DO_mg_L": "Dissolved Oxygen (mg/L)",
    "BOD_mg_L": "Biochemical Oxygen Demand (mg/L)",
    "COD_mg_L": "Chemical Oxygen Demand (mg/L)",
    "EC_uS_cm": "Electrical Conductivity (µS/cm)",
    "Turbidity_NTU": "Turbidity (NTU)",
    "TDS_mg_L": "Total Dissolved Solids (mg/L)",
    "Nitrate_mg_L": "Nitrate (mg/L)",
    "Total_Phosphorus_mgP_L": "Total Phosphorus (mgP/L)",
    "Fecal_Coliform_MPN_100mL": "Fecal Coliform (MPN/100 mL)",
    "Total_Coliform_MPN_100mL": "Total Coliform (MPN/100 mL)",
}
NUMERIC_COLUMNS = list(PARAMETERS.keys())

# The fecal-coliform values below are from a separate primary
# bathing-water criteria framework; they are not the DBU Class B
# total-coliform criterion.
PH_LOW, PH_HIGH = 6.5, 8.5
DO_MIN = 5.0
BOD_MAX = 3.0  # Provisional: source file does not specify test method.
FC_DESIRABLE = 500.0
FC_MAX = 2500.0


# ============================================================
# 2. PAGE STYLING
# ============================================================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.7rem 1.8rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #073b4c 0%, #087e8b 55%, #118ab2 100%);
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .hero h1 {color: #ffffff; margin: 0 0 .55rem 0; font-size: 2.2rem;}
    .hero p {color: #eefaff; margin: .25rem 0; line-height: 1.55;}
    .small-note {font-size: .9rem; color: #6b7280;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. LOAD AND VALIDATE DATA
# ============================================================
@st.cache_data
def load_data(file_path: str, modified_time: float) -> pd.DataFrame:
    data = pd.read_csv(file_path)

    required = ["Station", "Data Acquisition Time"]
    missing_required = [column for column in required if column not in data.columns]
    if missing_required:
        raise ValueError(
            "The CSV is missing required column(s): " + ", ".join(missing_required)
        )

    # Keep the dashboard resilient if a parameter column is absent.
    for column in NUMERIC_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Station"] = data["Station"].fillna("Unknown Station").astype(str)
    data["Data Acquisition Time"] = pd.to_datetime(
        data["Data Acquisition Time"], errors="coerce"
    )
    return data


st.title("🌊 Cauvery River Water Quality Assessment")

if not DATA_FILE.exists():
    st.error(
        "The analysis dataset could not be found. Expected location: "
        "`data/processed/cauvery_analysis_data.csv`."
    )
    st.stop()

try:
    df = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
except Exception as exc:
    st.error(f"Unable to load the analysis dataset: {exc}")
    st.stop()

if df.empty:
    st.error("The analysis dataset contains no observations.")
    st.stop()

st.markdown(
    """
    <div class="hero">
      <h1>Data-driven assessment of the Cauvery River</h1>
      <p><strong>Study focus:</strong> selected Cauvery/Kaveri monitoring stations in Karnataka</p>
      <p>Explore available observations, compare stations, inspect selected water-quality indicators,
      and review data availability through this interactive dashboard.</p>
      <p><strong>Scope note:</strong> this version performs descriptive analysis. It does not train
      an AI model or predict future pollution.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("📘 Project overview: objectives, methodology and scope"):
    left, right = st.columns(2)
    with left:
        st.subheader("Objectives")
        st.markdown(
            """
            - Explore available Cauvery River water-quality observations.
            - Summarise pH, dissolved oxygen (DO), BOD and fecal coliform.
            - Compare measurements between monitoring stations.
            - Flag observations that warrant source-record validation.
            - Report missing values transparently and export filtered records.
            """
        )
    with right:
        st.subheader("Methodology")
        st.markdown(
            """
            1. Select CPCB/NWIC Karnataka records whose station/river text matches Cauvery/Kaveri.
            2. Match available physical, chemical and biological records by station/date.
            3. Parse dates and measurement values; keep missing values missing.
            4. Calculate descriptive statistics and generate interactive visualisations.
            5. Compare selected parameters with clearly labelled reference criteria.
            """
        )
    st.subheader("Scope and limitations")
    st.markdown(
        """
        - Prepared analysis file: 70 station-date observations across 24 stations, from 5 January to 24 March 2021.
        - pH, DO and fecal coliform are available for all 70 rows; BOD is available for 67 rows.
        - COD, electrical conductivity, turbidity, TDS, nitrate, total phosphorus and total coliform have no usable values in this prepared file.
        - The initial KSPCB station-name filter did not identify Cauvery/Kaveri records, so unrelated KSPCB rows were not mixed into this analysis.
        - These selected observations do not represent continuous monitoring or current river-wide conditions.
        """
    )

st.divider()


# ============================================================
# 4. SIDEBAR FILTERS
# ============================================================
st.sidebar.title("🔎 Filter observations")
st.sidebar.caption("Filters update the charts, summaries and downloads.")

stations = sorted(df["Station"].dropna().unique().tolist())
selected_station = st.sidebar.selectbox(
    "Monitoring station", ["All Stations"] + stations
)

valid_dates = df["Data Acquisition Time"].dropna()
if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    selected_dates = st.sidebar.date_input(
        "Sample date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
else:
    selected_dates = ()

st.sidebar.divider()
st.sidebar.markdown("**Dataset period**")
st.sidebar.write(
    f"{valid_dates.min().date()} to {valid_dates.max().date()}"
    if not valid_dates.empty
    else "No valid sample dates"
)
st.sidebar.caption("The source data are historical observations, not live water-quality readings.")

filtered_df = df.copy()

if selected_station != "All Stations":
    filtered_df = filtered_df[filtered_df["Station"] == selected_station]

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    date_mask = filtered_df["Data Acquisition Time"].dt.date.between(start_date, end_date)
    filtered_df = filtered_df[date_mask]

filtered_df = filtered_df.sort_values("Data Acquisition Time")

if filtered_df.empty:
    st.warning("No observations match the selected filters. Change the station or date range.")
    st.stop()


# ============================================================
# 5. SUMMARY METRICS
# ============================================================
st.header("📊 Water-quality overview")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Observations", f"{len(filtered_df):,}")
m2.metric("Monitoring stations", f"{filtered_df['Station'].nunique():,}")

mean_ph = filtered_df["pH"].mean()
mean_do = filtered_df["DO_mg_L"].mean()
m3.metric("Mean pH", f"{mean_ph:.2f}" if pd.notna(mean_ph) else "N/A")
m4.metric("Mean dissolved oxygen", f"{mean_do:.2f} mg/L" if pd.notna(mean_do) else "N/A")

m5, m6, m7 = st.columns(3)
mean_bod = filtered_df["BOD_mg_L"].mean()
mean_fc = filtered_df["Fecal_Coliform_MPN_100mL"].mean()
m5.metric("Mean BOD", f"{mean_bod:.2f} mg/L" if pd.notna(mean_bod) else "N/A")
m6.metric("Mean fecal coliform", f"{mean_fc:,.2f} MPN/100 mL" if pd.notna(mean_fc) else "N/A")
m7.metric("Parameters with data", f"{sum(filtered_df[c].notna().any() for c in NUMERIC_COLUMNS)} / {len(NUMERIC_COLUMNS)}")

st.caption("Summary metrics describe only the observations currently selected; they are not predictions.")
st.divider()


# ============================================================
# 6. PARAMETER VISUALISATIONS
# ============================================================
st.header("📈 Parameter analysis")
st.caption("Select a parameter to inspect its distribution, station means and sample-level values.")

available_parameters = [
    column for column in NUMERIC_COLUMNS if filtered_df[column].notna().any()
]
parameter_labels = {column: PARAMETERS[column] for column in available_parameters}

if available_parameters:
    chosen_parameter = st.selectbox(
        "Choose a parameter",
        available_parameters,
        format_func=lambda column: PARAMETERS[column],
        key="parameter_analysis_choice",
    )
    parameter_data = filtered_df.dropna(subset=[chosen_parameter]).copy()

    p1, p2 = st.columns(2)
    with p1:
        fig_hist = px.histogram(
            parameter_data,
            x=chosen_parameter,
            nbins=18,
            title=f"Distribution: {PARAMETERS[chosen_parameter]}",
            labels={chosen_parameter: PARAMETERS[chosen_parameter]},
        )
        fig_hist.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig_hist, width="stretch")

    with p2:
        station_mean = (
            parameter_data.groupby("Station", as_index=False)[chosen_parameter]
            .mean()
            .sort_values(chosen_parameter)
        )
        fig_means = px.bar(
            station_mean,
            x=chosen_parameter,
            y="Station",
            orientation="h",
            title=f"Mean {PARAMETERS[chosen_parameter]} by station",
            labels={
                chosen_parameter: PARAMETERS[chosen_parameter],
                "Station": "Monitoring station",
            },
        )
        fig_means.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=10, r=10, t=55, b=10),
        )
        st.plotly_chart(fig_means, width="stretch")

    time_data = parameter_data.dropna(subset=["Data Acquisition Time"])
    if not time_data.empty:
        fig_time = px.scatter(
            time_data,
            x="Data Acquisition Time",
            y=chosen_parameter,
            color="Station",
            hover_data=["Station"],
            title=f"{PARAMETERS[chosen_parameter]} by sample date",
            labels={
                "Data Acquisition Time": "Sample date",
                chosen_parameter: PARAMETERS[chosen_parameter],
            },
        )
        fig_time.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig_time, width="stretch")

    st.subheader("Selected parameter summary")
    st.dataframe(
        parameter_data[["Station", "Data Acquisition Time", chosen_parameter]]
        .rename(columns={chosen_parameter: PARAMETERS[chosen_parameter]}),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No usable numeric measurements are available for the current selection.")

st.divider()


# ============================================================
# 7. REFERENCE COMPARISON
# ============================================================
st.header("🧭 Preliminary water-quality reference comparison")
st.markdown(
    """
    These are **parameter-wise comparisons only**, not a formal river classification or a safety certificate.

    **CPCB Designated Best Use (DBU), Class B — organised outdoor bathing**
    - pH: 6.5–8.5
    - Dissolved oxygen: at least 5 mg/L
    - BOD₅ at 20°C: at most 3 mg/L
    - Total coliform: at most 500 MPN/100 mL

    **Separate primary bathing-water fecal-coliform criteria**
    - Fecal coliform: 500 MPN/100 mL desirable
    - Fecal coliform: 2,500 MPN/100 mL maximum permissible

    The fecal-coliform values above belong to a separate bathing-water framework; they are **not** the DBU Class B total-coliform limit.
    """
)

st.info(
    """
    **Limitations:** total-coliform measurements are unavailable, so the complete DBU Class B criteria cannot be assessed.
    The source file does not specify the BOD test duration/temperature, so BOD comparisons are provisional.
    These criteria are use-specific and do not establish drinking-water safety or certify bathing safety.
    """
)

assessment = filtered_df[["Station", "Data Acquisition Time"]].copy()
assessment = assessment.rename(columns={"Data Acquisition Time": "Sample Date"})

def classify_ph(value):
    if pd.isna(value):
        return "Unavailable"
    return "Within reference range" if PH_LOW <= value <= PH_HIGH else "Outside reference range"

def classify_do(value):
    if pd.isna(value):
        return "Unavailable"
    return "Meets reference value" if value >= DO_MIN else "Below reference value"

def classify_bod(value):
    if pd.isna(value):
        return "Unavailable"
    return "Provisionally within reference value" if value <= BOD_MAX else "Provisionally above reference value"

def classify_fc(value):
    if pd.isna(value):
        return "Unavailable"
    if value <= FC_DESIRABLE:
        return "At or below desirable value"
    if value <= FC_MAX:
        return "Above desirable, within maximum"
    return "Above maximum permissible value"

assessment["pH"] = filtered_df["pH"]
assessment["pH comparison"] = filtered_df["pH"].map(classify_ph)
assessment["DO (mg/L)"] = filtered_df["DO_mg_L"]
assessment["DO comparison"] = filtered_df["DO_mg_L"].map(classify_do)
assessment["BOD (mg/L)"] = filtered_df["BOD_mg_L"]
assessment["BOD comparison (provisional)"] = filtered_df["BOD_mg_L"].map(classify_bod)
assessment["Fecal coliform (MPN/100 mL)"] = filtered_df["Fecal_Coliform_MPN_100mL"]
assessment["Fecal-coliform comparison"] = filtered_df["Fecal_Coliform_MPN_100mL"].map(classify_fc)

st.subheader("Observation-wise comparison")
st.dataframe(assessment, width="stretch", hide_index=True)
st.download_button(
    "📥 Download reference-comparison results",
    data=assessment.to_csv(index=False).encode("utf-8"),
    file_name="cauvery_water_quality_reference_comparison.csv",
    mime="text/csv",
)

st.subheader("Comparison counts")
status_cols = [
    ("pH comparison", "pH"),
    ("DO comparison", "Dissolved oxygen"),
    ("BOD comparison (provisional)", "BOD (provisional)"),
    ("Fecal-coliform comparison", "Fecal coliform"),
]
scols = st.columns(2)
for index, (column, title) in enumerate(status_cols):
    with scols[index % 2]:
        st.markdown(f"**{title}**")
        counts = assessment[column].value_counts().rename_axis("Status").reset_index(name="Observations")
        st.dataframe(counts, width="stretch", hide_index=True)

st.divider()


# ============================================================
# 8. MISSING-DATA ANALYSIS
# ============================================================
st.header("⚠️ Data availability and missing measurements")
missing_rows = []
total_records = len(filtered_df)
for column, label in PARAMETERS.items():
    available = int(filtered_df[column].notna().sum())
    missing = total_records - available
    missing_rows.append(
        {
            "Parameter": label,
            "Available measurements": available,
            "Missing measurements": missing,
            "Missing (%)": round((missing / total_records) * 100, 2) if total_records else 0.0,
        }
    )
missing_df = pd.DataFrame(missing_rows)
st.dataframe(missing_df, width="stretch", hide_index=True)

fig_missing = px.bar(
    missing_df.sort_values("Missing (%)", ascending=True),
    x="Missing (%)",
    y="Parameter",
    orientation="h",
    title="Percentage of missing measurements",
    range_x=[0, 100],
)
fig_missing.update_layout(margin=dict(l=10, r=10, t=55, b=10))
st.plotly_chart(fig_missing, width="stretch")

st.warning(
    "A missing measurement is not zero. Parameters with no usable values in this prepared dataset are shown as unavailable; "
    "they are not filled with invented values."
)
st.divider()


# ============================================================
# 9. FILTERED OBSERVATIONS AND EXPORT
# ============================================================
st.header("📋 Filtered water-quality observations")
display_columns = [
    "Station",
    "Data Acquisition Time",
    "pH",
    "DO_mg_L",
    "BOD_mg_L",
    "Fecal_Coliform_MPN_100mL",
    "COD_mg_L",
    "EC_uS_cm",
    "Turbidity_NTU",
    "TDS_mg_L",
    "Nitrate_mg_L",
    "Total_Phosphorus_mgP_L",
    "Total_Coliform_MPN_100mL",
]
display_columns = [column for column in display_columns if column in filtered_df.columns]
display_df = filtered_df[display_columns].rename(columns=PARAMETERS)
st.dataframe(display_df, width="stretch", hide_index=True)
st.download_button(
    "📥 Download filtered observations (CSV)",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="cauvery_filtered_observations.csv",
    mime="text/csv",
)

st.divider()


# ============================================================
# 10. KEY FINDINGS AND SOURCES
# ============================================================
st.header("🧾 Key findings and interpretation")
st.markdown(
    """
    - The prepared records have pH values from **6.9 to 8.4** (mean **7.87**), within the selected 6.5–8.5 reference range.
    - Dissolved oxygen ranges from **1.2 to 8.7 mg/L** (mean **6.51 mg/L**); the minimum is below the selected 5 mg/L reference value and should be validated against its original station/date record.
    - BOD ranges from **1.2 to 5.0 mg/L** (mean **1.90 mg/L**); criterion comparisons remain provisional because the test method is not specified.
    - Fecal coliform ranges from **21 to 14,000 MPN/100 mL**. The highest value is above the separate 2,500 MPN/100 mL maximum-permissible bathing-water reference and should be checked against the original source record.
    - Several parameters have no usable values in the prepared file, preventing a complete multi-parameter assessment.

    These findings apply only to the included observations from January–March 2021. They should not be generalised to the entire Cauvery River or current conditions.
    """
)

st.subheader("Data sources and references")
st.markdown(
    """
    - [CPCB/NWIC physical surface-water quality dataset — Karnataka](https://nwdp.nwic.gov.in/en/dataset/surface-water-quality-manual-physical-parameters-cpcb)
    - [CPCB/NWIC chemical surface-water quality dataset — Karnataka](https://www.nwdp.nwic.gov.in/en/dataset/surface-water-quality-manual-chemical-parameters-cpcb)
    - [CPCB/NWIC biological surface-water quality dataset — Karnataka](https://www.nwdp.nwic.gov.in/en/dataset/surface-water-quality-manual-biological-parameters-cpcb)
    - [KSPCB/NWIC Karnataka water-quality dataset](https://nwdp.nwic.gov.in/dataset/water-quality-manual-karnataka)
    - [CPCB Designated Best Use Water Quality Criteria](https://cpcb.nic.in/wqm/Designated_Best_Use_Water_Quality_Criteria.pdf)
    - [Project source code on GitHub](https://github.com/pavanireddy06/cauvery-water-quality-project)
    """
)

st.caption(
    "Academic project | Cauvery River Water Quality Assessment | Descriptive analysis, not an AI prediction or safety certification."
)
