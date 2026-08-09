
import streamlit as st
import pandas as pd
import plotly.express as px
from cassandra.cluster import Cluster

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# CASSANDRA CONNECTION
# ============================================================

@st.cache_resource
def get_cassandra_session():
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect("sales")
    return session


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    session = get_cassandra_session()

    rows = session.execute(
        "SELECT * FROM sales_by_order"
    )

    data = rows.all()

    df = pd.DataFrame(data)

    return df


# ============================================================
# LOAD DATASET
# ============================================================

try:

    df = load_data()

except Exception as e:

    st.error("Could not connect to Cassandra.")
    st.code(str(e))
    st.stop()


# ============================================================
# DATA PREPARATION
# ============================================================

df["order_date"] = pd.to_datetime(
    df["order_date"].apply(
        lambda x: x.date() if hasattr(x, "date") else x
    )
)

df["ship_date"] = pd.to_datetime(
    df["ship_date"].apply(
        lambda x: x.date() if hasattr(x, "date") else x
    )
)


# ============================================================
# TITLE
# ============================================================

st.title("📊 Sales Intelligence Dashboard")

st.markdown(
    "Interactive business intelligence dashboard "
    "powered by Apache Cassandra and Streamlit."
)

st.divider()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Filters")

regions = sorted(df["region"].unique())

selected_regions = st.sidebar.multiselect(
    "Region",
    regions,
    default=regions
)


countries = sorted(df["country"].unique())

selected_countries = st.sidebar.multiselect(
    "Country",
    countries,
    default=countries
)


item_types = sorted(df["item_type"].unique())

selected_items = st.sidebar.multiselect(
    "Item Type",
    item_types,
    default=item_types
)


channels = sorted(df["sales_channel"].unique())

selected_channels = st.sidebar.multiselect(
    "Sales Channel",
    channels,
    default=channels
)


priorities = sorted(df["order_priority"].unique())

selected_priorities = st.sidebar.multiselect(
    "Order Priority",
    priorities,
    default=priorities
)


# ============================================================
# DATE FILTER
# ============================================================

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    df["region"].isin(selected_regions)
    & df["country"].isin(selected_countries)
    & df["item_type"].isin(selected_items)
    & df["sales_channel"].isin(selected_channels)
    & df["order_priority"].isin(selected_priorities)
]


# Apply date filter safely

if len(selected_dates) == 2:

    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1])

    filtered_df = filtered_df[
        (filtered_df["order_date"] >= start_date)
        & (filtered_df["order_date"] <= end_date)
    ]


# ============================================================
# CALCULATE KPIs
# ============================================================

total_revenue = filtered_df["total_revenue"].sum()

total_cost = filtered_df["total_cost"].sum()

total_profit = filtered_df["total_profit"].sum()

units_sold = filtered_df["units_sold"].sum()

orders = len(filtered_df)

profit_margin = (
    total_profit / total_revenue * 100
    if total_revenue != 0
    else 0
)

average_order_value = (
    total_revenue / orders
    if orders != 0
    else 0
)


# ============================================================
# KPI DISPLAY
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"${total_revenue:,.0f}"
)

col2.metric(
    "Total Profit",
    f"${total_profit:,.0f}"
)

col3.metric(
    "Profit Margin",
    f"{profit_margin:.2f}%"
)

col4.metric(
    "Average Order Value",
    f"${average_order_value:,.0f}"
)


col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Cost",
    f"${total_cost:,.0f}"
)

col2.metric(
    "Units Sold",
    f"{units_sold:,}"
)

col3.metric(
    "Orders",
    f"{orders:,}"
)

st.divider()


# ============================================================
# DASHBOARD TABS
# ============================================================

overview_tab, sales_tab, profit_tab, data_tab = st.tabs(
    [
        "📊 Overview",
        "📈 Sales Analysis",
        "💰 Profitability",
        "📋 Raw Data"
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

with overview_tab:

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # REVENUE BY REGION
    # --------------------------------------------------------

    region_sales = (
        filtered_df
        .groupby("region", as_index=False)["total_revenue"]
        .sum()
        .sort_values(
            "total_revenue",
            ascending=False
        )
    )

    fig_region = px.bar(
        region_sales,
        x="region",
        y="total_revenue",
        title="Revenue by Region"
    )

    fig_region.update_layout(
        xaxis_title="Region",
        yaxis_title="Revenue"
    )

    with col1:

        st.plotly_chart(
            fig_region,
            width="stretch"
        )


    # --------------------------------------------------------
    # PROFIT BY ITEM TYPE
    # --------------------------------------------------------

    item_profit = (
        filtered_df
        .groupby("item_type", as_index=False)["total_profit"]
        .sum()
        .sort_values(
            "total_profit",
            ascending=False
        )
    )

    fig_item = px.bar(
        item_profit,
        x="item_type",
        y="total_profit",
        title="Profit by Item Type"
    )

    fig_item.update_layout(
        xaxis_title="Item Type",
        yaxis_title="Profit"
    )

    with col2:

        st.plotly_chart(
            fig_item,
            width="stretch"
        )


    # --------------------------------------------------------
    # SALES CHANNEL PIE
    # --------------------------------------------------------

    channel_sales = (
        filtered_df
        .groupby("sales_channel", as_index=False)["total_revenue"]
        .sum()
    )

    fig_channel = px.pie(
        channel_sales,
        names="sales_channel",
        values="total_revenue",
        title="Revenue by Sales Channel",
        hole=0.35
    )

    st.plotly_chart(
        fig_channel,
        width="stretch"
    )


    # --------------------------------------------------------
    # REVENUE OVER TIME
    # --------------------------------------------------------

    monthly_sales = (
        filtered_df
        .set_index("order_date")
        .resample("ME")["total_revenue"]
        .sum()
        .reset_index()
    )

    fig_time = px.line(
        monthly_sales,
        x="order_date",
        y="total_revenue",
        title="Monthly Revenue",
        markers=True
    )

    fig_time.update_layout(
        xaxis_title="Date",
        yaxis_title="Revenue"
    )

    st.plotly_chart(
        fig_time,
        width="stretch"
    )


# ============================================================
# SALES ANALYSIS
# ============================================================

with sales_tab:

    st.subheader("Sales Performance")


    # --------------------------------------------------------
    # TOP COUNTRIES
    # --------------------------------------------------------

    country_sales = (
        filtered_df
        .groupby("country", as_index=False)["total_revenue"]
        .sum()
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .head(10)
    )

    fig_countries = px.bar(
        country_sales,
        x="total_revenue",
        y="country",
        orientation="h",
        title="Top 10 Countries by Revenue"
    )

    fig_countries.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(
        fig_countries,
        width="stretch"
    )


    # --------------------------------------------------------
    # UNITS SOLD BY ITEM
    # --------------------------------------------------------

    item_units = (
        filtered_df
        .groupby("item_type", as_index=False)["units_sold"]
        .sum()
        .sort_values(
            "units_sold",
            ascending=False
        )
    )

    fig_units = px.bar(
        item_units,
        x="item_type",
        y="units_sold",
        title="Units Sold by Item Type"
    )

    st.plotly_chart(
        fig_units,
        width="stretch"
    )


    col1, col2 = st.columns(2)


    # --------------------------------------------------------
    # ORDER PRIORITY
    # --------------------------------------------------------

    priority_counts = (
        filtered_df["order_priority"]
        .value_counts()
        .reset_index()
    )

    priority_counts.columns = [
        "order_priority",
        "orders"
    ]

    fig_priority = px.pie(
        priority_counts,
        names="order_priority",
        values="orders",
        title="Orders by Priority"
    )

    with col1:

        st.plotly_chart(
            fig_priority,
            width="stretch"
        )


    # --------------------------------------------------------
    # SALES CHANNEL ORDERS
    # --------------------------------------------------------

    channel_orders = (
        filtered_df["sales_channel"]
        .value_counts()
        .reset_index()
    )

    channel_orders.columns = [
        "sales_channel",
        "orders"
    ]

    fig_orders_channel = px.pie(
        channel_orders,
        names="sales_channel",
        values="orders",
        title="Orders by Sales Channel"
    )

    with col2:

        st.plotly_chart(
            fig_orders_channel,
            width="stretch"
        )


    # --------------------------------------------------------
    # REVENUE VS PROFIT
    # --------------------------------------------------------

    country_performance = (
        filtered_df
        .groupby("country", as_index=False)
        .agg(
            revenue=("total_revenue", "sum"),
            profit=("total_profit", "sum"),
            units=("units_sold", "sum")
        )
    )

    fig_scatter = px.scatter(
        country_performance,
        x="revenue",
        y="profit",
        size="units",
        hover_name="country",
        title="Revenue vs Profit by Country"
    )

    st.plotly_chart(
        fig_scatter,
        width="stretch"
    )


# ============================================================
# PROFITABILITY
# ============================================================

with profit_tab:

    st.subheader("Profitability Analysis")


    # --------------------------------------------------------
    # PROFIT BY REGION
    # --------------------------------------------------------

    region_profit = (
        filtered_df
        .groupby("region", as_index=False)["total_profit"]
        .sum()
        .sort_values(
            "total_profit",
            ascending=False
        )
    )

    fig_region_profit = px.bar(
        region_profit,
        x="region",
        y="total_profit",
        title="Profit by Region"
    )

    st.plotly_chart(
        fig_region_profit,
        width="stretch"
    )


    # --------------------------------------------------------
    # MONTHLY PROFIT
    # --------------------------------------------------------

    monthly_profit = (
        filtered_df
        .set_index("order_date")
        .resample("ME")["total_profit"]
        .sum()
        .reset_index()
    )

    fig_profit_time = px.line(
        monthly_profit,
        x="order_date",
        y="total_profit",
        title="Monthly Profit",
        markers=True
    )

    st.plotly_chart(
        fig_profit_time,
        width="stretch"
    )


    # --------------------------------------------------------
    # TOP PROFITABLE COUNTRIES
    # --------------------------------------------------------

    top_profit = (
        filtered_df
        .groupby("country", as_index=False)
        .agg(
            Revenue=("total_revenue", "sum"),
            Cost=("total_cost", "sum"),
            Profit=("total_profit", "sum"),
            Units=("units_sold", "sum")
        )
        .sort_values(
            "Profit",
            ascending=False
        )
        .head(10)
    )

    st.subheader("Top 10 Most Profitable Countries")

    st.dataframe(
        top_profit,
        width="stretch",
        hide_index=True
    )


    # --------------------------------------------------------
    # PROFIT MARGIN BY ITEM
    # --------------------------------------------------------

    item_margin = (
        filtered_df
        .groupby("item_type", as_index=False)
        .agg(
            Revenue=("total_revenue", "sum"),
            Profit=("total_profit", "sum")
        )
    )

    item_margin["Profit Margin"] = (
        item_margin["Profit"]
        / item_margin["Revenue"]
        * 100
    )

    item_margin = item_margin.sort_values(
        "Profit Margin",
        ascending=False
    )

    fig_margin = px.bar(
        item_margin,
        x="item_type",
        y="Profit Margin",
        title="Profit Margin by Item Type"
    )

    fig_margin.update_layout(
        yaxis_title="Profit Margin (%)"
    )

    st.plotly_chart(
        fig_margin,
        width="stretch"
    )


# ============================================================
# RAW DATA
# ============================================================

with data_tab:

    st.subheader("Sales Data")

    st.write(
        f"Displaying {len(filtered_df):,} records."
    )

    st.dataframe(
        filtered_df,
        width="stretch",
        hide_index=True
    )


    # --------------------------------------------------------
    # DOWNLOAD DATA
    # --------------------------------------------------------

    csv = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Filtered Data",
        data=csv,
        file_name="filtered_sales_data.csv",
        mime="text/csv",
        width="stretch"
    )