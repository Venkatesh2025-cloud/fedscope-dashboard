import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Data loading and file handling
@st.cache_data
def load_data(filename):
    """
    Loads CSV data, handling potential file errors.

    Args:
        filename (str): Name of the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the data, or None on error.
    """
    try:
        # Construct the full path relative to the script's location.  This is more robust.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)

        # Check if the file exists
        if not os.path.exists(filepath):
            st.error(f"Error: File not found at {filepath}.  Please ensure the file is in the same directory as the script, or update the path.")
            return None  # Explicitly return None for the error case

        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        st.error(f"Error loading data from {filename}: {e}")
        return None  # Important: Return None on any exception

# --- Data Preparation ---
@st.cache_data
def prepare_fedscope_data(df):
    """
    Prepares the fedscope data for analysis.  Handles missing data.

    Args:
        df (pd.DataFrame): The raw fedscope data.

    Returns:
        pd.DataFrame: Processed DataFrame, or None on error.
    """
    if df is None:
        return None

    # Drop rows where 'WORKFORCE' or 'AGENCY' is missing
    df_filtered = df.dropna(subset=['WORKFORCE', 'AGENCY'])

    # Calculate 'TOTAL_EMP' by summing relevant columns, handling potential errors
    columns_to_sum = ['TOTAL_EMP_PERM_FT', 'TOTAL_EMP_PERM_PT', 'TOTAL_EMP_TEMP_FT', 'TOTAL_EMP_TEMP_PT']
    for col in columns_to_sum:
        if col not in df_filtered.columns:
            st.error(f"Column '{col}' not found in fedscope data.")
            return None

    df_filtered['TOTAL_EMP'] = df_filtered[columns_to_sum].sum(axis=1)

    # Group by 'WORKFORCE' and 'AGENCY' and calculate the sum of 'TOTAL_EMP'
    df_grouped = df_filtered.groupby(['WORKFORCE', 'AGENCY'])['TOTAL_EMP'].sum().reset_index()

    return df_grouped

@st.cache_data
def prepare_layoff_data(df_news, df_decision):
    """
    Prepares layoff data by merging and aggregating.  Handles missing data.

    Args:
        df_news (pd.DataFrame): Layoff news data.
        df_decision (pd.DataFrame): Layoff decision data.

    Returns:
        pd.DataFrame: Processed DataFrame, or None on error.
    """
    if df_news is None or df_decision is None:
        return None

    # Basic cleaning of df_decision
    df_decision_filtered = df_decision.dropna(subset=['city', 'Skill Category'])
    #Keep only needed columns
    df_decision_filtered = df_decision_filtered[['city', 'Skill Category', 'Number of Employees Impacted']]

    # Merge the dataframes on 'Skill Category'
    df_merged = pd.merge(df_news, df_decision_filtered, on='Skill Category', how='inner')

    # Group by 'city' and 'Skill Category' and calculate the sum of 'Number of Employees Impacted'
    df_grouped = df_merged.groupby(['city', 'Skill Category'])['Number of Employees Impacted'].sum().reset_index()

    return df_grouped

@st.cache_data
def calculate_kpis(df_fedscope, df_layoff):
    """
    Calculates key performance indicators (KPIs). Handles missing data.

    Args:
        df_fedscope (pd.DataFrame): Prepared fedscope data.
        df_layoff (pd.DataFrame): Prepared layoff data.

    Returns:
        dict: A dictionary containing the calculated KPIs, or None on error.
    """
    if df_fedscope is None or df_layoff is None:
        return None

    total_federal_employees = df_fedscope['TOTAL_EMP'].sum()
    if total_federal_employees == 0:
        return {"total_layoffs": 0, "most_impacted_skill": "N/A", "percentage_impacted": 0}

    total_layoffs = df_layoff['Number of Employees Impacted'].sum()
    most_impacted_skill = df_layoff.groupby('Skill Category')['Number of Employees Impacted'].sum().idxmax()
    percentage_impacted = (total_layoffs / total_federal_employees) * 100 if total_federal_employees else 0

    return {
        "total_layoffs": total_layoffs,
        "most_impacted_skill": most_impacted_skill,
        "percentage_impacted": percentage_impacted
    }

# --- Plotly Charting Functions ---
def create_workforce_chart(df, title):
    """
    Creates a Plotly bar chart for workforce distribution.

    Args:
        df (pd.DataFrame): Data for the chart.
        title (str): Title of the chart.

    Returns:
        plotly.graph_objects.Figure: The Plotly figure.
    """
    if df is None:
        return None
    fig = px.bar(
        df,
        x='WORKFORCE',
        y='TOTAL_EMP',
        color='AGENCY',
        title=title,
        hover_data=['WORKFORCE', 'AGENCY', 'TOTAL_EMP'],
        labels={'WORKFORCE': 'Workforce Category', 'AGENCY': 'Agency', 'TOTAL_EMP': 'Total Employees'}
    )
    fig.update_layout(
        xaxis_title="Workforce Category",
        yaxis_title="Total Employees",
        legend_title="Agency",
        # Make the chart interactive
        hovermode="x unified"
    )
    return fig

def create_layoff_impact_chart(df, title):
    """
    Creates a Plotly bubble chart for layoff impact.

    Args:
        df (pd.DataFrame): Data for the chart.
        title (str): Title of the chart.
    Returns:
        plotly.graph_objects.Figure: The Plotly figure.
    """
    if df is None:
        return None
    fig = px.scatter(
        df,
        x='city',
        y='Skill Category',
        size='Number of Employees Impacted',
        color='Skill Category',
        title=title,
        hover_data=['city', 'Skill Category', 'Number of Employees Impacted'],
        labels={'city': 'City', 'Skill Category': 'Skill Category', 'Number of Employees Impacted': 'Number of Employees Impacted'}
    )
    fig.update_layout(
        xaxis_title="City",
        yaxis_title="Skill Category",
        legend_title="Skill Category",
        # Make the chart interactive
        hovermode="x unified"
    )
    return fig

# --- Streamlit UI ---
def main():
    """
    Main function to run the Streamlit application.
    """
    # --- 1. Setup the Streamlit Page ---
    st.set_page_config(page_title="Federal Layoff Intelligence Dashboard", layout="wide")

    # --- 2. Load the Data ---
    # Load all datasets.  The load_data function handles errors, so we don't need to repeat the error checking here.
    df_city_skill_talent = load_data('city_skill_Available_Talent_projection.csv')
    df_city_skill_demand = load_data('city_skill_demand_alignment_live.csv')
    df_city_skill_decision = load_data('city_skill_decision_table.csv')
    df_federal_layoff_news = load_data('federal_layoff_news_with_categories.csv')
    df_fedscope_enriched = load_data('fedscope_enriched_summary.csv')

    # --- 3. Prepare Data and Calculate KPIs ---
    # Process the dataframes.  Check for None after each processing step.
    df_fedscope_prepared = prepare_fedscope_data(df_fedscope_enriched)
    df_layoff_prepared = prepare_layoff_data(df_federal_layoff_news, df_city_skill_decision)

    # Calculate KPIs
    kpis = calculate_kpis(df_fedscope_prepared, df_layoff_prepared) if df_fedscope_prepared is not None and df_layoff_prepared is not None else None

    # --- 4. Sidebar Filters ---
    st.sidebar.header("Filters")

    # Create a list of all available cities
    all_cities = []
    if df_city_skill_talent is not None:
        all_cities.extend(df_city_skill_talent['city'].unique())
    if df_city_skill_demand is not None:
        all_cities.extend(df_city_skill_demand['city'].unique())
    if df_city_skill_decision is not None:
        all_cities.extend(df_city_skill_decision['city'].unique())
    all_cities = list(set(all_cities))  # Remove duplicates

    # Add a default option
    all_cities.insert(0, 'All')
    selected_city = st.sidebar.selectbox("Select a U.S. City/State", all_cities)

    # Agency filter.
    all_agencies = ['All']
    if df_fedscope_prepared is not None:
        all_agencies.extend(df_fedscope_prepared['AGENCY'].unique())
    selected_agency = st.sidebar.selectbox("Filter by Federal Agency", all_agencies)

    # --- 5. Main Content with Tabs ---
    # Centered title using markdown
    st.markdown("<h1 style='text-align: center;'>Federal Layoff Intelligence</h1>", unsafe_allow_html=True)

    # Display KPIs at the top
    if kpis:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Layoffs", kpis["total_layoffs"])
        col2.metric("Most Impacted Skill", kpis["most_impacted_skill"])
        col3.metric("Percentage of Workforce Impacted", f"{kpis['percentage_impacted']:.2f}%")
    elif kpis is None:
        st.warning("Warning: Unable to calculate KPIs.  Please ensure data files are available and correctly formatted.")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Federal Workforce", "Layoff Impact", "Layoff News"])

    # --- Tab 1: Federal Workforce ---
    with tab1:
        if df_fedscope_prepared is not None:
            # Apply filters
            df_filtered = df_fedscope_prepared.copy() #start with a copy
            if selected_city != 'All':
                df_filtered = df_filtered[df_filtered['WORKFORCE'].str.contains(selected_city, case=False, na=False)]
            if selected_agency != 'All':
                df_filtered = df_filtered[df_filtered['AGENCY'] == selected_agency]
            # Create the chart.
            workforce_chart = create_workforce_chart(df_filtered, "Federal Workforce Distribution")
            if workforce_chart:
                st.plotly_chart(workforce_chart, use_container_width=True)

            # Display the filtered data as a table
            st.subheader("Federal Workforce Data")
            st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("Warning: Federal workforce data is not available.")

    # --- Tab 2: Layoff Impact ---
    with tab2:
        if df_layoff_prepared is not None:
             # Apply filters
            df_filtered_layoff = df_layoff_prepared.copy()
            if selected_city != 'All':
                df_filtered_layoff = df_filtered_layoff[df_filtered_layoff['city'] == selected_city]

            layoff_impact_chart = create_layoff_impact_chart(df_filtered_layoff, "Layoff Impact by City and Skill")
            if layoff_impact_chart:
                st.plotly_chart(layoff_impact_chart, use_container_width=True)
        else:
            st.warning("Warning: Layoff impact data is not available.")

    # --- Tab 3: Layoff News ---
    with tab3:
        if df_federal_layoff_news is not None:
            # Format the 'published_date' column to datetime objects
            df_federal_layoff_news['published_date'] = pd.to_datetime(df_federal_layoff_news['published_date'])

            # Apply filters
            df_news_filtered = df_federal_layoff_news.copy()  # Create a copy to avoid modifying the original DataFrame
            if selected_city != 'All':
                # Filter based on the 'city' column in df_city_skill_decision
                if df_city_skill_decision is not None:
                  affected_cities = df_city_skill_decision[df_city_skill_decision['city'] == selected_city]['city'].unique()
                  # Filter news articles if their summary contains the selected city.
                  df_news_filtered = df_news_filtered[df_news_filtered['summary'].str.contains('|'.join(affected_cities), case=False, na=False)]
                else:
                    df_news_filtered = df_news_filtered[df_news_filtered['summary'].str.contains(selected_city, case=False, na=False)]

            # Format the date for display
            df_news_filtered['published_date'] = df_news_filtered['published_date'].dt.strftime('%Y-%m-%d')
            # Create a link for the title
            df_news_filtered['title'] = df_news_filtered.apply(lambda row: f'<a href="{row["link"]}" target="_blank">{row["title"]}</a>', axis=1)

            # Display the news articles.  Use the formatted title with link, and the formatted date.
            st.subheader("Federal Layoff News")
            st.dataframe(df_news_filtered[['published_date', 'title', 'categories', 'summary']], use_container_width=True, height=500,
                         column_config={
                             "published_date": st.column_config.Column(
                                 "Published Date",
                                 format="YYYY-MM-DD",
                             ),
                             "title": st.column_config.Column("Title", unsafe_allow_html=True), # Allow HTML for the link
                             "categories": "Categories",
                             "summary": "Summary"
                         })
        else:
            st.warning("Warning: Layoff news data is not available.")

if __name__ == "__main__":
    main()
