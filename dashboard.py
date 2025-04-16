import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Federal Workforce & Skill Dashboard", layout="wide")

# === HEADER ===
st.markdown("""
    <h1 style='text-align: center; color: white; background-color: #003366; padding: 25px; border-radius: 8px'>
    🏛️ Federal Workforce and Skill Availability Dashboard
    </h1>
""", unsafe_allow_html=True)

# === FILE UPLOAD SECTION ===
with st.expander("Upload Required CSV Files", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        available_file = st.file_uploader(" Available Talent Projection CSV", type="csv", key="available")
        decision_file = st.file_uploader(" Decision Table CSV", type="csv", key="decision")
    with col2:
        alignment_file = st.file_uploader(" Demand Alignment CSV", type="csv", key="alignment")
        fedscope_file = st.file_uploader(" Fedscope Summary CSV", type="csv", key="fedscope")
    with col3:
        layoffs_file = st.file_uploader(" Layoff News CSV", type="csv", key="layoffs")

# === IF ALL FILES ARE LOADED ===
if all([available_file, alignment_file, decision_file, layoffs_file, fedscope_file]):
    available_df = pd.read_csv(available_file)
    alignment_df = pd.read_csv(alignment_file)
    decision_df = pd.read_csv(decision_file)
    layoffs_df = pd.read_csv(layoffs_file)
    fedscope_df = pd.read_csv(fedscope_file)

    # === SIDEBAR FILTERS ===
    st.sidebar.header("🧭 Filters")
    view_mode = st.sidebar.radio("View Mode", ["National", "City"])

    selected_city = None
    if view_mode == "City":
        cities = sorted(decision_df["City"].dropna().unique())
        selected_city = st.sidebar.selectbox("Select a City", cities)

    agencies = sorted(fedscope_df["Agency Name"].dropna().unique())
    selected_agency = st.sidebar.selectbox("Filter by Agency (optional)", ["All"] + agencies)

    # === CITY/NATIONAL FILTERING HELPERS ===
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

    # === Apply AGENCY FILTER ===
    if selected_agency != "All":
        layoff_data = layoff_data[layoff_data["Agency"] == selected_agency]
        fed_data = fed_data[fed_data["Agency Name"] == selected_agency]

    # === KPI METRICS ===
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

    # === TAB 1: Available Talent ===
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

    # === TAB 2: Demand vs Supply ===
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

    # === TAB 3: Layoff News ===
    with tab3:
        st.subheader(f"📰 Layoff Events — {label_title}")
        if not layoff_data.empty:
            st.dataframe(layoff_data[[
                "Date", "Agency", "Occupations Affected", "Locations Impacted",
                "Key Skills Potentially Affected", "Layoff Risk Level", "Article Title", "Link"
            ]], use_container_width=True)
        else:
            st.info("No layoff news available.")

    # === TAB 4: Fedscope Impact ===
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

    # === TAB 5: Decision Intelligence ===
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

else:
    st.info("Please upload all five required CSV files to begin.")
