
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Nassau Candy Route Analytics",
    page_icon="🚚",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = BASE_DIR / "Nassau Candy Distributor.csv"


# --------------------------------------------------
# 2. PRODUCT-TO-FACTORY MAPPING
# --------------------------------------------------

PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory",
}

# State name -> US postal abbreviation, for mapping
STATE_ABBREVIATIONS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ",
    "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL",
    "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}


# --------------------------------------------------
# 3. LOAD AND PREPARE DATA
# --------------------------------------------------

@st.cache_data
def load_data(path, modified_time):
    df = pd.read_csv(path)

    required_columns = [
        "Order ID", "Order Date", "Ship Date", "Ship Mode",
        "State/Province", "Region", "Product Name",
        "Sales", "Units", "Gross Profit", "Cost",
        "Customer ID", "City",
    ]

    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    # Parse dates without changing the source CSV.
    df["Order Date"] = pd.to_datetime(
        df["Order Date"], errors="coerce"
    )
    df["Ship Date"] = pd.to_datetime(
        df["Ship Date"], errors="coerce"
    )

    # Convert measures to numeric values.
    for col in ["Sales", "Units", "Gross Profit", "Cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove accidental spaces around product names.
    df["Product Name"] = df["Product Name"].astype("string").str.strip()

    # Assign the factory from the provided mapping.
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY)

    # Provisional lead time. It is not treated as reliable
    # until the source date issue is resolved.
    df["Lead Time Days"] = (
        df["Ship Date"] - df["Order Date"]
    ).dt.days

    # One row is a product record, not necessarily a unique order.
    df["State/Province"] = (
        df["State/Province"].astype("string").str.strip()
    )
    df["State Code"] = df["State/Province"].map(STATE_ABBREVIATIONS)

    return df


st.title("🚚 Nassau Candy Shipping Route Efficiency")
st.caption("Factory-to-customer analysis | Interactive business dashboard")

if not CSV_PATH.exists():
    st.error(
        f"Dataset not found: {CSV_PATH}\n\n"
        "Place 'Nassau Candy Distributor.csv' next to app.py."
    )
    st.stop()

try:
    data = load_data(str(CSV_PATH), CSV_PATH.stat().st_mtime)
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

# --------------------------------------------------
# 4. DATE QUALITY WARNING
# --------------------------------------------------

valid_dates = data.dropna(subset=["Order Date", "Ship Date"])
if not valid_dates.empty:
    earliest_order = valid_dates["Order Date"].min()
    latest_order = valid_dates["Order Date"].max()
    earliest_ship = valid_dates["Ship Date"].min()
    latest_ship = valid_dates["Ship Date"].max()

    st.warning(
        "Date validation required: the source data currently reports "
        f"Order Dates from {earliest_order:%Y-%m-%d} to "
        f"{latest_order:%Y-%m-%d}, and Ship Dates from "
        f"{earliest_ship:%Y-%m-%d} to {latest_ship:%Y-%m-%d}. "
        "Lead-time figures are provisional and should not be used to "
        "claim which route or shipping method is fastest."
    )


# --------------------------------------------------
# 5. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

factories = sorted(data["Factory"].dropna().unique().tolist())
selected_factories = st.sidebar.multiselect(
    "Factory",
    options=factories,
    default=factories,
)

modes = sorted(data["Ship Mode"].dropna().astype(str).unique().tolist())
selected_modes = st.sidebar.multiselect(
    "Shipping method",
    options=modes,
    default=modes,
)

regions = sorted(data["Region"].dropna().astype(str).unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Region",
    options=regions,
    default=regions,
)

states = sorted(
    data["State/Province"].dropna().astype(str).unique().tolist()
)
selected_states = st.sidebar.multiselect(
    "Customer state",
    options=states,
    default=states,
)

products = sorted(data["Product Name"].dropna().astype(str).unique().tolist())
selected_products = st.sidebar.multiselect(
    "Product",
    options=products,
    default=products,
)

filtered = data[
    data["Factory"].isin(selected_factories)
    & data["Ship Mode"].astype(str).isin(selected_modes)
    & data["Region"].astype(str).isin(selected_regions)
    & data["State/Province"].astype(str).isin(selected_states)
    & data["Product Name"].astype(str).isin(selected_products)
].copy()

if filtered.empty:
    st.info("No records match these filters. Change your selections.")
    st.stop()


# --------------------------------------------------
# 6. KPI CARDS
# --------------------------------------------------

total_records = len(filtered)
total_orders = filtered["Order ID"].nunique()
total_customers = filtered["Customer ID"].nunique()
total_sales = filtered["Sales"].sum()
total_units = filtered["Units"].sum()
total_profit = filtered["Gross Profit"].sum()

k1, k2, k3 = st.columns(3)
k1.metric("Product records", f"{total_records:,}")
k2.metric("Unique orders", f"{total_orders:,}")
k3.metric("Unique customers", f"{total_customers:,}")

k4, k5, k6 = st.columns(3)
k4.metric("Total sales", f"${total_sales:,.2f}")
k5.metric("Units sold", f"{total_units:,.0f}")
k6.metric("Gross profit", f"${total_profit:,.2f}")


# --------------------------------------------------
# 7. TABS
# --------------------------------------------------

overview_tab, routes_tab, shipping_tab, map_tab, data_tab = st.tabs([
    "Overview",
    "Route Analysis",
    "Shipping Methods",
    "Customer Map",
    "Data Explorer",
])


# --------------------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------------------

with overview_tab:
    st.subheader("Business Overview")

    left, right = st.columns(2)

    with left:
        factory_counts = (
            filtered.groupby("Factory", as_index=False)
            .agg(Product_Records=("Order ID", "size"))
            .sort_values("Product_Records", ascending=False)
        )

        fig_factory = px.bar(
            factory_counts,
            x="Factory",
            y="Product_Records",
            title="Product Records by Factory",
            text="Product_Records",
        )
        fig_factory.update_layout(xaxis_title="", yaxis_title="Records")
        st.plotly_chart(fig_factory, use_container_width=True)

    with right:
        mode_counts = (
            filtered.groupby("Ship Mode", as_index=False)
            .agg(Product_Records=("Order ID", "size"))
            .sort_values("Product_Records", ascending=False)
        )

        fig_modes = px.pie(
            mode_counts,
            names="Ship Mode",
            values="Product_Records",
            title="Record Distribution by Shipping Method",
            hole=0.4,
        )
        st.plotly_chart(fig_modes, use_container_width=True)

    sales_region = (
        filtered.groupby("Region", as_index=False)
        .agg(Sales=("Sales", "sum"), Units=("Units", "sum"))
        .sort_values("Sales", ascending=False)
    )

    fig_region = px.bar(
        sales_region,
        x="Region",
        y="Sales",
        color="Region",
        title="Sales by Region",
        hover_data=["Units"],
    )
    st.plotly_chart(fig_region, use_container_width=True)

    st.caption(
        "Sales, units, and gross profit are aggregated from product records. "
        "Order counts use distinct Order IDs."
    )


# --------------------------------------------------
# TAB 2: ROUTE ANALYSIS
# --------------------------------------------------

with routes_tab:
    st.subheader("Factory-to-State Route Analysis")

    route_summary = (
        filtered.groupby(["Factory", "State/Province"], as_index=False)
        .agg(
            Product_Records=("Order ID", "size"),
            Unique_Orders=("Order ID", "nunique"),
            Sales=("Sales", "sum"),
            Units=("Units", "sum"),
            Gross_Profit=("Gross Profit", "sum"),
        )
    )

    sort_choice = st.selectbox(
        "Rank routes by",
        ["Unique orders", "Product records", "Sales", "Units", "Gross profit"],
    )

    sort_columns = {
        "Unique orders": "Unique_Orders",
        "Product records": "Product_Records",
        "Sales": "Sales",
        "Units": "Units",
        "Gross profit": "Gross_Profit",
    }

    ranked = route_summary.sort_values(
        sort_columns[sort_choice], ascending=False
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**Top 10 routes**")
        top10 = ranked.head(10)
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with right:
        st.markdown("**Bottom 10 routes**")
        bottom10 = ranked.tail(10).sort_values(
            sort_columns[sort_choice], ascending=True
        )
        st.dataframe(bottom10, use_container_width=True, hide_index=True)

    chart_data = ranked.head(15).copy()
    chart_data["Route"] = (
        chart_data["Factory"] + " → " + chart_data["State/Province"]
    )

    fig_routes = px.bar(
        chart_data.sort_values(sort_columns[sort_choice]),
        x=sort_columns[sort_choice],
        y="Route",
        orientation="h",
        title=f"Top Routes by {sort_choice}",
        hover_data=["Unique_Orders", "Product_Records", "Sales", "Units"],
    )
    st.plotly_chart(fig_routes, use_container_width=True)

    st.download_button(
        "Download route analysis CSV",
        data=route_summary.to_csv(index=False).encode("utf-8"),
        file_name="factory_state_route_analysis.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# TAB 3: SHIPPING METHODS
# --------------------------------------------------

with shipping_tab:
    st.subheader("Shipping Method Comparison")

    mode_summary = (
        filtered.groupby("Ship Mode", as_index=False)
        .agg(
            Product_Records=("Order ID", "size"),
            Unique_Orders=("Order ID", "nunique"),
            Sales=("Sales", "sum"),
            Units=("Units", "sum"),
            Gross_Profit=("Gross Profit", "sum"),
        )
    )

    st.dataframe(mode_summary, use_container_width=True, hide_index=True)

    left, right = st.columns(2)

    with left:
        fig_order_modes = px.bar(
            mode_summary.sort_values("Unique_Orders", ascending=False),
            x="Ship Mode",
            y="Unique_Orders",
            title="Unique Orders by Shipping Method",
            text="Unique_Orders",
        )
        st.plotly_chart(fig_order_modes, use_container_width=True)

    with right:
        fig_sales_modes = px.bar(
            mode_summary.sort_values("Sales", ascending=False),
            x="Ship Mode",
            y="Sales",
            title="Sales by Shipping Method",
            text_auto=".2s",
        )
        st.plotly_chart(fig_sales_modes, use_container_width=True)

    st.info(
        "Lead-time comparisons are intentionally excluded from the main "
        "performance rankings until the source dates are validated."
    )

    st.download_button(
        "Download shipping method summary",
        data=mode_summary.to_csv(index=False).encode("utf-8"),
        file_name="shipping_method_summary.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# TAB 4: CUSTOMER DESTINATION MAP
# --------------------------------------------------

with map_tab:
    st.subheader("Customer Destination Map")
    map_data = (
        filtered.dropna(subset=["State Code"])
        .groupby("State Code", as_index=False)
        .agg(
            Product_Records=("Order ID", "size"),
            Unique_Orders=("Order ID", "nunique"),
            Sales=("Sales", "sum"),
        )
    )

    if map_data.empty:
        st.info(
            "No recognizable US state names are available for the map. "
            "Check the State/Province values in the Data Explorer tab."
        )
    else:
        fig_map = px.choropleth(
            map_data,
            locations="State Code",
            locationmode="USA-states",
            color="Unique_Orders",
            scope="usa",
            hover_name="State Code",
            hover_data=["Product_Records", "Unique_Orders", "Sales"],
            title="Unique Orders by Customer State",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.caption(
            "This map shows customer destinations by state, not actual road "
            "routes or driving distances from the factories."
        )


# --------------------------------------------------
# TAB 5: DATA EXPLORER
# --------------------------------------------------

with data_tab:
    st.subheader("Filtered Dataset")

    st.write(f"Rows after filters: **{len(filtered):,}**")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download filtered dataset",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="nassau_candy_filtered_data.csv",
        mime="text/csv",
    )

    st.subheader("Data Quality Checks")

    quality = pd.DataFrame({
        "Check": [
            "Total records",
            "Missing Order Date",
            "Missing Ship Date",
            "Missing factory mapping",
            "Duplicate full rows",
            "Negative lead times",
        ],
        "Result": [
            len(filtered),
            int(filtered["Order Date"].isna().sum()),
            int(filtered["Ship Date"].isna().sum()),
            int(filtered["Factory"].isna().sum()),
            int(filtered.duplicated().sum()),
            int((filtered["Lead Time Days"] < 0).sum()),
        ],
    })

    st.dataframe(quality, use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered data quality report",
        data=quality.to_csv(index=False).encode("utf-8"),
        file_name="data_quality_report.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "Nassau Candy Shipping Route Efficiency Analysis | "
    "Built with Python, Pandas, Plotly, and Streamlit"
)
