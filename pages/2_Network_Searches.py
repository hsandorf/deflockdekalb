
import streamlit as st
import plotly.express as px

from data_utils import download_file, query_parquet, sql_file_path


st.set_page_config(
    page_title="Who's Searching DeKalb's Data?",
    page_icon="🤔",
    layout="wide"
)


st.markdown(
    """
    <h1 style='text-align:center;'>
    Who's Searching DeKalb's Data?
    </h1>
    """,
    unsafe_allow_html=True
)


st.write("""
From January 2025 - May 2026 there were over 17 million
network searches on DeKalb County Flock camera data.

A coalition of DeKalb County residents obtained Flock records
via legal FOIA requests. Here is what we found.

- Police Departments Across Georgia accounted for the most
  Flock Searches, but Texas and Florida were not far behind.
- Over 2.5 million searches were conducted without being linked
  to a specific case. Despite this, Flock only blocked 5 searches
  in 18 months, in violation of their stated standards.
- These records only included the organization name, not the
  individual's. No way to validate who these people are and
  their roles.
- Flock claims they only collect images of cars and license
  plates, but freeform text searches tell a different story.
  Free text prompts included phrases such as "a person",
  "person walking", and "person wearing orange shirt".
- Flock claims to only keep data for 30 days, but many search
  timeframes expanded past that limit without error.

See below to explore Flock data requests from DeKalb cameras yourself!
""")


DATA_URL = (
    "https://www.dropbox.com/scl/fi/"
    "tvzcwws2o0l4prnvjo8r9/"
    "1_25-5_26-Combined-Network.parquet"
    "?rlkey=7hmqkovb21r3xcgqswb6ea8r8&st=sqezzl0r&dl=1"
)


# --------------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------------

path = download_file(DATA_URL)
parquet_path = sql_file_path(path)


# --------------------------------------------------
# GET FILTER OPTIONS
# --------------------------------------------------

@st.cache_data(ttl=3600, max_entries=4)
def get_filter_options(path):

    source = sql_file_path(path)

    return query_parquet(path, f"""

        SELECT
            'org_type' AS kind,
            CAST("Org Type" AS VARCHAR) AS value
        FROM read_parquet({source})
        WHERE "Org Name" NOT ILIKE '%DeKalb%'
          AND "Org Type" IS NOT NULL
        GROUP BY "Org Type"

        UNION ALL

        SELECT
            'state' AS kind,
            CAST(State AS VARCHAR) AS value
        FROM read_parquet({source})
        WHERE "Org Name" NOT ILIKE '%DeKalb%'
          AND State IS NOT NULL
        GROUP BY State

        ORDER BY kind, value

    """)


options = get_filter_options(path)

org_options = (
    options.loc[
        options["kind"] == "org_type", "value"
    ].tolist()
)

state_options = (
    options.loc[
        options["kind"] == "state", "value"
    ].tolist()
)


# --------------------------------------------------
# STATE MAP
# --------------------------------------------------

@st.cache_data(ttl=3600, max_entries=4)
def get_state_counts(path):

    source = sql_file_path(path)

    return query_parquet(path, f"""

        SELECT
            State,

            COUNT(*) AS Searches,

            array_to_string(
                list_slice(
                    list_sort(
                        list_distinct(
                            list("Org Name")
                        )
                    ),
                    1,
                    10
                ),
                ', '
            ) AS Orgs

        FROM read_parquet({source})

        WHERE "Org Name" NOT ILIKE '%DeKalb%'
          AND State IS NOT NULL

        GROUP BY State

        ORDER BY Searches DESC

    """)


st.header("Searches by State")

state_counts = get_state_counts(path)


fig = px.choropleth(
    state_counts,
    locations="State",
    locationmode="USA-states",
    color="Searches",
    scope="usa",
    color_continuous_scale="Blues",
    hover_name="State",
    hover_data={
        "Searches": ":,",
        "Orgs": True,
        "State": False
    }
)

fig.update_layout(
    height=600,
    font=dict(size=14),
    title=dict(
        text="Searches by State",
        font=dict(size=24)
    ),
    geo=dict(
        bgcolor="rgba(0,0,0,0)"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

st.header("Searches by Org Name")

col1, col2 = st.columns(2)

with col1:

    org_types = st.multiselect(
        "Filter by Org Type",
        options=org_options,
        default=org_options
    )

with col2:

    states = st.multiselect(
        "Filter by State",
        options=state_options,
        default=state_options
    )


# --------------------------------------------------
# QUERY FILTERED DATA
# --------------------------------------------------

@st.cache_data(ttl=1800, max_entries=8)
def get_filtered_counts(path, selected_org_types, selected_states):

    if not selected_org_types or not selected_states:
        return None

    source = sql_file_path(path)

    org_marks = ", ".join(
        ["?"] * len(selected_org_types)
    )

    state_marks = ", ".join(
        ["?"] * len(selected_states)
    )

    where_clause = f"""
        WHERE "Org Name" NOT ILIKE '%DeKalb%'
          AND "Org Type" IN ({org_marks})
          AND State IN ({state_marks})
    """

    params = (
        list(selected_org_types) +
        list(selected_states)
    )

    sql = f"""

        WITH filtered AS (

            SELECT
                "Org Name",
                Category

            FROM read_parquet({source})

            {where_clause}

        ),

        top_orgs AS (

            SELECT
                "Org Name",
                COUNT(*) AS count

            FROM filtered

            GROUP BY "Org Name"

            ORDER BY count DESC

            LIMIT 20

        )

        SELECT
            'org' AS chart,
            "Org Name" AS label,
            count

        FROM top_orgs

        UNION ALL

        SELECT
            'category' AS chart,
            COALESCE(
                CAST(Category AS VARCHAR),
                'Uncategorized'
            ) AS label,
            COUNT(*) AS count

        FROM filtered

        GROUP BY Category

    """

    import duckdb

    with duckdb.connect(
        database=":memory:",
        config={
            "memory_limit": "1GB",
            "threads": 2,
            "temp_directory": "/tmp/dekalb_flock_data"
        }
    ) as con:

        return con.execute(
            sql,
            params
        ).fetchdf()


filtered_counts = get_filtered_counts(
    path,
    tuple(org_types),
    tuple(states)
)


# --------------------------------------------------
# DISPLAY CHARTS
# --------------------------------------------------

if filtered_counts is None:

    st.info("Select at least one Org Type and one State.")

else:

    org_counts = filtered_counts[
        filtered_counts["chart"] == "org"
    ].copy()

    category_counts = filtered_counts[
        filtered_counts["chart"] == "category"
    ].copy()


    if filtered_counts.empty:

        st.warning("No data matches the selected filters.")

    else:

        # ORGANIZATION CHART

        if not org_counts.empty:

            fig = px.bar(
                org_counts,
                x="count",
                y="label",
                orientation="h",
                text="count",
                title="Searches by Org Name"
            )

            fig.update_traces(
                marker=dict(
                    color=org_counts["count"],
                    colorscale="Blues"
                ),
                texttemplate="%{text:,}",
                textposition="outside"
            )

            fig.update_layout(
                font=dict(
                    size=16,
                    color="#1a1a1a"
                ),
                title_font_size=24,
                height=600,
                yaxis={
                    "categoryorder": "total ascending",
                    "title": "Organization"
                },
                xaxis_title="Number of Searches"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # CATEGORY CHART

        if not category_counts.empty:

            fig = px.bar(
                category_counts,
                x="label",
                y="count",
                text="count",
                title="Searches by Reason Category"
            )

            fig.update_traces(
                marker=dict(
                    color=category_counts["count"],
                    colorscale="Blues"
                ),
                texttemplate="%{text:,}",
                textposition="outside"
            )

            fig.update_layout(
                font=dict(
                    size=16,
                    color="#1a1a1a"
                ),
                title_font_size=24,
                height=600,
                xaxis_title="Reason Category",
                yaxis_title="Number of Searches"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


st.text(
    'Reasons were grouped based on the presence of case #s '
    'or keywords in the "Reason" field completed by the Flock user.'
)


st.divider()

st.write("Want to dive in deeper? Download the original data:")

st.markdown(
    "[Download Network Audit Data]"
    "(https://www.dropbox.com/scl/fi/"
    "znyj5de1fty5hxsdm477w/"
    "5_1_2026-5_31_2026-DeKalb_County_GA_PD-Network-Audit.zip"
    "?rlkey=tjajzkn64djv4loibksr1tofs&st=eftftyll&dl=0)"
)
