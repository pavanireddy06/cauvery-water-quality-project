import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cauvery River Water Quality Assessment",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. CONSTANTS AND FILE PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "cauvery_analysis_data.csv"
)

PARAMETERS = {
    "pH": "pH",
    "DO_mg_L": "Dissolved Oxygen (mg/L)",
    "BOD_mg_L": "Biochemical Oxygen Demand (mg/L)",
    "COD_mg_L": "Chemical Oxygen Demand (mg/L)",
    "EC_uS_cm": "Electrical Conductivity (μS/cm)",
    "Turbidity_NTU": "Turbidity (NTU)",
    "TDS_mg_L": "Total Dissolved Solids (mg/L)",
    "Nitrate_mg_L": "Nitrate (mg/L)",
    "Total_Phosphorus_mgP_L": "Total Phosphorus (mgP/L)",
    "Fecal_Coliform_MPN_100mL": (
        "Fecal Coliform (MPN/100 mL)"
    ),
    "Total_Coliform_MPN_100mL": (
        "Total Coliform (MPN/100 mL)"
    )
}

NUMERIC_COLUMNS = list(PARAMETERS.keys())

# ============================================================
# 3. LOAD DATA
# ============================================================

@st.cache_data
def load_data(file_path, modified_time):
    data = pd.read_csv(file_path)

    required_columns = [
        "Station",
        "Data Acquisition Time",
        *NUMERIC_COLUMNS
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "The dataset is missing these required columns: "
            + ", ".join(missing_columns)
        )

    data["Data Acquisition Time"] = pd.to_datetime(
        data["Data Acquisition Time"],
        errors="coerce"
    )

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data["Station"] = data["Station"].fillna(
        "Unknown Station"
    )

    return data


st.title("🌊 Cauvery River Water Quality Assessment")

st.markdown(
    """
    ### AI-Based Water Quality Assessment and Pollution Analysis

    **Study area:** Cauvery River monitoring stations in Karnataka

    This application explores available water quality observations
    obtained from CPCB datasets and prepared for analysis.

    Use the filters to investigate individual monitoring stations,
    examine water quality parameters, compare observations, and
    identify missing measurements.
    """
)

st.divider()

# ============================================================
# 4. CHECK DATASET
# ============================================================

if not DATA_FILE.exists():

    st.error(
        "Dataset not found. Please check the file location."
    )

    st.code(
        "data/processed/cauvery_analysis_data.csv"
    )

    st.stop()

try:
    df = load_data(
        str(DATA_FILE),
        DATA_FILE.stat().st_mtime
    )

except Exception as error:

    st.error(f"Unable to load the dataset: {error}")
    st.stop()


if df.empty:
    st.error("The dataset contains no observations.")
    st.stop()


# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

st.sidebar.title("🔎 Filter Observations")

st.sidebar.write(
    "Select a monitoring station and date range."
)

stations = sorted(
    df["Station"].dropna().unique().tolist()
)

station_options = ["All Stations"] + stations

selected_station = st.sidebar.selectbox(
    "Monitoring Station",
    station_options
)

valid_dates = df["Data Acquisition Time"].dropna()

if not valid_dates.empty:

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

else:
    selected_dates = ()


st.sidebar.divider()

st.sidebar.caption(
    "The results update according to your selected filters."
)

# ============================================================
# 6. APPLY FILTERS
# ============================================================

filtered_df = df.copy()

if selected_station != "All Stations":

    filtered_df = filtered_df[
        filtered_df["Station"] == selected_station
    ]


if isinstance(selected_dates, (tuple, list)):

    if len(selected_dates) == 2:

        start_date, end_date = selected_dates

        filtered_df = filtered_df[
            filtered_df["Data Acquisition Time"]
            .dt.date
            .between(start_date, end_date)
        ]


filtered_df = filtered_df.sort_values(
    "Data Acquisition Time"
)

# ============================================================
# 7. SUMMARY CARDS
# ============================================================

st.header("📊 Water Quality Overview")

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:

    st.metric(
        "Observations",
        f"{len(filtered_df):,}"
    )

with metric2:

    station_count = filtered_df["Station"].nunique()

    st.metric(
        "Monitoring Stations",
        station_count
    )

with metric3:

    average_ph = filtered_df["pH"].mean()

    st.metric(
        "Average pH",
        f"{average_ph:.2f}"
        if pd.notna(average_ph)
        else "N/A"
    )

with metric4:

    average_do = filtered_df["DO_mg_L"].mean()

    st.metric(
        "Average Dissolved Oxygen",
        f"{average_do:.2f} mg/L"
        if pd.notna(average_do)
        else "N/A"
    )


metric5, metric6 = st.columns(2)

with metric5:

    average_bod = filtered_df["BOD_mg_L"].mean()

    st.metric(
        "Average BOD",
        f"{average_bod:.2f} mg/L"
        if pd.notna(average_bod)
        else "N/A"
    )

with metric6:

    average_fc = filtered_df[
        "Fecal_Coliform_MPN_100mL"
    ].mean()

    st.metric(
        "Average Fecal Coliform",
        f"{average_fc:.2f} MPN/100 mL"
        if pd.notna(average_fc)
        else "N/A"
    )


st.caption(
    "These are descriptive statistics of the filtered observations, "
    "not predictions of future water quality."
)

if filtered_df.empty:

    st.warning(
        "No observations match the selected station and date range. "
        "Please change your filters."
    )

    st.stop()

st.divider()

# ============================================================
# 8. PH ANALYSIS
# ============================================================

st.header("🧪 1. pH Analysis")

st.write(
    "pH describes the acidity or alkalinity of water."
)

ph_data = filtered_df.dropna(
    subset=["pH"]
).copy()

if not ph_data.empty:

    ph_col1, ph_col2 = st.columns(2)

    with ph_col1:

        fig_ph_hist = px.histogram(
            ph_data,
            x="pH",
            nbins=15,
            title="Distribution of pH Measurements",
            labels={
                "pH": "pH Value"
            }
        )

        st.plotly_chart(
            fig_ph_hist,
            use_container_width=True
        )

    with ph_col2:

        ph_time_data = ph_data.dropna(
            subset=["Data Acquisition Time"]
        )

        if not ph_time_data.empty:

            fig_ph_time = px.scatter(
                ph_time_data,
                x="Data Acquisition Time",
                y="pH",
                color="Station",
                title="pH Observations Over Time",
                labels={
                    "Data Acquisition Time": "Sample Date",
                    "pH": "pH Value"
                }
            )

            st.plotly_chart(
                fig_ph_time,
                use_container_width=True
            )

    st.write(
        f"Minimum pH: **{ph_data['pH'].min():.2f}**"
        f" | Maximum pH: **{ph_data['pH'].max():.2f}**"
    )

else:

    st.info("No pH measurements are available for this selection.")

st.divider()

# ============================================================
# 9. DISSOLVED OXYGEN ANALYSIS
# ============================================================

st.header("💧 2. Dissolved Oxygen Analysis")

st.write(
    "Dissolved oxygen (DO) measures the oxygen available "
    "in water and helps investigate aquatic conditions."
)

do_data = filtered_df.dropna(
    subset=["DO_mg_L"]
).copy()

if not do_data.empty:

    do_col1, do_col2 = st.columns(2)

    with do_col1:

        fig_do_box = px.box(
            do_data,
            y="DO_mg_L",
            points="all",
            title="Dissolved Oxygen Distribution",
            labels={
                "DO_mg_L": "DO (mg/L)"
            }
        )

        st.plotly_chart(
            fig_do_box,
            use_container_width=True
        )

    with do_col2:

        do_time_data = do_data.dropna(
            subset=["Data Acquisition Time"]
        )

        if not do_time_data.empty:

            fig_do_time = px.scatter(
                do_time_data,
                x="Data Acquisition Time",
                y="DO_mg_L",
                color="Station",
                title="Dissolved Oxygen Over Time",
                labels={
                    "Data Acquisition Time": "Sample Date",
                    "DO_mg_L": "DO (mg/L)"
                }
            )

            st.plotly_chart(
                fig_do_time,
                use_container_width=True
            )

    st.write(
        f"Minimum DO: **{do_data['DO_mg_L'].min():.2f} mg/L**"
        f" | Maximum DO: **{do_data['DO_mg_L'].max():.2f} mg/L**"
    )

else:

    st.info(
        "No dissolved oxygen measurements are available."
    )

st.divider()

# ============================================================
# 10. BOD ANALYSIS
# ============================================================

st.header("🔬 3. Biochemical Oxygen Demand Analysis")

st.write(
    """
    Biochemical Oxygen Demand (BOD) measures the oxygen consumed
    by microorganisms while breaking down biodegradable organic
    matter under specified test conditions.
    """
)

bod_data = filtered_df.dropna(
    subset=["BOD_mg_L"]
).copy()

if not bod_data.empty:

    bod_col1, bod_col2 = st.columns(2)

    with bod_col1:

        fig_bod_box = px.box(
            bod_data,
            y="BOD_mg_L",
            points="all",
            title="BOD Distribution",
            labels={
                "BOD_mg_L": "BOD (mg/L)"
            }
        )

        st.plotly_chart(
            fig_bod_box,
            use_container_width=True
        )

    with bod_col2:

        bod_time_data = bod_data.dropna(
            subset=["Data Acquisition Time"]
        )

        if not bod_time_data.empty:

            fig_bod_time = px.scatter(
                bod_time_data,
                x="Data Acquisition Time",
                y="BOD_mg_L",
                color="Station",
                title="BOD Observations Over Time",
                labels={
                    "Data Acquisition Time": "Sample Date",
                    "BOD_mg_L": "BOD (mg/L)"
                }
            )

            st.plotly_chart(
                fig_bod_time,
                use_container_width=True
            )

    st.warning(
        "The dataset does not specify the BOD test duration or "
        "temperature. Comparisons with BOD reference criteria "
        "are therefore provisional."
    )

else:

    st.info(
        "No BOD measurements are available for this selection."
    )

st.divider()

# ============================================================
# 11. FECAL COLIFORM ANALYSIS
# ============================================================

st.header("🦠 4. Fecal Coliform Analysis")

st.write(
    """
    Fecal coliform measurements can help identify observations
    that warrant investigation for possible fecal contamination.
    They do not, by themselves, establish whether water is safe.
    """
)

fc_data = filtered_df.dropna(
    subset=["Fecal_Coliform_MPN_100mL"]
).copy()

if not fc_data.empty:

    fc_col1, fc_col2 = st.columns(2)

    with fc_col1:

        fig_fc_hist = px.histogram(
            fc_data,
            x="Fecal_Coliform_MPN_100mL",
            nbins=20,
            title="Fecal Coliform Distribution",
            labels={
                "Fecal_Coliform_MPN_100mL":
                    "Fecal Coliform (MPN/100 mL)"
            }
        )

        st.plotly_chart(
            fig_fc_hist,
            use_container_width=True
        )

    with fc_col2:

        fc_time_data = fc_data.dropna(
            subset=["Data Acquisition Time"]
        )

        if not fc_time_data.empty:

            fig_fc_time = px.scatter(
                fc_time_data,
                x="Data Acquisition Time",
                y="Fecal_Coliform_MPN_100mL",
                color="Station",
                title="Fecal Coliform Over Time",
                labels={
                    "Data Acquisition Time": "Sample Date",
                    "Fecal_Coliform_MPN_100mL":
                        "Fecal Coliform (MPN/100 mL)"
                }
            )

            st.plotly_chart(
                fig_fc_time,
                use_container_width=True
            )

    st.write(
        f"Minimum: **{fc_data['Fecal_Coliform_MPN_100mL'].min():.0f}**"
        f" | Maximum: **{fc_data['Fecal_Coliform_MPN_100mL'].max():.0f}**"
        " MPN/100 mL"
    )

else:

    st.info(
        "No fecal coliform measurements are available."
    )

st.divider()

# ============================================================
# 12. STATION COMPARISON
# ============================================================

st.header("📍 5. Monitoring Station Comparison")

st.write(
    "Compare the mean value of a selected parameter across "
    "the monitoring stations included in the current filters."
)

comparison_parameters = {
    "pH": "pH",
    "DO_mg_L": "Dissolved Oxygen (mg/L)",
    "BOD_mg_L": "Biochemical Oxygen Demand (mg/L)",
    "Fecal_Coliform_MPN_100mL":
        "Fecal Coliform (MPN/100 mL)"
}

comparison_parameter = st.selectbox(
    "Select parameter",
    list(comparison_parameters.keys()),
    format_func=lambda value: comparison_parameters[value],
    key="station_comparison_parameter"
)

station_means = (
    filtered_df.groupby("Station", as_index=False)
    [comparison_parameter]
    .mean()
    .dropna(subset=[comparison_parameter])
    .sort_values(comparison_parameter)
)

if not station_means.empty:

    fig_station = px.bar(
        station_means,
        x="Station",
        y=comparison_parameter,
        title=(
            "Mean "
            + comparison_parameters[comparison_parameter]
            + " by Station"
        ),
        labels={
            "Station": "Monitoring Station",
            comparison_parameter:
                comparison_parameters[comparison_parameter]
        }
    )

    fig_station.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_station,
        use_container_width=True
    )

    st.dataframe(
        station_means,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No measurements are available for this comparison."
    )

st.divider()

# ============================================================
# 13. PRELIMINARY CPCB CLASS B REFERENCE ASSESSMENT
# ============================================================

st.header("✅ 6. Preliminary Water Quality Reference Assessment")

st.markdown(
    """
    This section compares available measurements with selected
    CPCB Class B reference criteria for organised outdoor bathing.

    **This is a parameter-wise reference comparison, not an
    overall water quality classification or a bathing-safety
    certificate.**
    """
)

st.markdown(
    """
    **Reference criteria used**

    - pH: 6.5–8.5
    - Dissolved Oxygen: at least 5 mg/L
    - BOD: at most 3 mg/L, subject to confirmation of the
      applicable test method
    - Fecal Coliform: 500 MPN/100 mL desirable and
      2,500 MPN/100 mL maximum permissible
    """
)

st.info(
    """
    Important limitations:

    1. The BOD test method is not specified in the dataset.
       BOD comparisons are provisional.
    2. Total coliform measurements are unavailable in the
       prepared dataset.
    3. These criteria are specific to a designated use.
    4. A complete water quality or bathing-safety determination
       requires additional information and appropriate assessment.
    """
)

assessment_rows = []

for _, row in filtered_df.iterrows():

    # --------------------------------------------------------
    # pH
    # --------------------------------------------------------

    ph_value = row["pH"]

    if pd.isna(ph_value):

        ph_status = "Unavailable"

    elif 6.5 <= ph_value <= 8.5:

        ph_status = "Within reference range"

    else:

        ph_status = "Outside reference range"

    # --------------------------------------------------------
    # DISSOLVED OXYGEN
    # --------------------------------------------------------

    do_value = row["DO_mg_L"]

    if pd.isna(do_value):

        do_status = "Unavailable"

    elif do_value >= 5:

        do_status = "Meets reference value"

    else:

        do_status = "Below reference value"

    # --------------------------------------------------------
    # BOD: PROVISIONAL
    # --------------------------------------------------------

    bod_value = row["BOD_mg_L"]

    if pd.isna(bod_value):

        bod_status = "Unavailable"

    elif bod_value <= 3:

        bod_status = "Provisionally within reference value"

    else:

        bod_status = "Provisionally above reference value"

    # --------------------------------------------------------
    # FECAL COLIFORM
    # --------------------------------------------------------

    fc_value = row["Fecal_Coliform_MPN_100mL"]

    if pd.isna(fc_value):

        fc_status = "Unavailable"

    elif fc_value <= 500:

        fc_status = "At or below desirable value"

    elif fc_value <= 2500:

        fc_status = "Above desirable, within maximum"

    else:

        fc_status = "Above maximum permissible value"

    # --------------------------------------------------------
    # SAVE ASSESSMENT
    # --------------------------------------------------------

    assessment_rows.append({
        "Station": row["Station"],
        "Sample Date": row["Data Acquisition Time"],
        "pH": ph_value,
        "pH Comparison": ph_status,
        "DO (mg/L)": do_value,
        "DO Comparison": do_status,
        "BOD (mg/L)": bod_value,
        "BOD Comparison (Provisional)": bod_status,
        "Fecal Coliform (MPN/100 mL)": fc_value,
        "Fecal Coliform Comparison": fc_status
    })


assessment_df = pd.DataFrame(assessment_rows)

if not assessment_df.empty:

    st.subheader("Observation-wise Assessment")

    st.dataframe(
        assessment_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        label="📥 Download Assessment Results",
        data=assessment_df.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="cauvery_water_quality_assessment.csv",
        mime="text/csv"
    )

    st.subheader("Summary of Parameter Comparisons")

    sum_col1, sum_col2 = st.columns(2)

    with sum_col1:

        st.write("**pH comparison**")

        st.dataframe(
            assessment_df["pH Comparison"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Observations"),
            use_container_width=True,
            hide_index=True
        )

        st.write("**Dissolved Oxygen comparison**")

        st.dataframe(
            assessment_df["DO Comparison"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Observations"),
            use_container_width=True,
            hide_index=True
        )

    with sum_col2:

        st.write("**BOD comparison — provisional**")

        st.dataframe(
            assessment_df["BOD Comparison (Provisional)"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Observations"),
            use_container_width=True,
            hide_index=True
        )

        st.write("**Fecal Coliform comparison**")

        st.dataframe(
            assessment_df["Fecal Coliform Comparison"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Observations"),
            use_container_width=True,
            hide_index=True
        )

else:

    st.warning(
        "No observations are available for assessment."
    )

st.divider()

# ============================================================
# 14. MISSING DATA ANALYSIS
# ============================================================

st.header("⚠️ 7. Data Availability and Missing Measurements")

st.write(
    """
    Missing measurements limit which water quality analyses can
    be performed. A missing value is not the same as zero.
    """
)

missing_rows = []

for column, label in PARAMETERS.items():

    total_records = len(filtered_df)

    available_records = filtered_df[column].notna().sum()

    missing_records = total_records - available_records

    missing_percentage = (
        (missing_records / total_records) * 100
        if total_records > 0
        else 0
    )

    missing_rows.append({
        "Parameter": label,
        "Available Measurements": int(available_records),
        "Missing Measurements": int(missing_records),
        "Missing Percentage (%)": round(
            missing_percentage,
            2
        )
    })


missing_df = pd.DataFrame(missing_rows)

st.dataframe(
    missing_df,
    use_container_width=True,
    hide_index=True
)

st.info(
    """
    The prepared dataset contains usable observations for pH,
    dissolved oxygen, BOD and fecal coliform.

    Several other parameters have no usable measurements in the
    selected dataset. They are retained as unavailable rather
    than being filled with invented values or zeros.
    """
)

st.divider()

# ============================================================
# 15. RAW OBSERVATION TABLE
# ============================================================

st.header("📋 8. Collected Water Quality Observations")

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
    "Total_Coliform_MPN_100mL"
]

display_columns = [
    column
    for column in display_columns
    if column in filtered_df.columns
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True
)

st.download_button(
    label="📥 Download Filtered Observations",
    data=filtered_df[display_columns].to_csv(
        index=False
    ).encode("utf-8"),
    file_name="cauvery_filtered_observations.csv",
    mime="text/csv"
)

st.divider()

# ============================================================
# 16. PROJECT INFORMATION
# ============================================================

st.header("ℹ️ About This Project")

st.markdown(
    """
    **Project title:** AI-Based Water Quality Assessment and
    Pollution Analysis of the Cauvery River Using KSPCB and CPCB Data.

    **Current implementation:**
    - Data preparation and filtering.
    - Descriptive statistical analysis.
    - Interactive visualizations.
    - Monitoring station comparison.
    - Preliminary reference-criteria assessment.
    - Missing-data analysis.
    - CSV export of filtered observations.

    **Limitations:**
    - Some water quality parameters are unavailable.
    - The BOD test method is not specified in the dataset.
    - The assessment is not a complete water quality classification.
    - This dashboard does not currently train an AI model or
      predict future pollution.
    """
)

st.caption(
    "Academic project | Cauvery River Water Quality Assessment"
)