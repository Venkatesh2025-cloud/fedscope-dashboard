import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Federal Layoff Intelligence Platform",
    layout="wide",
    page_icon="📊"
)

# === Custom CSS for SaaS Look ===
st.markdown("""
    <style>
        .big-title {
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2em;
            color: #6c757d;
            margin-top: -10px;
            margin-bottom: 30px;
        }
        .kpi-card {
            padding: 1rem;
            border-radius: 10px;
            background-color: #f8f9fa;
            text-align: center;
            border: 1px solid #dee2e6;
        }
    </style>
""", unsafe_allow_html=True)

# === Load Data ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

def load_csv(file_name):
    path = os.path.join(DATA_PATH, file_name)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error(f"❌ File not found: {file_name}")
        return pd.DataFrame()

available_df = load_csv("city_skill_Available_Talent_projection.csv")
alignment_df = load_csv("city_skill_demand_alignment_live.csv")
decision_df = load_csv("city_skill_decision_table.csv")
layoffs_df = load_csv("federal_layoff_news_with_categories.csv")
fedscope_df = load_csv("fedscope_enriched_summary.csv")

# === Sidebar ===
with st.sidebar:
    st.header("📍 Filters")
    states = sorted(decision_df["City"].dropna().unique())
    selected_state = st.selectbox("Select a State", states)

    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.selectbox("Filter by Agency", ["All"] + agencies)

    st.markdown("---")
    st.caption("🔄 Data auto-refreshes every 24h")
    st.caption("🧠 Powered by Streamlit + Plotly")

# === Filtered Data ===
avail_data = available_df[available_df["Location Name"] == selected_state]
decision_data = decision_df[decision_df["City"] == selected_state]
layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]
fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]

if selected_agency != "All":
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]

# === Header ===
st.markdown("<div class='big-title'>📊 Federal Layoff Intelligence</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>Data-driven insights for workforce trends in <b>{selected_state}</b></div>", unsafe_allow_html=True)

# === KPI Cards ===
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_feds = fed_data["Employee Count"].sum()
layoff_pct = (est_layoffs / total_feds) * 100 if total_feds else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"<div class='kpi-card'>👥<br><b>Estimated Layoffs</b><br>{est_layoffs:,.0f}</div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'>🏆<br><b>Most Affected Skill</b><br>{top_skill}</div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'>📉<br><b>Impact %</b><br>{layoff_pct:.2f}%</div>", unsafe_allow_html=True)

# === Tabs ===
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Workforce Overview",
    "📉 Layoff Intelligence",
    "📰 News & Articles",
    "🧠 AI Suggestions"
])

# === Tab 1: Workforce Overview ===
with tab1:
    st.subheader("Federal Workforce Breakdown")
    if not fed_data.empty:
        occ_chart = (
            fed_data.groupby("Occupation Title")["Employee Count"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        fig_occ = px.bar(occ_chart, x="Occupation Title", y="Employee Count", title="Top Occupations in Federal Agencies")
        st.plotly_chart(fig_occ, use_container_width=True)
        st.dataframe(fed_data, use_container_width=True)
    else:
        st.info("No workforce data for the selected filters.")

# === Tab 2: Layoff Intelligence ===
with tab2:
    st.subheader("Skills at Risk")
    if not decision_data.empty:
        fig_skill = px.bar(
            decision_data.sort_values("Estimated Layoffs", ascending=False).head(10),
            x="Skill Category",
            y="Estimated Layoffs",
            color="Action",
            title="Top Skills by Estimated Layoffs"
        )
        st.plotly_chart(fig_skill, use_container_width=True)

        bubble = decision_data.groupby(["City", "Skill Category"])["Estimated Layoffs"].sum().reset_index()
        fig_bubble = px.scatter(bubble, x="City", y="Skill Category", size="Estimated Layoffs", title="Layoff Distribution by City & Skill", size_max=60)
        st.plotly_chart(fig_bubble, use_container_width=True)
        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff intelligence for this region.")

# === Tab 3: News & Articles ===
with tab3:
    st.subheader("Related News & Articles")
    if not layoff_data.empty:
        layoff_data['Date'] = pd.to_datetime(layoff_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        st.dataframe(layoff_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No news articles found for this selection.")

# === Tab 4: AI-Powered Skill Suggestions ===
with tab4:
    st.subheader("🧠 Smart Skill Suggestions & Insights")

    if not decision_data.empty:
        top_skills = decision_data.groupby("Skill Category")["Estimated Layoffs"].sum().sort_values(ascending=False)
        top_actions = decision_data["Action"].value_counts()
        risky_roles = decision_data["Skill Category"].value_counts().head(5).index.tolist()

        st.markdown("### 📌 Summary")
        st.info(f"""
- Most layoffs are occurring in **{top_skills.index[0]}**
- Common agency response: **{top_actions.index[0]}**
- Top impacted skill categories: **{", ".join(risky_roles)}**
        """)

        st.markdown("### 💡 Suggested Skill Development Areas")
        for skill in top_skills.index[:3]:
            st.success(f"✅ Consider upskilling in **{skill}** to align with shifting agency priorities.")

        st.markdown("### 🧭 Strategy Tips")
        st.write("""
- Cross-train teams on digital tools, data analysis, or policy strategy.
- Encourage flexible skills across adjacent categories (e.g., "Cybersecurity" ⇨ "Cloud Security").
- Monitor demand data in the next cycle for shifting agency needs.
        """)
    else:
        st.warning("No actionable layoff data available to generate suggestions.")
