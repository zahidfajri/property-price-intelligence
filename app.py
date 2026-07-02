import os

import plotly.express as px
import pydeck as pdk
import streamlit as st

from processor import (
    load_data,
    calculate_summary
)

from utils.excel_export import (
    create_excel_file
)


# =================================
# HELPER FUNCTIONS
# =================================
def normalize_input(user_input):
    """
    Convert area name or Speedhome URL
    into our CSV filename format.
    """

    user_input = user_input.strip()

    # Handle full Speedhome URL
    if "speedhome.com/rent/" in user_input:

        area_slug = user_input.split("/")[-1]

    else:

        area_slug = (
            user_input
            .lower()
            .replace(" ", "-")
        )

    return area_slug.replace("-", "_")


def get_available_areas():
    """
    Return all available CSV files.
    """

    files = os.listdir("data")

    return [
        file.replace(".csv", "")
        for file in files
        if file.endswith(".csv")
    ]


# =================================
# STREAMLIT CONFIG
# =================================
st.set_page_config(
    page_title="Property Price Intelligence Dashboard",
    layout="wide"
)


# =================================
# HEADER
# =================================
st.title("🏠 Property Price Intelligence Dashboard")

st.markdown("""
Analyze rental prices using pre-scraped Speedhome data.

Supported input:

- Area name (e.g. Mont Kiara)
- Available Areas: Bangsar, Cyberjaya, KLCC, Kuala Lumpur, Mont Kiara, Petaling Jaya

The application uses locally generated datasets to ensure reliable public deployment.
""")


# =================================
# INPUT SECTION
# =================================
user_input = st.text_input(
    "Enter Area Name or Speedhome URL",
    placeholder=(
        "Example: Mont Kiara "
        "or https://speedhome.com/rent/mont-kiara"
    )
)

load_button = st.button(
    "Load Data"
)


# =================================
# MAIN LOGIC
# =================================
if load_button:

    if not user_input:

        st.warning(
            "Please enter an area name or URL."
        )

        st.stop()

    area_slug = normalize_input(
        user_input
    )

    available_areas = get_available_areas()

    if area_slug not in available_areas:

        st.error(
            f"""
No data found for:

{user_input}

Please generate the CSV locally first
using scraper.py.
"""
        )

        st.stop()

    csv_path = f"data/{area_slug}.csv"

    # =================================
    # LOAD DATA
    # =================================
    df = load_data(
        csv_path
    )

    summary_df = calculate_summary(
        df
    )

    # =================================
    # TOP METRICS
    # =================================
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Units",
            len(df)
        )

    with col2:
        st.metric(
            "Average Monthly Rent",
            f"RM {round(df['monthly_price'].mean()):,}"
        )

    with col3:
        st.metric(
            "Median Monthly Rent",
            f"RM {round(df['monthly_price'].median()):,}"
        )

    # =================================
    # PRICE DISTRIBUTION
    # =================================
    st.divider()

    st.subheader(
        "📈 Monthly Rent Distribution"
    )

    fig = px.histogram(
        df,
        x="monthly_price",
        nbins=15,
        labels={
            "monthly_price": "Monthly Rent (RM)"
        },
        title="Distribution of Monthly Rental Prices"
    )

    fig.update_layout(
        xaxis_title="Monthly Rent (RM)",
        yaxis_title="Number of Properties"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =================================
    # PROPERTY HIGHLIGHTS
    # =================================
    st.divider()

    st.subheader(
        "🏆 Property Highlights"
    )

    cheapest = df.loc[
        df["monthly_price"].idxmin()
    ]

    most_expensive = df.loc[
        df["monthly_price"].idxmax()
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.success(
            "💰 Cheapest Property"
        )

        st.write(
            f"**{cheapest['name']}**"
        )

        st.write(
            f"RM {cheapest['monthly_price']:,}/month"
        )

        st.link_button(
            "View Listing",
            cheapest["listing_url"]
        )

    with col2:

        st.warning(
            "💎 Premium Property"
        )

        st.write(
            f"**{most_expensive['name']}**"
        )

        st.write(
            f"RM {most_expensive['monthly_price']:,}/month"
        )

        st.link_button(
            "View Listing",
            most_expensive["listing_url"]
        )

    # =================================
    # PROPERTY MAP
    # =================================
    if (
        "latitude" in df.columns
        and "longitude" in df.columns
    ):

        map_df = df.dropna(
            subset=["latitude", "longitude"]
        )

        if not map_df.empty:

            st.divider()

            st.subheader(
                "🗺️ Property Locations"
            )

            st.caption(
                "Hover over a marker to see property details."
            )

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[longitude, latitude]',
                get_radius=80,
                get_fill_color='[255, 0, 0, 180]',
                pickable=True
            )

            view_state = pdk.ViewState(
                latitude=map_df["latitude"].mean(),
                longitude=map_df["longitude"].mean(),
                zoom=12
            )

            tooltip = {
                "html": """
                <b>{name}</b><br/>
                RM {monthly_price}/month<br/>
                {bedroom} Bedrooms<br/>
                {sqft} sqft
                """,
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white"
                }
            }

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=tooltip
                )
            )

        # =================================
        # PRICE SUMMARY
        # =================================
        st.divider()

        st.subheader(
            "📊 Price Summary"
        )

        st.dataframe(
            summary_df,
            use_container_width=True
        )

        # =================================
        # DAILY RENTAL DISCLAIMER
        # =================================
        st.info("""
    ℹ️ Daily rental information is not available on Speedhome.

    This application displays monthly and yearly rental estimates instead.
    """)

        # =================================
        # UNIT LISTINGS
        # =================================
        st.divider()

        st.subheader(
            "🏢 Unit Listings"
        )

        display_df = df.rename(columns={
            "name": "Property Name",
            "bedroom": "Bedrooms",
            "bathroom": "Bathrooms",
            "carpark": "Carparks",
            "monthly_price": "Monthly Price (RM)",
            "yearly_price": "Yearly Price (RM)",
            "sqft": "Size (sqft)",
            "furnish_type": "Furnishing",
            "property_type": "Property Type",
            "listing_url": "Listing URL"
        })

        st.dataframe(
            display_df,
            use_container_width=True
        )

        # =================================
        # DOWNLOAD SECTION
        # =================================
        st.divider()

        st.subheader(
            "⬇️ Download Report"
        )

        excel_file = create_excel_file(
            summary_df,
            df
        )

        st.download_button(
            label="Download Excel Report",
            data=excel_file,
            file_name=f"{area_slug}_analysis.xlsx",
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )