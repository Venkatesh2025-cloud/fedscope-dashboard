import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Streamlit Config ===
st.set_page_config(page_title="Federal Layoff Intelligence", layout="wide", page_icon="📈")

# === CSS Styling ===
st.markdown("""
    <style>
        body {
            background-color: #f5f7fb;
        }
        .main-header {
            font-size: 40px;
            font-weight: 800;
            margin-bottom: 0.5rem;
            color: #1f2937;
        }
        .sub-header {
            font-size: 18px;
            color: #6b7280;
            margin-bottom: 2rem;
        }
        .metric-box {
            background-color: white;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }
        .metric-box h3 {
            font-size: 14px;
            color: #6b7280;
            margin: 0;
        }
        .metric-box p {
            font-size: 28px;
            margin: 0;
            font-weight: bold;
            color: #3b82f6;
        }
        .section-card {
            background: white;
            padding: 1.5rem;
            margin-top: 1rem;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            box-shadow: 0px 3px 10px rgba(0,0,0,0.03);
        }
    </style>
""", unsafe_allow_html=True)

# === Load Data ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

def load_csv(file):
    path = os.path.join(DATA_PATH, file)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error(f"Missing file: {file}")
        return pd.DataFrame()

# === Load datasets ===
available_df = load_csv("city_skill_Available_Talent_projection.csv")
alignment_df = load_csv("city_skill_demand_alignment_live.csv")
decision_df = load_csv("city_skill_decision_table.csv")
layoffs_df = load_csv("federal_layoff_news_with_categories.csv")
fedscope_df = load_csv("fedscope_enriched_summary.csv")

# === Sidebar filters ===
with st.sidebar:
    st.title("📌 Filters")
    states = sorted(decision_df["City"].dropna().unique())
    selected_state = st.selectbox("Select State", states)
    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.selectbox("Select Agency", ["All"] + agencies)

# === Filter Data ===
decision_data = decision_df[decision_df["City"] == selected_state]
layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]
fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]

if selected_agency != "All":
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]

# === Page Header ===
st.markdown("<div class='main-header'>📊 Federal Layoff Intelligence Dashboard</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Real-time insight for <strong>{selected_state}</strong> staffing impact</div>", unsafe_allow_html=True)

# === KPIs ===
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_feds = fed_data["Employee Count"].sum()
layoff_pct = (est_layoffs / total_feds) * 100 if total_feds else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"<div class='metric-box'><h3>Estimated Layoffs</h3><p>{est_layoffs:,.0f}</p></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='metric-box'><h3>Top Skill Affected</h3><p>{top_skill}</p></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='metric-box'><h3>Layoff % of Workforce</h3><p>{layoff_pct:.2f}%</p></div>", unsafe_allow_html=True)

# === Tabs ===
tab1, tab2, tab3 = st.tabs(["📈 Workforce Overview", "📉 Layoff Trends", "📰 Layoff News"])

# === Tab 1: Workforce Overview ===
with tab1:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📌 Top 10 Occupations")
    if not fed_data.empty:
        chart = fed_data.groupby("Occupation Title")["Employee Count"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(chart, x="Occupation Title", y="Employee Count", color_discrete_sequence=["#3b82f6"])
        fig.update_layout(xaxis_title="", yaxis_title="Employees", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fed_data, use_container_width=True)
    else:
        st.info("No workforce data available.")
    st.markdown("</div>", unsafe_allow_html=True)

# === Tab 2: Layoff Trends ===
with tab2:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📉 Skill Categories at Risk")
    if not decision_data.empty:
        chart = decision_data.sort_values("Estimated Layoffs", ascending=False).head(10)
        fig = px.bar(chart, x="Skill Category", y="Estimated Layoffs", color="Action", color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(xaxis_title="", yaxis_title="Estimated Layoffs", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff data found.")
    st.markdown("</div>", unsafe_allow_html=True)

# === Tab 3: Layoff News ===
with tab3:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📰 Recent News Articles")
    if not layoff_data.empty:
        layoff_data["Date"] = pd.to_datetime(layoff_data["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        st.dataframe(layoff_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No articles found for this state.")
    st.markdown("</div>", unsafe_allow_html=True)
