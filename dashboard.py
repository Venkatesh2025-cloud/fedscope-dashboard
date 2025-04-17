import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Streamlit Config ===
st.set_page_config(page_title="Federal Layoff Intelligence", layout="wide", page_icon="📈")

# === Custom CSS Styling ===
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafd;
        }
        .main-title {
            font-size: 34px;
            font-weight: 700;
            color: #2c3e50;
            padding: 0.5rem 0 0.2rem 0;
        }
        .kpi-box {
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 20px;
            text-align: center;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.03);
        }
        .kpi-box h3 {
            font-size: 15px;
            color: #6c757d;
        }
        .kpi-box p {
            font-size: 24px;
            margin: 0;
            font-weight: 600;
            color: #3f8efc;
        }
        .callout {
            background-color: #e8f1ff;
            border-left: 5px solid #3f8efc;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# === Load Data ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

def load_csv(filename):
    path = os.path.join(DATA_PATH, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error(f"Missing file: {filename}")
        return pd.DataFrame()

# === Datasets ===
available_df = load_csv("city_skill_Available_Talent_projection.csv")
alignment_df = load_csv("city_skill_demand_alignment_live.csv")
decision_df = load_csv("city_skill_decision_table.csv")
layoffs_df = load_csv("federal_layoff_news_with_categories.csv")
fedscope_df = load_csv("fedscope_enriched_summary.csv")

# === Sidebar ===
with st.sidebar:
    st.title("📍 Filters")
    states = sorted(decision_df["City"].dropna().unique())
    selected_state = st.selectbox("Select a State", states)
    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.selectbox("Select Agency", ["All"] + agencies)

# === Filtered Data ===
decision_data = decision_df[decision_df["City"] == selected_state]
layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]
fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]

if selected_agency != "All":
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]

# === Header ===
st.markdown("<div class='main-title'>📈 Federal Layoff Intelligence</div>", unsafe_allow_html=True)

# === Callout Box ===
st.markdown("""
<div class="callout">
    💡 <strong>Insight:</strong> View federal agency layoff projections, most affected roles, and organizational staffing data by region.
</div>
""", unsafe_allow_html=True)

# === KPIs ===
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_feds = fed_data["Employee Count"].sum()
layoff_pct = (est_layoffs / total_feds) * 100 if total_feds else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""
        <div class="kpi-box">
            <h3>Estimated Layoffs</h3>
            <p>{est_layoffs:,.0f}</p>
        </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
        <div class="kpi-box">
            <h3>Top Skill at Risk</h3>
            <p>{top_skill}</p>
        </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
        <div class="kpi-box">
            <h3>Layoff Impact (%)</h3>
            <p>{layoff_pct:.2f}%</p>
        </div>
    """, unsafe_allow_html=True)

# === Tabs ===
tab1, tab2, tab3 = st.tabs(["🏢 Workforce", "📉 Layoffs", "📰 News"])

# === Tab 1: Workforce Overview ===
with tab1:
    st.subheader("Top Occupations by Workforce")
    if not fed_data.empty:
        occ_chart = fed_data.groupby("Occupation Title")["Employee Count"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(occ_chart, x="Occupation Title", y="Employee Count", color_discrete_sequence=["#3f8efc"])
        fig.update_layout(title="Top 10 Occupations", xaxis_title="", yaxis_title="Employees")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fed_data, use_container_width=True)
    else:
        st.info("No workforce data available.")

# === Tab 2: Layoffs ===
with tab2:
    st.subheader("Most Impacted Skills")
    if not decision_data.empty:
        chart = decision_data.sort_values("Estimated Layoffs", ascending=False).head(10)
        fig = px.bar(chart, x="Skill Category", y="Estimated Layoffs", color="Action", color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(title="Layoff Risk by Skill", xaxis_title="", yaxis_title="Layoffs")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff data available.")

# === Tab 3: Layoff News ===
with tab3:
    st.subheader("Related News")
    if not layoff_data.empty:
        layoff_data["Date"] = pd.to_datetime(layoff_data["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        st.dataframe(layoff_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No news found.")
