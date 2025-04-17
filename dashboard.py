import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Federal Layoff Intelligence", layout="wide")

# === Load CSVs with fallback uploader ===
def load_data(filename, label=None):
    """
    Loads a CSV file from local directory or via uploader.
    """
    if os.path.isfile(filename):
        return pd.read_csv(filename)

    uploaded_file = st.file_uploader(f"Upload {label or filename}", type="csv", key=filename)
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    st.warning(f"⚠️ File `{filename}` not found. Please upload it above.")
    return None

# === Load All Datasets ===
df_talent = load_data("city_skill_Available_Talent_projection.csv", "Available Talent")
df_demand = load_data("city_skill_demand_alignment_live.csv", "Demand Alignment")
df_decision = load_data("city_skill_decision_table.csv", "Layoff Decision Table")
df_news = load_data("federal_layoff_news_with_categories.csv", "Layoff News")
df_fedscope = load_data("fedscope_enriched_summary.csv", "Fedscope Summary")

if None in [df_talent, df_demand, df_decision, df_news, df_fedscope]:
    st.stop()

# === Sidebar Filters ===
st.sidebar.header("📌 Filters")
cities = sorted(df_decision["city"].dropna().unique())
selected_city = st.sidebar.selectbox("Select a U.S. City/State", ["All"] + cities)
agencies = sorted(df_fedscope["Agency Name"].dropna().unique())
selected_agency = st.sidebar.selectbox("Filter by Federal Agency", ["All"] + agencies)

# === Filtered Data ===
decision_data = df_decision.copy()
fedscope_data = df_fedscope.copy()
news_data = df_news.copy()

if selected_city != "All":
    decision_data = decision_data[decision_data["city"] == selected_city]
    fedscope_data = fedscope_data[fedscope_data["Location Name"].str.contains(selected_city, case=False, na=False)]
    news_data = news_data[news_data["Locations Impacted"].str.contains(selected_city, case=False, na=False)]

if selected_agency != "All":
    fedscope_data = fedscope_data[fedscope_data["Agency Name"] == selected_agency]
    news_data = news_data[news_data["Agency"] == selected_agency]

# === KPIs ===
st.markdown("<h1 style='text-align: center;'>📊 Federal Layoff Intelligence</h1>", unsafe_allow_html=True)
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_feds = fedscope_data["Employee Count"].sum()
layoff_pct = (est_layoffs / total_feds) * 100 if total_feds else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

col1, col2, col3 = st.columns(3)
col1.metric("👥 Estimated Layoffs", f"{est_layoffs:,.0f}")
col2.metric("🏆 Most Affected Skill", top_skill)
col3.metric("📉 Layoff Impact", f"{layoff_pct:.2f}% of Federal Workforce")

# === Tabs ===
tab1, tab2, tab3 = st.tabs(["🏢 Federal Workforce", "📉 Layoff Impact", "📰 Layoff News"])

# --- Tab 1: Federal Workforce ---
with tab1:
    st.subheader("Top Federal Occupations & Agencies")
    if not fedscope_data.empty:
        occ_chart = fedscope_data.groupby("Occupation Title")["Employee Count"].sum().sort_values(ascending=False).head(10).reset_index()
        fig_occ = px.bar(occ_chart, x="Occupation Title", y="Employee Count", title="Top 10 Occupations")
        st.plotly_chart(fig_occ, use_container_width=True)

        agency_chart = fedscope_data.groupby("Agency Name")["Employee Count"].sum().sort_values(ascending=False).head(10).reset_index()
        fig_agency = px.bar(agency_chart, x="Agency Name", y="Employee Count", title="Top 10 Agencies")
        st.plotly_chart(fig_agency, use_container_width=True)

        st.dataframe(fedscope_data, use_container_width=True)
    else:
        st.info("No federal workforce data available for selected filters.")

# --- Tab 2: Layoff Impact ---
with tab2:
    st.subheader("Layoffs by Skill & City")
    if not decision_data.empty:
        skill_chart = decision_data.sort_values("Estimated Layoffs", ascending=False).head(10)
        fig_skill = px.bar(skill_chart, x="Skill Category", y="Estimated Layoffs", color="Action", title="Top Skills Affected")
        st.plotly_chart(fig_skill, use_container_width=True)

        bubble_data = decision_data.groupby(["city", "Skill Category"])["Estimated Layoffs"].sum().reset_index()
        fig_bubble = px.scatter(bubble_data, x="city", y="Skill Category", size="Estimated Layoffs", title="Layoff Impact by City & Skill", size_max=60)
        st.plotly_chart(fig_bubble, use_container_width=True)

        st.dataframe(decision_data, use_container_width=True)
    else:
        st.info("No layoff data available for selected filters.")

# --- Tab 3: Layoff News ---
with tab3:
    st.subheader("Recent Federal Layoff News")
    if not news_data.empty:
        news_data['Date'] = pd.to_datetime(news_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        st.dataframe(news_data[[
            "Date", "Agency", "Occupations Affected", "Locations Impacted",
            "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
        ]], use_container_width=True, height=500)
    else:
        st.info("No news articles found for selected filters.")
