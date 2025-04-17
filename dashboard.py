import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from PIL import Image  # For adding a logo

st.set_page_config(page_title="Federal Layoff Intelligence", layout="wide")

# === Paths ===
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

# Ensure the data directory exists
if not os.path.exists(DATA_PATH):
    st.error(f"Data directory not found: {DATA_PATH}")
    st.stop()

# === Load Data ===
# Use try-except blocks to handle potential file loading errors.
try:
    available_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_Available_Talent_projection.csv"))
except FileNotFoundError:
    st.error(f"File not found: city_skill_Available_Talent_projection.csv")
    st.stop()

try:
    alignment_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_demand_alignment_live.csv"))
except FileNotFoundError:
    st.error(f"File not found: city_skill_demand_alignment_live.csv")
    st.stop()

try:
    decision_df = pd.read_csv(os.path.join(DATA_PATH, "city_skill_decision_table.csv"))
except FileNotFoundError:
    st.error(f"File not found: city_skill_decision_table.csv")
    st.stop()

try:
    layoffs_df = pd.read_csv(os.path.join(DATA_PATH, "federal_layoff_news_with_categories.csv"))
except FileNotFoundError:
    st.error(f"File not found: federal_layoff_news_with_categories.csv")
    st.stop()

try:
    fedscope_df = pd.read_csv(os.path.join(DATA_PATH, "fedscope_enriched_summary.csv"))
except FileNotFoundError:
    st.error(f"File not found: fedscope_enriched_summary.csv")
    st.stop()

# === Sidebar ===
st.sidebar.header("🧭 Filters")
states = sorted(decision_df["City"].dropna().unique())
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
# Add a logo (replace 'logo.png' with your actual logo file)
# logo = Image.open(os.path.join(BASE_DIR, 'logo.png'))  # Removed for now, as the file path may cause errors.
# st.image(logo, width=100)  # Adjust width as needed

st.markdown(f"""
<h1 style='text-align: center; background-color: #002b5c; color: white; padding: 20px; border-radius: 8px;'>
📊 Federal Layoff Intelligence – {selected_state}
</h1>
""", unsafe_allow_html=True)

# === KPI Metrics ===
col1, col2, col3 = st.columns(3)  # Added a third column for % Change
est_layoffs = decision_data["Estimated Layoffs"].sum()
total_federal_employees = fedscope_df[fedscope_df["Location Name"] == selected_state]["Employee Count"].sum()
layoff_percentage = (est_layoffs / total_federal_employees) * 100 if total_federal_employees else 0
top_skill = decision_data.sort_values("Estimated Layoffs", ascending=False)["Skill Category"].iloc[0] if not decision_data.empty else "N/A"

col1.metric("👥 Estimated Layoffs", f"{est_layoffs:,.0f}")
col2.metric("🏆 Most Affected Skill", top_skill)
col3.metric("📉 Layoff Impact", f"{layoff_percentage:.2f}% of Federal Workforce")

# === TABS ===
tab1, tab2, tab3 = st.tabs([
    "🏢 Federal Workforce",
    "📉 Layoff Impact",
    "📰 Layoff News"
])

# === Tab 1: Federal Workforce Overview ===
with tab1:
    st.subheader(f"Federal Agency Workforce Analysis – {selected_state}")

    if not fed_data.empty:
        # 1. Occupational Distribution
        chart_data_occupation = fed_data.groupby("Occupation Title")["Employee Count"].sum().reset_index()
        if not chart_data_occupation.empty:
            # Use a more visually appealing chart with interactivity
            fig_occupation = px.bar(
                chart_data_occupation.sort_values("Employee Count", ascending=False).head(10),
                x="Occupation Title",
                y="Employee Count",
                title="Top 10 Occupations",
                color_discrete_sequence=px.colors.sequential.Plasma,  # Use a color sequence
                hover_data=["Occupation Title", "Employee Count"],  # Add hover data for interactivity
            )
            fig_occupation.update_layout(
                xaxis_title="Occupation Title",
                yaxis_title="Number of Employees",
                plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_occupation, use_container_width=True)
        else:
            st.info("No occupation data available for the selected state and agency.")

        # 2. Agency Distribution
        chart_data_agency = fed_data.groupby("Agency Name")["Employee Count"].sum().reset_index()
        if not chart_data_agency.empty:
            fig_agency = px.bar(
                chart_data_agency.sort_values("Employee Count", ascending=False).head(10),
                x="Agency Name",
                y="Employee Count",
                title="Top 10 Agencies",
                color_discrete_sequence=px.colors.sequential.Viridis,
                hover_data=["Agency Name", "Employee Count"],
            )
            fig_agency.update_layout(
                xaxis_title="Agency Name",
                yaxis_title="Number of Employees",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_agency, use_container_width=True)
        else:
            st.info("No agency data available for the selected state and agency.")

        # 3. Data Table with Search and Pagination
        st.subheader("Federal Workforce Data")
        st.dataframe(
            fed_data,
            use_container_width=True,
            # Add these for better UI in the dataframe
            column_config={
                "Employee Count": st.column_config.NumberColumn(
                    format=","
                ),
            },
            height=300,
        )
    else:
        st.info("No federal staffing data available for this state.")


# === Tab 2: Layoff Impact Analysis ===
with tab2:
    st.subheader("Deep Dive into Layoff Impact")
    if not decision_data.empty:
        # 1. Layoffs by Skill and Action
        fig1 = px.bar(
            decision_data.sort_values("Estimated Layoffs", ascending=False).head(10),
            x="Skill Category",
            y="Estimated Layoffs",
            color="Action",
            title="Top Skill Categories Affected by Layoffs",
            color_discrete_sequence=px.colors.qualitative.Set1,
            hover_data=["Skill Category", "Estimated Layoffs", "Action"],
        )
        fig1.update_layout(
            xaxis_title="Skill Category",
            yaxis_title="Estimated Layoffs",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 2. Layoff Impact by City and Skill
        impact_df = decision_data.groupby(['City', 'Skill Category'])['Estimated Layoffs'].sum().reset_index()
        fig2 = px.scatter(
            impact_df,
            x='City',
            y='Skill Category',
            size='Estimated Layoffs',
            title='Geographic and Skill-Based Layoff Impact',
            hover_data=['City', 'Skill Category', 'Estimated Layoffs'],
            size_max=60,
            color_discrete_sequence=px.colors.qualitative.Dark2
        )
        fig2.update_layout(
            xaxis_title="City",
            yaxis_title="Skill Category",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

        # 3. Display Decision Data
        st.subheader("Layoff Decision Data")
        st.dataframe(decision_data, use_container_width=True, height=300)
    else:
        st.info("No layoff intelligence available.")

# === Tab 3: Layoff News ===
with tab3:
    st.subheader("Federal Layoff News Articles")
    if not layoff_data.empty:
        # Format the date for better readability
        layoff_data['Date'] = pd.to_datetime(layoff_data['Date']).dt.strftime('%Y-%m-%d')
        st.dataframe(
            layoff_data[[
                "Date", "Agency", "Occupations Affected", "Locations Impacted",
                "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
            ]],
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No layoff-related news found for this state.")
