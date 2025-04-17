import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Streamlit Page Config ===
st.set_page_config(
    page_title="Federal Layoff Intelligence Dashboard",
    layout="wide",
    page_icon="📊"
)

# === Custom CSS ===
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        .main-title {
            font-size: 36px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 16px;
            text-align: center;
            color: #6c757d;
            margin-bottom: 25px;
        }
        .kpi-card {
            padding: 1rem;
            border-radius: 12px;
            background-color: #f0f2f6;
            text-align: center;
            border: 1px solid #d3d3d3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        .kpi-card h2 {
            font-size: 20px;
            margin: 5px 0;
        }
        .kpi-card p {
            font-size: 28px;
            margin: 0;
            font-weight: bold;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# === Load Data Function ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

def load_csv(filename):
    path = os.path.join(DATA_PATH, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error(f"Missing file: {filename}")
        return pd.DataFrame()

# === Load All Datasets ===
available_df = load_csv("city_skill_Available_Talent_projection.csv")
alignment_df = load_csv("city_skill_demand_alignment_live.csv")
decision_df = load_csv("city_skill_decision_table.csv")
layoffs_df = load_csv("federal_layoff_news_with_categories.csv")
fedscope_df = load_csv("fedscope_enriched_summary.csv")

# === Sidebar Filters ===
with st.sidebar:
    st.title("🔍 Filter Data")
    states = sorted(decision_df["City"].dropna().unique())
    selected_state = st.selectbox("Select State", states)

    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.selectbox("Select Agency", ["All"] + agencies)

    st.markdown("---")
    st.caption("🕒 Data refreshes daily")

# === Filter Data ===
avail_data = available_df[available_df["Location Name"] == selected_state]
decision_data = decision_df[decision_df["City"] == selected_state]
layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]
fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]

if selected_agency != "All":
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]

# === Header ===
st.markdown("<div class='main-title'>📊 Federal Layoff Intelligence</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>Analyzing federal workforce disruptions in <strong>{selected_state}</strong></div>", unsafe_allow_html=True)

# === KPI Cards ===
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_feds = fed_data["Employee Count"].sum()
layoff_pct = (est_layoffs / total_feds) * 100 if total_feds else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <h2>Estimated Layoffs</h2>
        <p>{est_layoffs:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <h2>Top Affected Skill</h2>
        <p>{top_skill}</p>
    </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <h2>Layoff Impact</h2>
        <p>{layoff_pct:.2f}%</p>
    </div>
    """, unsafe_allow_html=True)

# === Tabs ===
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Workforce Overview",
    "📉 Layoff Intelligence",
    "📰 Layoff News",
    "🧠 AI Suggestions"
])

# === Tab 1: Workforce Overview ===
with tab1:
    st.subheader("Top Federal Occupations")
    if not fed_data.empty:
        chart = fed_data.groupby("Occupation Title")["Employee Count"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(chart, x="Occupation Title", y="Employee Count", title="Top 10 Occupations")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fed_data, use_container_width=True)
    else:
        st.info("No workforce data available for this selection.")

# === Tab 2: Layoff Intelligence ===
with tab2:
    st.subheader("At-Risk Skill Categories")
    if not decision_data.empty:
        fig = px.bar(decision_data.sort_values("Estimated Layoffs", ascending=False).head(10),
                     x="Skill Category", y="Estimated Layoffs", color="Action",
                     title="Skills Most Affected by Layoffs")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff projections for this selection.")

# === Tab 3: News ===
with tab3:
    st.subheader("Recent Layoff Articles")
    if not layoff_data.empty:
        layoff_data["Date"] = pd.to_datetime(layoff_data["Date"], errors='coerce').dt.strftime('%Y-%m-%d')
        st.dataframe(layoff_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No news found for this selection.")

# === Tab 4: AI-Powered Suggestions ===
with tab4:
    st.subheader("Smart Skill Suggestions & Strategy")
    if not decision_data.empty:
        top_skills = decision_data.groupby("Skill Category")["Estimated Layoffs"].sum().sort_values(ascending=False)
        top_actions = decision_data["Action"].value_counts()
        risky_skills = decision_data["Skill Category"].value_counts().head(5).index.tolist()

        st.markdown("### 🔍 Summary")
        st.info(f"""
- Highest risk skill: **{top_skills.index[0]}**
- Most common response: **{top_actions.index[0]}**
- Skills most impacted: **{", ".join(risky_skills)}**
        """)

        st.markdown("### 💡 Recommendations")
        for skill in top_skills.index[:3]:
            st.success(f"🔧 Upskill in **{skill}** to mitigate future risk.")

        st.markdown("### 📌 Strategy Tips")
        st.write("""
- Focus on hybrid/transferable skills.
- Align training with growth areas in digital, policy, and tech.
- Monitor quarterly shifts in demand vs. supply by region.
        """)
    else:
        st.warning("Not enough data to generate suggestions.")
