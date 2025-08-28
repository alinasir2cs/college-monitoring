import base64
import os
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
# Load data
from streamlit_autorefresh import st_autorefresh
# -----------------------------
# Page Config
# -----------------------------
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


st.set_page_config(page_title="College Facility Dashboard", layout="wide")

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
            <h4 style="color: black; font-size: 18px; margin-top: 0; white-space: nowrap;">
                Special Monitoring Drive of Govt. Colleges (College cleanliness and readiness)
            </h4>
        </div>
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

st_autorefresh(interval=300 * 1000, key="datarefresh")
data = pd.DataFrame(ws.get_all_records())
data.columns = [col.strip() for col in data.columns]

# -----------------------------
# Column references by position
# -----------------------------
col_district = data.columns[2]   # C
col_gender = data.columns[3]     # D (assume gender col here, adjust if diff)
col_type = data.columns[4]       # E (assume college type col)
col_college = data.columns[5]    # F
col_officer = data.columns[18]   # S (if exists)

# -----------------------------
# Facility Columns
# -----------------------------
facility_cols = {
    "Classrooms cleaned, ventilated, and furniture arranged?": "class.jpg",
    "Toilets cleaned, functional, and with water supply?": "toilets.jpg",
    "Drinking water availability and quality check?": "water.jpg",
    "Electricity and lighting functional in classrooms and labs?": "electricity.jpg",
    "Campus grounds cleaned (lawns, courtyards, pathways)?": "grounds.jpg",
    "Boundary wall and gates secured (no open or broken sections)?": "boundry.jpg",
    "Science labs ready with basic equipment and chemicals?": "science.jpg",
    "IT/Computer labs functional (systems, internet, power)?": "it.jpg",
    "Library operational clean and open for students?": "library.jpg",
    "Biometric Attendance Device installed and functional?": "bio.jpg",
    "Principal and administration staff presence on reopening day?": 'attendance.jpg',
    "Students attendance registers available and ready?": "students.jpg"
}
facility_label = [
    "Classrooms cleaned, ventilated?",
    "Toilets cleaned, functional?",
    "Drinking water availability?",
    "Electricity and lighting functional?",
    "Campus grounds cleaned?",
    "Boundary wall and gates secured?",
    "Science labs readiness?",
    "IT/Computer labs functional?",
    "Library operational?",
    "Biometric Attendance functional?",
    'Staff Presence?',
    "Student Attendance Registers Ready?"
]

# Convert yes/no → 1/0
for col in facility_cols.keys():
    data[col] = data[col].apply(lambda x: 1 if str(x).strip().lower() == "yes" else 0)

# -----------------------------
# Top Summary Cards
# -----------------------------
#st.markdown("## 🎓 College Monitoring Overview")
col1, col2, col3, col4, col5 = st.columns(5)

# 1st column → Total Colleges
with col1:
    st.markdown(f"""
    <div style="background:#8e44ad; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white;">{len(data)}</h2>
        <p style="color:white;">Total Colleges Visited</p>
    </div>
    """, unsafe_allow_html=True)

# 2nd column → General
with col2:
    st.markdown(f"""
    <div style="background:#3498db; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white;">{(data[col_type]=='General').sum()}</h2>
        <p style="color:white;">General Colleges</p>
    </div>
    """, unsafe_allow_html=True)

# 3rd column → Commerce
with col3:
    st.markdown(f"""
    <div style="background:#808080; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white;">{(data[col_type]=='Commerce').sum()}</h2>
        <p style="color:white;">Commerce Colleges</p>
    </div>
    """, unsafe_allow_html=True)

# 4th column → Male
with col4:
    st.markdown(f"""
    <div style="background:#2ecc71; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white;">{(data[col_gender]=='Male').sum()}</h2>
        <p style="color:white;">Male Colleges</p>
    </div>
    """, unsafe_allow_html=True)

# 5th column → Female
with col5:
    st.markdown(f"""
    <div style="background:#e84393; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white;">{(data[col_gender]=='Female').sum()}</h2>
        <p style="color:white;">Female Colleges</p>
    </div>
    """, unsafe_allow_html=True)

# Initialize defaults before widgets
if "district" not in st.session_state:
    st.session_state["district"] = "All"
if "gender" not in st.session_state:
    st.session_state["gender"] = "All"
if "type" not in st.session_state:
    st.session_state["type"] = "All"
if "compliance" not in st.session_state:
    st.session_state["compliance"] = "All"

# -----------------------------
# Filters with Styled Buttons
# -----------------------------
st.markdown("### 🔍 Filters")

# Inject CSS for button styling
st.markdown("""
    <style>
    div.stButton > button:first-child {
        padding: 0.45rem 1.2rem;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        margin-top: 28px; /* aligns with selectbox */
    }
    div.stButton.apply-btn > button:first-child {
        background-color: #4CAF50;
        color: white;
        border: none;
    }
    div.stButton.apply-btn > button:first-child:hover {
        background-color: #45a049;
        color: white;
    }
    div.stButton.clear-btn > button:first-child {
        background-color: #f44336;
        color: white;
        border: none;
    }
    div.stButton.clear-btn > button:first-child:hover {
        background-color: #d32f2f;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

f1, f2, f3, f4, f5, f6 = st.columns([2, 2, 2, 2, 1, 1])

with f1:
    selected_district = st.selectbox(
        "Select District",
        options=["All"] + list(data[col_district].unique()),
        key="district"
    )
with f2:
    selected_gender = st.selectbox(
        "Select Gender",
        options=["All"] + list(data[col_gender].unique()),
        key="gender"
    )
with f3:
    selected_type = st.selectbox(
        "Select College Type",
        options=["All"] + list(data[col_type].unique()),
        key="type"
    )

with f4:
    selected_compliance = st.selectbox(
        "Compliance Filter",
        options=["All", "<= 50%", "> 50%"],
        key="compliance"
    )

with f5:
    apply = st.button("Apply Filters", key="apply")

with f6:
    clear = st.button("Clear Filters", key="clear")

# Custom CSS
st.markdown("""
<style>
/* Make all buttons consistent */
div[data-testid="stButton"] > button {
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}

/* First button (Apply Filters) → Yellow */
div[data-testid="stButton"]:nth-of-type(1) > button {
    background-color: #FFD700 !important;  /* Yellow */
    color: black !important;
}

/* Second button (Clear Filters) → Grey */
div[data-testid="stButton"]:nth-of-type(2) > button {
    background-color: #A9A9A9 !important;  /* Grey */
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Apply filtering
# -----------------------------
filtered = data.copy()

# Calculate compliance early for filtering
filtered["Compliance %"] = (filtered[list(facility_cols.keys())].mean(axis=1) * 100).round(0)
if apply:
    if selected_district != "All":
        filtered = filtered[filtered[col_district] == selected_district]
    if selected_gender != "All":
        filtered = filtered[filtered[col_gender] == selected_gender]
    if selected_type != "All":
        filtered = filtered[filtered[col_type] == selected_type]
    if selected_compliance == "<= 50%":
        filtered = filtered[filtered["Compliance %"] <= 50]
    elif selected_compliance == "> 50%":
        filtered = filtered[filtered["Compliance %"] > 50]

if clear:
    for key in ["district", "gender", "type", "compliance"]:
        st.session_state.pop(key, None)
    st.rerun()



# -----------------------------
# Facility Icons with % Compliance
# -----------------------------
#st.markdown("### 🏫 Facility Compliance Overview")
cols = st.columns(6)

for i, (facility, icon_file) in enumerate(facility_cols.items()):
    yes_rate = int((filtered[facility].mean() * 100) if len(filtered) > 0 else 0)
    icon_base64 = get_base64_image(icon_file)

    with cols[i % 6]:
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:10px; text-align:center; min-height:180px;">
            <p style="color:#2c3e50; font-size:14px; font-weight:bold; margin-bottom:8px;">{facility_label[i]}</p>
            <img src="data:image/png;base64,{icon_base64}" width="100" style="display:block; margin:auto; margin-bottom:6px;">
            <p style="color:black; font-size:25px; font-weight:bold; margin:0; display:block; text-align:center; margin:auto;">
    {yes_rate}%
</p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------
# Detailed College List
# -----------------------------
st.markdown("### 📋 Detailed College List")

# Calculate compliance per row
filtered["Compliance %"] = (filtered[list(facility_cols.keys())].mean(axis=1) * 100).round(0)
def compliance_badge(val):
    """Return HTML span with background only behind text (not whole cell)."""
    try:
        num = int(str(val).replace('%', ''))
    except:
        return val  # if not a number, return as is

    if num <= 50:
        color = "#ffcccc"
        text_color = "#b30000"
    else:
        color = "#ccffcc"
        text_color = "#006600"

    return (
        f"<span style='background-color:{color}; color:{text_color}; "
        f"font-weight:bold; border-radius:4px; padding:2px 6px; "
        f"display:inline-block; text-align:center;'>{val}</span>"
    )


# Prepare dataframe
styled_df = filtered[
    [col_college, col_district, col_gender, col_type, "Compliance %", col_officer]
].copy()

# Format percentages nicely
styled_df["Compliance %"] = styled_df["Compliance %"].apply(
    lambda x: f"{int(x)}%" if float(x).is_integer() else f"{x:.1f}%"
)

# Apply badge formatting
styled_df["Compliance %"] = styled_df["Compliance %"].apply(compliance_badge)

# Render as HTML table (escape=False lets HTML work)
html_table = styled_df.to_html(escape=False, index=False)

# Force table width 100% and LTR headers
html_table = html_table.replace(
    "<table",
    '<table style="width:100%;"'
).replace(
    "<th",
    '<th style="direction:ltr; text-align:left;"'
)

st.markdown(
    f"""
    <div style="max-height:500px; overflow-y:auto; overflow-x:auto; width:100%;">
        {html_table}
    </div>
    """,
    unsafe_allow_html=True,
)


