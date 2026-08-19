import streamlit as st

st.set_page_config(page_title="DeKalb ALPR Data Search", page_icon="👮", layout="wide")

pages = [
    st.Page("app_pages/about_flock.py", title="About Automated License Plate Readers (Flock Cameras)", icon="❓"),
    st.Page("app_pages/dekalb_pd.py", title="DeKalb PD Flock ALPR Use", icon="🚓"),
    st.Page("app_pages/network_audit.py", title="Who Else is Searching DeKalb's Data?", icon="🔍"),
]

pg = st.navigation(pages)

with st.sidebar:
    org_types = st.multiselect('Filter by Org Type', options=df['Org Type'].unique(), default=df['Org Type'].unique())
    
pg.run()
