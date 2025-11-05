# monitoring_dashboard.py
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import base64
import re
import os

# ---------------------- CONFIG ----------------------

st.set_page_config(
    page_title="Colleges Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- GOOGLE SHEET CONFIG ----------------------
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1CaRv9M_Xvs0xu0RSWR_NGvNE0SGC3XqCzoEbqQAuoqc/edit"

# ---------------------- UTILS ----------------------

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def merge_duplicate_columns(df: pd.DataFrame):
    """
    Properly merge duplicate columns (like 'Action', 'Action_1', 'Action_2', etc.)
    by taking the first non-empty value in each row across all duplicates.
    Works even if Google Sheets repeated headers multiple times.
    """
    merged_df = df.copy()
    base_map = {}

    for col in merged_df.columns:
        base = re.sub(r'[_\.\s]*\d+$', '', col.strip())
        base_map.setdefault(base, []).append(col)

    for base, cols in base_map.items():
        if len(cols) > 1:
            merged_df[base] = merged_df[cols].apply(
                lambda row: next((x for x in row if pd.notna(x) and str(x).strip() != ''), ''),
                axis=1
            )
            merged_df.drop(columns=[c for c in cols if c != base], inplace=True)

    return merged_df


def load_data():
    """Always load directly from Google Sheet."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(DEFAULT_SHEET_URL).sheet1
    rows = sheet.get_all_values()

    if not rows:
        st.error("No data found in the Google Sheet.")
        st.stop()

    headers = rows[0]
    data = rows[1:]

    # Handle duplicate headers
    unique_headers = []
    seen = {}
    for h in headers:
        if h in seen:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_headers.append(h)

    df = pd.DataFrame(data, columns=unique_headers)

    # Clean column names
    df.columns = [c.strip().replace("-", "_") for c in df.columns]

    # Merge duplicate logical columns
    df = merge_duplicate_columns(df)

    # Ensure essential columns exist
    for col in ['Scale', 'Reason', 'Category']:
        if col not in df.columns:
            df[col] = np.nan

    df['Scale'] = pd.to_numeric(df['Scale'], errors='coerce')

    return df


def multi_filter(df, key):
    opts = ['All'] + sorted(df[key].dropna().astype(str).unique().tolist())
    choice = st.sidebar.multiselect(key, opts, default=['All'])
    if 'All' in choice or not choice:
        return df
    return df[df[key].astype(str).isin(choice)]


# ---------------------- HEADER ----------------------

logo_path = "logo_hed.png"

st.markdown(
    f"""
    <div style="width: 100%; display: flex; justify-content: center; align-items: center; margin-top: -40px;">
        <div style="margin-right: 15px;">
            <img src="data:image/png;base64,{get_base64_image(logo_path)}" 
                 alt="Logo" width="120">
        </div>
        <div style="text-align: center;">
            <h1 style="color: green; font-size: 40px; margin-bottom: 5px;">
                Higher Education Department
            </h1>
            <h4 style="color: black; font-size: 22px; margin-top: 0;">
                Colleges Monitoring Dashboard
            </h4>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------- LOAD DATA ----------------------
df = load_data()

# ---------------------- FILTERS ----------------------

st.sidebar.header("Filters")

# Define filters and any fixed options you want
filter_columns = ['District', 'College Name', 'College Gender', 'College Type', 'Category', 'Action', 'Reason', 'Action By']

# 👇 Define custom allowed options for specific filters
custom_filter_options = {
    "Reason": [
        "Habitual Absentiesm",
        "Proxy Attendance",
        "Staff absent during monitoring visit"
    ]
}

# --- Apply filters ---
for col in filter_columns:
    if col in df.columns:
        # Use predefined options if available, else get unique values from df
        if col in custom_filter_options:
            opts = ['All'] + custom_filter_options[col]
        else:
            opts = ['All'] + sorted(df[col].dropna().astype(str).unique().tolist())

        state_key = f"filter_{col}"
        choice = st.sidebar.multiselect(col, opts, default=['All'], key=state_key)

        if 'All' not in choice and choice:
            df = df[df[col].astype(str).isin(choice)]

# --- Text search ---
text_search = st.sidebar.text_input('Search across all columns', key='Search')
if text_search:
    mask = df.astype(str).apply(lambda row: row.str.contains(text_search, case=False, na=False)).any(axis=1)
    df = df[mask]




# ---------------------- KPI CARDS ----------------------

st.markdown("## Monitoring Action Report Overview")

col1, col2, col3, col4, col5, col6 = st.columns(6)
card_style = """
    background:{color}; padding:20px; border-radius:12px; text-align:center;
    box-shadow:0 4px 8px rgba(0,0,0,0.15); height:150px; display:flex;
    flex-direction:column; justify-content:center;
"""

total_actions = len(df)
unique_colleges = df['College Name'].nunique() if 'College Name' in df.columns else 0
salary_ded = df[df['Action'].str.contains('Salary', case=False, na=False)]
total_salary_ded = int((salary_ded['Salary Deducted'].apply(pd.to_numeric, errors='coerce').sum() if not salary_ded.empty else 0))

facility_updates = df[df['Category'].astype(str).str.contains('Facility', case=False, na=False)]
actions_against_employees = df[df['Action'].astype(str).str.contains('Warning', case=False, na=False)]
proxy_attendance = df[df['Reason'].astype(str).str.contains('Proxy Attendance', case=False, na=False)]

# --- Define new KPI metrics ---
unvisited_college_actions = df[df["Action"].str.contains("Explanation", case=False, na=False)]
habitual_absenteeism_actions = df[df["Reason"].str.contains("Habitual Absentiesm", case=False, na=False)]

# --- Prepare KPI data ---
kpis = [
    ("#16a085", total_actions, "Total Actions"),
    ("#2980b9", unique_colleges, "Colleges"),
    ("#d35400", f"PKR {total_salary_ded}", "Salary Deduction"),
    ("#8e44ad", len(facility_updates), "Facility Updates"),
    ("#c0392b", len(actions_against_employees), "Warnings Issued"),
    ("#e74c3c", len(proxy_attendance), "Proxy Attendance Cases"),
    ("#27ae60", len(unvisited_college_actions), "Explanation Called"),
    ("#f39c12", len(habitual_absenteeism_actions), "Habitual Absenteeism Action"),
]

# --- Create layout: 2 rows × 4 columns with spacing ---
for row_start in range(0, len(kpis), 4):
    cols = st.columns(4)
    for i, (color, value, label) in enumerate(kpis[row_start:row_start + 4]):
        with cols[i]:
            st.markdown(
                f"""
                <div style="{card_style.format(color=color)}">
                    <h2 style="color:white; margin:0;">{value}</h2>
                    <p style="color:white; margin:0; font-weight:600;">{label}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    # Add small vertical space between rows
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------- CHARTS ----------------------

if 'Action' in df.columns:
    valid_actions = df['Action'].dropna().astype(str).str.strip()
    valid_actions = valid_actions[valid_actions != '']  # remove empty strings

    if not valid_actions.empty:
        st.subheader('Actions Overview')
        cat_counts = valid_actions.value_counts().reset_index()
        cat_counts.columns = ['Action', 'Count']
        fig = px.pie(cat_counts, values='Count', names='Action', hole=0.3)
        fig.update_traces(textinfo='label+value', textfont=dict(size=14, family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------------------- TABLE & DOWNLOAD ----------------------

st.subheader("Detailed Records")

df_display = df.dropna(axis=1, how='all')
df_display = df_display.loc[:, ~(df_display.astype(str).apply(lambda x: x.str.strip()).eq('').all())]
df_display.drop(columns=['Timestamp', 'Email Address'], errors='ignore', inplace=True)
st.dataframe(df_display, height=400)

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_display)
st.download_button("Download Filtered Data as CSV", data=csv, file_name="monitoring_filtered.csv", mime="text/csv")
