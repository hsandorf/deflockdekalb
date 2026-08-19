import streamlit as st

st.set_page_config(page_title="DeKalb ALPR Data Search", page_icon="👮", layout="wide")

pages = [
    st.Page("app_pages/overview.py", title="About Automated License Plate Readers (Flock Cameras)", icon="❓"),
    st.Page("app_pages/dekalb_pd_audit.py", title="DeKalb PD Flock ALPR Use", icon="🚓"),
    st.Page("app_pages/officer_lookup.py", title="Who Else is Searching DeKalb's Data?", icon="🔍"),
]

pg = st.navigation(pages)
pg.run()
