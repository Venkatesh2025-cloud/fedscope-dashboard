import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Federal Layoff Intelligence", layout="wide")

# === Paths ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

# === Load Data ===
available_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_Available_Talent_projection.csv"))
alignment_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_demand_alignment_live.csv"))
decision_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_decision_table.csv"))
layoffs_df = pd.read_csv(os.path.join(DATA_PATH, "federal_layoff_news_with_categories.csv"))
fedscope_df = pd.read_csv(os.path.join(DATA_PATH, "fedscope_enriched_summary.csv"))

# === Sidebar ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Seal_of_the_United_States.svg/800px-Seal_of_the_United_States.svg.png", width=100)
    st.header("🧭 Navigation")
    states = sorted(decision_df["City"].dropna().unique())
    selected_state = st.selectbox("📍 Select a State", states)

    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.selectbox("🏛️ Filter by Agency", ["All"] + agencies)

# === Filtered Datasets ===
avail_data = available_df[available_df["Location Name"] == selected_state]
decision_data = decision_df[decision_df["City"] == selected_state]
layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]
fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]

if selected_agency != "All":
    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]
    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]

# === Page Header ===
st.markdown(f"""
<div style='text-align: center; background-color: #0e2a47; padding: 25px; border-radius: 12px;'>
    <h1 style='color: white; margin-bottom: 0;'>📊 Federal Layoff Intelligence Dashboard</h1>
    <p style='color: #ccc;'>Insights & Trends for <strong>{selected_state}</strong></p>
</div>
""", unsafe_allow_html=True)

# === KPIs ===
est_layoffs = decision_data["Estimated Layoffs"].sum()
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].head(1).values[0]

st.markdown("### 📌 Key Insights")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="👥 Estimated Layoffs", value=f"{est_layoffs:,.0f}")
with col2:
    st.metric(label="🎯 Most Affected Skill", value=top_skill)

st.markdown("---")

# === Tabs Section ===
tab1, tab2, tab3 = st.tabs(["🏢 Workforce Overview", "📉 Layoff Intelligence", "📰 Layoff News"])

# === Tab 1: Federal Staff Overview ===
with tab1:
    st.subheader("👷 Federal Staff Distribution by Occupation")
    if not fed_data.empty:
        chart_data = fed_data.groupby("Occupation Title")["Employee Count"].sum().reset_index()
        fig = px.bar(chart_data.sort_values("Employee Count", ascending=False).head(10),
                     x="Employee Count", y="Occupation Title", orientation="h",
                     title="Top 10 Occupations by Employee Count",
                     labels={"Employee Count": "Employees", "Occupation Title": "Occupation"})
        fig.update_layout(yaxis=dict(tickfont=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("🔍 View Full Staffing Data"):
            st.dataframe(fed_data, use_container_width=True)
    else:
        st.info("No federal staffing data available for this state.")

# === Tab 2: Layoff Intelligence ===
with tab2:
    st.subheader("⚠️ Projected Layoffs by Skill Category")
    if not decision_data.empty:
        fig1 = px.bar(decision_data.sort_values("Estimated Layoffs", ascending=False).head(10),
                      x="Estimated Layoffs", y="Skill Category", color="Action", orientation="h",
                      title="Top Skill Categories by Estimated Layoffs")
        fig1.update_layout(yaxis=dict(tickfont=dict(size=12)))
        st.plotly_chart(fig1, use_container_width=True)
        with st.expander("📋 Full Decision Data Table"):
            st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff intelligence data available for this state.")

# === Tab 3: Layoff News ===
with tab3:
    st.subheader("🗞️ Latest Federal Layoff News")
    if not layoff_data.empty:
        st.dataframe(layoff_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True)
    else:
        st.info("No news articles found for this selection.")

# === Footer ===
st.markdown("""
<hr>
<div style='text-align: center; color: gray; font-size: 0.85em;'>
Built with ❤️ using Streamlit | Last Updated: 2025
</div>
""", unsafe_allow_html=True)
