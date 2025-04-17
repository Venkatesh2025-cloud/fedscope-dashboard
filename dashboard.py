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

st.sidebar.header("🧭 Filters")

states = sorted(decision_df["City"].dropna().unique())  # Still comes under 'City' column

selected_state = st.sidebar.selectbox("Select a State", states)



agencies = sorted(fedscope_df["Agency Name"].dropna().unique())

selected_agency = st.sidebar.selectbox("Filter by Agency (optional)", ["All"] + agencies)



# === Filtered Datasets ===

avail_data = available_df[available_df["Location Name"] == selected_state]

decision_data = decision_df[decision_df["City"] == selected_state]

layoff_data = layoffs_df[layoffs_df["Locations Impacted"].str.contains(selected_state, case=False, na=False)]

fed_data = fedscope_df[fedscope_df["Location Name"].str.contains(selected_state, case=False, na=False)]



if selected_agency != "All":

    fed_data = fed_data[fed_data["Agency Name"] == selected_agency]

    layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]



# === Header ===

st.markdown(f"""

<h1 style='text-align: center; background-color: #002b5c; color: white; padding: 20px; border-radius: 8px;'>

📊 Federal Layoff Intelligence – {selected_state}

</h1>

""", unsafe_allow_html=True)



# === KPI Metrics ===

col1, col2 = st.columns(2)

est_layoffs = decision_data["Estimated Layoffs"].sum()

top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].head(1).values[0]



col1.metric("👥 Estimated Layoffs", f"{est_layoffs:,.0f}")

col2.metric("🏆 Most Affected Skill", top_skill)



# === TABS ===

tab1, tab2, tab3 = st.tabs([

    "🏢 Federal Staff by Occupation",

    "📉 Federal Layoff Intelligence",

    "📰 Layoff News"

])



# === Tab 1: Federal Staff Overview ===

with tab1:

    st.subheader(f"Federal Agency Workforce – {selected_state}")

    if not fed_data.empty:

        chart_data = fed_data.groupby("Occupation Title")["Employee Count"].sum().reset_index()

        fig = px.bar(chart_data.sort_values("Employee Count", ascending=False).head(10),

                     x="Occupation Title", y="Employee Count",

                     title="Top 10 Occupations by Employee Count")

        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(fed_data, use_container_width=True)

    else:

        st.info("No federal staffing data available for this state.")



# === Tab 2: Layoff Intelligence ===

with tab2:

    st.subheader("Top Impacted Job Categories & Skills")

    if not decision_data.empty:

        fig1 = px.bar(decision_data.sort_values("Estimated Layoffs", ascending=False).head(10),

                      x="Skill Category", y="Estimated Layoffs", color="Action",

                      title="Top Skill Categories by Estimated Layoffs")

        st.plotly_chart(fig1, use_container_width=True)



        st.dataframe(decision_data, use_container_width=True)

    else:

        st.info("No layoff intelligence available.")



# === Tab 3: Layoff News ===

with tab3:

    st.subheader("Federal Layoff News Articles")

    if not layoff_data.empty:

        st.dataframe(layoff_data[[

            "Date", "Agency", "Occupations Affected", "Locations Impacted",

            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"

        ]], use_container_width=True)

    else:

        st.info("No layoff-related news found for this state.")
