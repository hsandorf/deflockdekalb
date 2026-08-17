import pandas as pd
import streamlit as st

st.title("Streamlit Google Drive Parquet Streamer")

# Reconstructs Google Drive link for direct download
FILE_ID = "Y112VRcpdgb2HxHwH565b5rsdOUEXjJR69"
DATA_URL = f"https://google.com{FILE_ID}"

@st.cache_data
def load_gdrive_parquet(url):
    return pd.read_parquet(url)

with st.spinner("Streaming 635MB Parquet file from Google Drive..."):
    df = load_gdrive_parquet(DATA_URL)

st.success("Successfully loaded!")
st.dataframe(df.head())

