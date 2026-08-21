import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker



st.set_page_config(page_title="Who's Searching DeKalb's Data?", page_icon="🤔", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>Who's Searching DeKalb's Data?</h1>",
    unsafe_allow_html=True
)

st.write(
    """From January 2025 - May 2026 there were over 17 million network searches on DeKalb County Flock camera data.  
A coalition of DeKalb County residents obtained Flock records via legal FOIA requests. Here is what we found.  

- Police Departments Across Georgia accounted for the most Flock Searches, but Texas and Florida were not far behind.  
- Over 2.5 million searches were conducted without being linked to a specific case. Despite this, Flock only blocked 5 searches in 18 months, in violation of their stated standards.  
- These records only included the organization name, not the individual's. No way to validate who these people are and their roles.  
- Flock claims they only collect images of cars and license plates, but freeform text searches tell a different story. Free text prompts included the phrases "a person", "person walking", and "person wearing orange shirt". There is an entire search option for "objectClass:people". 
- Flock claims to only keep data for 30 days, but many search timeframes expanded past that limit without error.  

See below to explore Flock data requests from DeKalb cameras yourself!"""
)


DATA_URL = "https://www.dropbox.com/scl/fi/tvzcwws2o0l4prnvjo8r9/1_25-5_26-Combined-Network.parquet?rlkey=7hmqkovb21r3xcgqswb6ea8r8&st=sqezzl0r&dl=1"

@st.cache_data
def load_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)

df = load_parquet(DATA_URL)
print(df.head())

df = df[df['Org Name'].str.contains('DeKalb')]

state_counts = df.groupby('State').agg(
    Searches=('State', 'count'),
    Orgs=('Org Name', lambda x: ', '.join(sorted(x.unique())[:10]))  # cap list length so hover isn't huge
).reset_index()

fig = px.choropleth(
    state_counts,
    locations='State',
    locationmode='USA-states',
    color='Searches',
    scope='usa',
    color_continuous_scale='Blues',
    hover_name='State',
    hover_data={'Searches': True, 'Orgs': True, 'State': False,'Searches': ':,'}
)

fig.update_layout(
    height=600,
    font=dict(size=14),
    title=dict(text='Searches by State', font=dict(size=24)),
    geo=dict(bgcolor='rgba(0,0,0,0)')
)

st.plotly_chart(fig, use_container_width=True)


st.header('Searches by Org Name') 

org_types = st.multiselect(
    'Filter by Org Type',
    options=df['Org Type'].unique(),
    default=df['Org Type'].unique()
)

states = st.multiselect(
    'Filter by State',
    options=df['State'].unique(),
    default=df['State'].unique()
)

filtered = df[
    df['Org Type'].isin(org_types) &
    df['State'].isin(states)
]

if filtered.empty:
    st.warning('No data matches the selected filters.')
else:
    
    fig = px.bar(
        filtered['Org Name'].value_counts().head(20).reset_index(),
        x='count', y='Org Name',
        orientation='h',
        text='count')

    fig.update_traces(
        marker=dict(
            color=filtered['Org Name'].value_counts().values,
            colorscale='Blues'
        )
    )
    fig.update_layout(
        font=dict(size=16, color="#1a1a1a"),
        title=dict(text='Searches by Org Name', font=dict(size=24)),
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)



fig = px.bar(
    df['Category'].value_counts().reset_index(),
    x='Category', y='count',
    orientation='v',
    text='count')

fig.update_traces(
    marker=dict(
        color=df['Category'].value_counts().values,
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


st.text('Reasons were grouped based on the presence of case #s or keywords in the "Reason" field completed by the Flock user.')


daily_counts = filtered.groupby('Search Date').size().reset_index(name='count')

daily_counts = daily_counts[daily_counts['Search Date'] > '2025-09-01']

fig = px.line(
    daily_counts,
    x='Search Date',
    y='count',
    markers=True  # adds dots at each data point, nice for sparser data
)

fig.update_layout(
    height=500,
    font=dict(size=14),
    title=dict(text='Searches Over Time', font=dict(size=24)),
    xaxis_title='Date',
    yaxis_title='Number of Searches'
)

st.plotly_chart(fig, use_container_width=True)


st.write("Want to dive in deeper? Download CSVs at https://www.dropbox.com/scl/fi/znyj5de1fty5hxsdm477w/5_1_2026-5_31_2026-DeKalb_County_GA_PD-Network-Audit.zip?rlkey=tjajzkn64djv4loibksr1tofs&st=eftftyll&dl=0")
