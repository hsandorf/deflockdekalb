import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


st.set_page_config(page_title="DeKalb PD Flock ALPR Use", page_icon="🚨", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'Is the DeKalb Police Department Using Flock Responsibly?</h1>",
    unsafe_allow_html=True
)

st.title(
    "Is the DeKalb Police Department Using Flock Responsibly?"
)

st.write(
    """In August 2026, 8 DeKalb County police officers were suspended for misusing Flock data. 
    This was not an isolated incident, or even unique to DeKalb County; dozens of similar stories have spread across the nation, just search 'Flock misuse' and see tons of examples.
      See the charts below and make your own decisions on how DeKalb has been using YOUR ALPR data. A few highlights:  
      -DeKalb County PD conducted over 158,000 searches in the past 18 months, 27% using a Mobile device  
      -With each search taking roughly a minute, likely longer, that means 158,000 minutes of searches ALPR images. Over an entire year of working days for one officer.  
      -According to the Federal Crime Data Explorer, DeKalb County has not seen a meaningful increase in crime solve rates, even vehiclular crimes https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/home """
  )

DATA_URL = "https://www.dropbox.com/scl/fi/3ci7grragut6ortlh4q34/1_25-5_26-Combined_PD-Audit_v2.csv?rlkey=maujt3ko3la40ekx7pn3j0zj0&st=4a2zlkpf&dl=1"

@st.cache_data
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

df = load_csv(DATA_URL)

print(df.head())


df['Search Time'] = pd.to_datetime(df['Search Time'], utc=True).dt.tz_convert('America/New_York')
df['Search Time'] = (
    pd.to_datetime(df['Search Time'], utc=True)
    .dt.tz_convert('America/New_York')
    .dt.tz_localize(None)
)

df['Hour'] = df['Search Time'].dt.hour

df['Reason Category'] = df['Reason Category'].replace('Unknown','Other / Uncategorized')
df['Reason Category'] = df['Reason Category'].replace('nan','Other / Uncategorized')


name = st.multiselect(
    'Filter by Officer Name',
    options=df['Name'].unique(),
    default=df['Name'].unique()
)


filtered = df[
    df['Name'].isin(name)]

if filtered.empty:
    st.warning('No data matches the selected filters.')
else:
    
    fig = px.bar(
        filtered['Name'].value_counts().head(30).reset_index(),
        x='count', y='Name',
        orientation='h',
        text='count')

    fig.update_traces(
        marker=dict(
            color=filtered['Name'].value_counts().values,
            colorscale='Blues'
        )
    )
    fig.update_layout(
        font=dict(size=16, color="#1a1a1a"),
        title=dict(text='Searches by Officer Name', font=dict(size=24)),
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)





fig = px.bar(
    filtered['Reason Category'].value_counts().reset_index(),
    x='Reason Category', y='count',
    orientation='v',
    text='count')

fig.update_traces(
    marker=dict(
        color=filtered['Reason Category'].value_counts().values,
        colorscale='Blues'
    )
)
fig.update_layout(
    font=dict(size=16, color="#1a1a1a"),
    title=dict(text='Searches by Reason Category', font=dict(size=24)),
    height=600,
    yaxis={'categoryorder': 'total ascending'}
)
fig.update_traces(texttemplate='%{text:,}', textposition='outside')
fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig, use_container_width=True)




hourly_counts = filtered['Hour'].value_counts().sort_index().reindex(range(24), fill_value=0)
hourly_df = hourly_counts.reset_index()
hourly_df.columns = ['Hour', 'count']

fig = px.line(
    hourly_df,
    x='Hour',
    y='count',
    markers=True
)

fig.update_layout(
    height=500,
    font=dict(size=14),
    title=dict(text='Searches by Hour of Day', font=dict(size=24)),
    xaxis_title='Hour of Day (24h)',
    yaxis_title='Number of Searches',
    xaxis=dict(tickmode='linear', dtick=2, range=[0, 23])
)



st.plotly_chart(fig, use_container_width=True)


search_types = filtered[
    (filtered['Search Type'] != 'searchSummary - Mobile') &
    (filtered['Search Type'] != 'multiGeo') &
    (filtered['Search Type'] != 'convoy')
]

search_type_counts = search_types['Search Type'].value_counts().reset_index()
search_type_counts.columns = ['Search Type', 'count']


fig = px.pie(
    search_type_counts,
    names='Search Type',
    values='count',
    title='Searches by Search Type'
)

fig.update_traces(textinfo='percent+label', textfont_size=14)
fig.update_layout(
    font=dict(size=14),
    title=dict(font=dict(size=24)),
    height=600
)

st.plotly_chart(fig, use_container_width=True)


after_hours_mask = (df['Hour'] < 4) | (df['Hour'] >= 22)
after_hours = df[after_hours_mask]

# Count by Officer and Reason Category together
grouped = after_hours.groupby(['Name', 'Reason Category']).size().reset_index(name='count')


top_officers = after_hours['Name'].value_counts().head(20).index
grouped = grouped[grouped['Name'].isin(top_officers)]


fig = px.bar(
    grouped,
    x='count',
    y='Name',
    color='Reason Category',
    orientation='h',
    text='count',
    barmode='stack'
)

fig.update_traces(texttemplate='%{text:,}', textposition='inside')
fig.update_layout(
    font=dict(size=16, color="#1a1a1a"),
    title=dict(text='Searches Between 10 PM - 4 AM by Officer and Reason', font=dict(size=24)),
    height=600,
    xaxis_title='Number of Searches',
    yaxis_title='Officer',
    xaxis={'categoryorder': 'total descending'}
)

st.plotly_chart(fig, use_container_width=True)





st.write("Want to dive in deeper? Download CSVs at https://www.dropbox.com/scl/fi/3ci7grragut6ortlh4q34/1_25-5_26-Combined_PD-Audit_v2.csv?rlkey=maujt3ko3la40ekx7pn3j0zj0&st=5umlwepl&dl=0")
