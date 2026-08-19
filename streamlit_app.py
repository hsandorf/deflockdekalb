import streamlit as st

st.set_page_config(page_title="DeKalb ALPR Data Search", page_icon="👮", layout="wide")

pages = [
    st.Page("pages/about_flock.py", title="About Automated License Plate Readers (Flock Cameras)", icon="❓"),
    st.Page("pages/dekalb_pd.py", title="DeKalb PD Flock ALPR Use", icon="🚓"),
    st.Page("pages/network_audit.py", title="Who Else is Searching DeKalb's Data?", icon="🔍"),
]

pg = st.navigation(pages)

pg.run()
