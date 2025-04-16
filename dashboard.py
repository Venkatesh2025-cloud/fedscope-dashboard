import os
import pandas as pd
import streamlit as st
import plotly.express as px

# Define relative data path
DATA_PATH = "data"

# Show absolute path for debugging
absolute_path = os.path.abspath(DATA_PATH)
st.markdown(f"📁 **Absolute Data Path:** `{absolute_path}`")

try:
    file_list = os.listdir(DATA_PATH)
    st.success("✅ Files in /data folder:")
    st.json(file_list)
except Exception as e:
    st.warning(f"Couldn't list files in data/: {e}")

# Function to load CSVs safely
def load_csv(file_name):
    try:
        file_path = os.path.join(DATA_PATH, file_name)
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"❌ Error: `{file_name}` not found in the data directory.")
        return None
    except Exception as e:
        st.error(f"⚠️ Error loading `{file_name}`: {e}")
        return None

# Load all files
dfs = {
    "available_df": load_csv("city_skill_Available_Talent_projection.csv"),
    "alignment_df": load_csv("city_skill_demand_alignment_live.csv"),
    "decision_df": load_csv("city_skill_decision_table.csv"),
    "layoffs_df": load_csv("federal_layoff_news_with_categories.csv"),
    "fedscope_df": load_csv("fedscope_enriched_summary.csv"),
}

# Stop if any failed
if any(df is None for df in dfs.values()):
    st.stop()

# Unpack
available_df = dfs["available_df"]
alignment_df = dfs["alignment_df"]
decision_df = dfs["decision_df"]
layoffs_df = dfs["layoffs_df"]
fedscope_df = dfs["fedscope_df"]

# === SIDEBAR ===
st.sidebar.header("🧭 Filters")
view_mode = st.sidebar.radio("View Mode", ["National", "City"])

selected_city = None
if view_mode == "City":
    cities = sorted(decision_df["City"].dropna().unique())
    selected_city = st.sidebar.selectbox("Select a City", cities)

agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
selected_agency = st.sidebar.selectbox("Filter by Agency (optional)", ["All"] + agencies)

# === DATA FILTERING ===
if view_mode == "City":
    avail_data = available_df[available_df["Location Name"] == selected_city]
    align_data = alignment_df[alignment_df["Location Name"] == selected_city]
    layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_city, case=False, na=False)]
    fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_city, case=False, na=False)]
    decision_data = decision_df[decision_df["City"] == selected_city]
    label_title = f"📍 City: {selected_city}"
else:
    avail_data = available_df.copy()
    align_data = alignment_df.copy()
    layoff_data = layoffs_df.copy()
    fed_data = fedscope_df.copy()
    decision_data = decision_df.copy()
    label_title = "🇺🇸 National View"

if selected_agency != "All":
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]

# === HEADER ===
st.markdown("""
    <h1 style='text-align: center; color: white; background-color: #003366; padding: 25px; border-radius: 8px'>
    🏛️ Federal Workforce and Skill Availability Dashboard
    </h1>
""", unsafe_allow_html=True)

# === KPIs ===
st.markdown(f"### 📌 Summary Overview — {label_title}")
col1, col2, col3 = st.columns(3)

total_skills = avail_data["Skill Category"].nunique()
total_available = avail_data["Available Talent"].sum()
top_skill = avail_data.loc[avail_data["Available Talent"].idxmax(), "Skill Category"] if not avail_data.empty else "N/A"

col1.metric("🔍 Skill Categories", total_skills)
col2.metric("👥 Available Talent", f"{total_available:,.0f}")
col3.metric("🏆 Most Available Skill", top_skill)

# === TABS ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Talent Availability",
    "Demand vs Supply",
    "Layoff News",
    "Federal Agency Staff",
    "Decision Intelligence"
])

# === TAB 1 ===
with tab1:
    st.subheader(f"📊 Talent Availability by Skill — {label_title}")
    if not avail_data.empty:
        fig = px.bar(
            avail_data.sort_values("Available Talent", ascending=False),
            x="Skill Category", y="Available Talent", color="Available Talent",
            height=450, title="Available Talent by Skill Category"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(avail_data, use_container_width=True)
    else:
        st.warning("No available talent data.")

# === TAB 2 ===
with tab2:
    st.subheader(f"⚖️ Demand-to-Supply Analysis — {label_title}")
    if not align_data.empty:
        fig = px.scatter(
            align_data, x="Skill Category", y="Demand-to-Supply Ratio",
            size="Available Talent", color="Alignment",
            hover_name="Skill Category", height=450,
            title="Demand vs Supply Ratio per Skill"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(align_data, use_container_width=True)
    else:
        st.warning("No demand alignment data.")

# === TAB 3 ===
with tab3:
    st.subheader(f"📰 Layoff Events — {label_title}")
    if not layoff_data.empty:
        st.dataframe(layoff_data[[ 
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No layoff news available.")

# === TAB 4 ===
with tab4:
    st.subheader(f"🏢 Federal Staff Breakdown — {label_title}")
    if not fed_data.empty:
        agg = fed_data.groupby("Occupation Title")["Employee Count"].sum().reset_index()
        fig = px.bar(
            agg.sort_values("Employee Count", ascending=False),
            x="Occupation Title", y="Employee Count",
            title="Federal Employee Count by Occupation", height=450
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fed_data, use_container_width=True)
    else:
        st.warning("No Fedscope data available.")

# === TAB 5 ===
with tab5:
    st.subheader(f"✅ Action Plan View — {label_title}")
    if not decision_data.empty:
        fig = px.bar(
            decision_data.sort_values("Estimated Layoffs", ascending=False),
            x="Skill Category", y="Estimated Layoffs", color="Action",
            hover_data=["Reasoning"], height=450,
            title="Action Plan by Skill Category"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No decision intelligence available.")
