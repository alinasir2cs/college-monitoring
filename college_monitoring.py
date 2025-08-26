import os
import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="College Facility Dashboard", layout="wide")

# -----------------------------
# Banner with College Symbol
# -----------------------------
st.markdown(
    """
    <div style="width: 100%; background-color: #4B7BEC; padding: 15px; display: flex; align-items: center; border-radius: 10px;">
        <img src="https://tse2.mm.bing.net/th/id/OIP.Nnr8QO-hQeDzRbpGERuXegHaFj?rs=1&pid=ImgDetMain&o=7&rm=3" 
             alt="College" style="height:60px; margin-right:20px;">
        <h1 style="color:white; margin:0;">College Facility Monitoring Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Google Sheets Authentication
# -----------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
gc = gspread.authorize(creds)

sheet_name = "Special Monitoring of Govt. Colleges  (Responses)"
worksheet_name = "Form Responses 1"
sh = gc.open(sheet_name)
ws = sh.worksheet(worksheet_name)

# Load data
data = pd.DataFrame(ws.get_all_records())
data.columns = [col.strip() for col in data.columns]

# -----------------------------
# Data Preprocessing
# -----------------------------
facility_cols = [
    "Classrooms cleaned, ventilated, and furniture arranged?",
    "Toilets cleaned, functional, and with water supply?",
    "Drinking water availability and quality check?",
    "Electricity and lighting functional in classrooms and labs?",
    "Campus grounds cleaned (lawns, courtyards, pathways)?",
    "Boundary wall and gates secured (no open or broken sections)?",
    "Science labs ready with basic equipment and chemicals?",
    "IT/Computer labs functional (systems, internet, power)?",
    "Library operational clean and open for students?",
    "Biometric Attendance Device installed and functional?",
    "Students attendance registers available and ready?",
    "Principal and administration staff presence on reopening day?"
]

for col in facility_cols:
    data[col] = data[col].apply(lambda x: 1 if str(x).strip().lower() == "yes" else 0)

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

# District filter
districts = data["Select District"].unique()
selected_district = st.sidebar.selectbox("Select District", options=["All"] + list(districts))

if selected_district != "All":
    filtered_data = data[data["Select District"] == selected_district]
else:
    filtered_data = data

# College filter
colleges = filtered_data["Provide College name"].unique()
selected_college = st.sidebar.selectbox("Select College", options=["All"] + list(colleges))

if selected_college != "All":
    filtered_data = filtered_data[filtered_data["Provide College name"] == selected_college]

# Monitoring Officer filter
if "Monitoring Officer Name" in data.columns:   # make sure column exists
    officers = filtered_data["Monitoring Officer Name"].unique()
    selected_officer = st.sidebar.selectbox("Select Monitoring Officer", options=["All"] + list(officers))

    if selected_officer != "All":
        filtered_data = filtered_data[filtered_data["Monitoring Officer Name"] == selected_officer]

# Final filtered data for downstream usage
college_data = filtered_data

# -----------------------------
# Metrics Cards
# -----------------------------
st.markdown("### 📈 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Districts", len(filtered_data["Select District"].unique()))
col2.metric("Total Colleges", len(filtered_data["Provide College name"].unique()))
col3.metric("Total Responses", len(filtered_data))

# -----------------------------
# Tabs for District / College Analysis
# -----------------------------
tabs = st.tabs(["District Analysis", "College Analysis"])

# --- District Analysis Tab ---
with tabs[0]:
    st.subheader("Facility Summary (District Level)")

    # --- Horizontal Bar Chart ---
    district_summary = filtered_data[facility_cols].sum().sort_values()
    fig_bar = px.bar(
        x=district_summary.values,
        y=district_summary.index,
        orientation='h',
        labels={'x': 'Count of Yes', 'y': 'Facility'},
        title=f"Facility Availability in {selected_district if selected_district != 'All' else 'All Districts'}",
        template="plotly_dark",
        color=district_summary.values,
        color_continuous_scale=["#ff7f0e", "#1f77b4"]  # orange → blue
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Pie Charts (2 per row) ---
    st.subheader("Overall Facility Status Pie Charts")
    cols = st.columns(2)  # define 2 columns for pie charts

    for i, col in enumerate(facility_cols):
        yes_count = filtered_data[col].sum()
        no_count = len(filtered_data) - yes_count

        fig_pie = px.pie(
            names=["Yes", "No"],
            values=[yes_count, no_count],
            title=f"{col} ({selected_district if selected_district != 'All' else 'All Districts'})",
            color=["Yes", "No"],
            color_discrete_map={"Yes": "#1f77b4", "No": "#ff7f0e"}
        )

        with cols[i % 2]:  # alternate placement across 2 columns
            st.plotly_chart(fig_pie, use_container_width=True)

# --- College Analysis Tab ---
with tabs[1]:
    st.subheader("Facility Summary (College Level)")

    # --- Horizontal Bar Chart ---
    college_summary = college_data[facility_cols].sum().sort_values()
    fig_bar_college = px.bar(
        x=college_summary.values,
        y=college_summary.index,
        orientation='h',
        labels={'x': 'Count of Yes', 'y': 'Facility'},
        title=f"Facility Availability in {selected_college if selected_college != 'All' else 'All Colleges'}",
        template="plotly_dark",
        color=college_summary.values,
        color_continuous_scale=["#ff7f0e", "#1f77b4"]  # orange → blue
    )
    st.plotly_chart(fig_bar_college, use_container_width=True)

    # --- Pie Charts (2 per row) ---
    st.subheader("Overall Facility Status Pie Charts")
    cols = st.columns(2)  # define 2 columns for pie charts

    for i, col in enumerate(facility_cols):
        yes_count = college_data[col].sum()
        no_count = len(college_data) - yes_count

        fig_pie = px.pie(
            names=["Yes", "No"],
            values=[yes_count, no_count],
            title=f"{col} ({selected_college if selected_college != 'All' else 'All Colleges'})",
            color=["Yes", "No"],
            color_discrete_map={"Yes": "#1f77b4", "No": "#ff7f0e"}
        )

        with cols[i % 2]:
            st.plotly_chart(fig_pie, use_container_width=True)

    # Collapsible raw data table
    with st.expander("Show Raw College Data Table"):
        st.dataframe(college_data, height=400)




