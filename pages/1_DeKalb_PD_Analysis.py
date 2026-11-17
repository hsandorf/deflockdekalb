
import streamlit as st
import plotly.express as px

from data_utils import download_file, query_csv, sql_file_path


st.set_page_config(
    page_title="DeKalb PD Flock ALPR Use",
    page_icon="🚨",
    layout="wide"
)


st.markdown(
    """
    <h1 style='text-align: center;'>
    Is the DeKalb Police Department Using Flock Responsibly?
    </h1>
    """,
    unsafe_allow_html=True
)


st.write("""
In August 2026, 8 DeKalb County police officers were suspended
for misusing Flock data.

This was not an isolated incident, or even unique to DeKalb County;
dozens of similar stories have spread across the nation.

See the charts below and make your own decisions on how DeKalb
has been using YOUR ALPR data.

A few highlights:

- DeKalb County PD conducted over 158,000 searches in the past
  18 months, 27% using a Mobile device.
- With each search taking roughly a minute, likely longer,
  that means 158,000 minutes of searches of ALPR images.
- According to the Federal Crime Data Explorer, DeKalb County
  has not seen a meaningful increase in crime solve rates,
  even vehicular crimes.
""")

st.markdown(
    "[Federal Crime Data Explorer](https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/home)"
)


DATA_URL = (
    "https://www.dropbox.com/scl/fi/"
    "3ci7grragut6ortlh4q34/"
    "1_25-5_26-Combined_PD-Audit_v2.csv"
    "?rlkey=maujt3ko3la40ekx7pn3j0zj0&st=4a2zlkpf&dl=1"
)


# Download once and reuse
path = download_file(DATA_URL)
csv_path = sql_file_path(path)


# --------------------------------------------------
# GET OFFICER OPTIONS
# --------------------------------------------------

@st.cache_data(ttl=3600, max_entries=4)
def get_officers(path):

    source = sql_file_path(path)

    return query_csv(path, f"""
        SELECT DISTINCT "Name"
        FROM read_csv_auto(
            {source},
            header=true,
            sample_size=20000
        )
        WHERE "Name" IS NOT NULL
        ORDER BY "Name"
    """)


officer_options = get_officers(path)["Name"].tolist()


name = st.multiselect(
    "Filter by Officer Name",
    options=officer_options,
    default=officer_options
)


# --------------------------------------------------
# GET ALL CHART DATA IN ONE DATABASE QUERY
# --------------------------------------------------

@st.cache_data(ttl=1800, max_entries=8)
def get_dashboard_data(path, selected_names):

    if not selected_names:
        return None

    source = sql_file_path(path)

    placeholders = ", ".join(
        ["?"] * len(selected_names)
    )

    sql = f"""
    WITH base AS (

        SELECT
            "Name",
            COALESCE(
                CASE
                    WHEN "Reason Category" IS NULL
                      OR "Reason Category" IN ('Unknown', 'nan')
                    THEN 'Other / Uncategorized'
                    ELSE "Reason Category"
                END,
                'Other / Uncategorized'
            ) AS reason,

            "Search Type",

            EXTRACT(
                HOUR FROM timezone(
                    'America/New_York',
                    TRY_CAST("Search Time" AS TIMESTAMPTZ)
                )
            )::INTEGER AS hour

        FROM read_csv_auto(
            {source},
            header=true,
            sample_size=20000
        )

        WHERE "Name" IN ({placeholders})
    ),

    after_hours AS (

        SELECT *
        FROM base
        WHERE hour < 4 OR hour >= 22

    ),

    top_after_hours AS (

        SELECT "Name"
        FROM after_hours
        GROUP BY "Name"
        ORDER BY COUNT(*) DESC
        LIMIT 20

    )

    SELECT
        'officer' AS chart,
        "Name" AS label,
        '' AS secondary,
        COUNT(*) AS count
    FROM base
    GROUP BY "Name"
    ORDER BY count DESC
    LIMIT 30

    UNION ALL

    SELECT
        'reason',
        reason,
        '',
        COUNT(*)
    FROM base
    GROUP BY reason

    UNION ALL

    SELECT
        'hour',
        CAST(hour AS VARCHAR),
        '',
        COUNT(*)
    FROM base
    WHERE hour IS NOT NULL
    GROUP BY hour

    UNION ALL

    SELECT
        'search_type',
        "Search Type",
        '',
        COUNT(*)
    FROM base
    WHERE "Search Type" NOT IN (
        'searchSummary - Mobile',
        'multiGeo',
        'convoy'
    )
    AND "Search Type" IS NOT NULL
    GROUP BY "Search Type"

    UNION ALL

    SELECT
        'after_hours',
        a."Name",
        a.reason,
        COUNT(*)
    FROM after_hours a
    INNER JOIN top_after_hours t
        ON a."Name" = t."Name"
    GROUP BY a."Name", a.reason
    """

    with __import__("duckdb").connect(
        database=":memory:",
        config={
            "memory_limit": "1GB",
            "threads": 2,
            "temp_directory": "/tmp/dekalb_flock_data"
        }
    ) as con:

        return con.execute(
            sql,
            list(selected_names)
        ).fetchdf()


# --------------------------------------------------
# DISPLAY CHARTS
# --------------------------------------------------

if not name:

    st.warning("Please select at least one officer.")

else:

    data = get_dashboard_data(
        path,
        tuple(name)
    )

    officer_counts = data[data["chart"] == "officer"].copy()
    reason_counts = data[data["chart"] == "reason"].copy()
    hourly_counts = data[data["chart"] == "hour"].copy()
    search_type_counts = data[data["chart"] == "search_type"].copy()
    after_hours_counts = data[data["chart"] == "after_hours"].copy()


    # CHART 1: OFFICER SEARCHES

    if not officer_counts.empty:

        fig = px.bar(
            officer_counts,
            x="count",
            y="label",
            orientation="h",
            text="count",
            title="Searches by Officer Name"
        )

        fig.update_traces(
            marker=dict(
                color=officer_counts["count"],
                colorscale="Blues"
            ),
            texttemplate="%{text:,}",
            textposition="outside"
        )

        fig.update_layout(
            height=600,
            font=dict(size=16, color="#1a1a1a"),
            title_font_size=24,
            yaxis={
                "categoryorder": "total ascending",
                "title": "Officer"
            },
            xaxis_title="Number of Searches"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # CHART 2: REASON CATEGORY

    if not reason_counts.empty:

        fig = px.bar(
            reason_counts,
            x="label",
            y="count",
            text="count",
            title="Searches by Reason Category"
        )

        fig.update_traces(
            marker=dict(
                color=reason_counts["count"],
                colorscale="Blues"
            ),
            texttemplate="%{text:,}",
            textposition="outside"
        )

        fig.update_layout(
            height=600,
            font=dict(size=16),
            title_font_size=24,
            xaxis_title="Reason Category",
            yaxis_title="Number of Searches"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # CHART 3: HOURLY SEARCHES

    if not hourly_counts.empty:

        hourly_counts["Hour"] = (
            hourly_counts["label"].astype(int)
        )

        hourly_counts = (
            hourly_counts
            .set_index("Hour")["count"]
            .reindex(range(24), fill_value=0)
            .reset_index()
        )

        fig = px.line(
            hourly_counts,
            x="Hour",
            y="count",
            markers=True,
            title="Searches by Hour of Day"
        )

        fig.update_layout(
            height=500,
            font=dict(size=14),
            title_font_size=24,
            xaxis_title="Hour of Day (24h)",
            yaxis_title="Number of Searches",
            xaxis=dict(
                tickmode="linear",
                dtick=2,
                range=[0, 23]
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # CHART 4: SEARCH TYPES

    if not search_type_counts.empty:

        fig = px.pie(
            search_type_counts,
            names="label",
            values="count",
            title="Searches by Search Type"
        )

        fig.update_traces(
            textinfo="percent+label",
            textfont_size=14
        )

        fig.update_layout(
            height=600,
            font=dict(size=14),
            title_font_size=24
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # CHART 5: AFTER HOURS

    if not after_hours_counts.empty:

        fig = px.bar(
            after_hours_counts,
            x="label",
            y="count",
            color="secondary",
            text="count",
            orientation="v",
            barmode="stack",
            title="Searches Between 10 PM - 4 AM by Officer and Reason"
        )

        fig.update_traces(
            texttemplate="%{text:,}",
            textposition="inside"
        )

        fig.update_layout(
            height=600,
            font=dict(size=16),
            title_font_size=24,
            xaxis_title="Officer",
            yaxis_title="Number of Searches",
            xaxis={
                "categoryorder": "total descending"
            },
            legend_title="Reason Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No after-hours searches found for the selected officers.")


st.divider()

st.write(
    "Want to dive in deeper? Download the original CSV:"
)

st.markdown(
    "[Download DeKalb PD Audit CSV]"
    "(https://www.dropbox.com/scl/fi/"
    "3ci7grragut6ortlh4q34/"
    "1_25-5_26-Combined_PD-Audit_v2.csv"
    "?rlkey=maujt3ko3la40ekx7pn3j0zj0&st=5umlwepl&dl=0)"
)
