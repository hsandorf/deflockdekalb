import gdown
import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Streamlit Google Drive Parquet Streamer")

# Reconstructs Google Drive link for direct download
FILE_ID = '1vRVrvN3wzdSpbD6chKJi1TthZmZY8KpF'
@st.cache_data
def load_gdrive_parquet(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "data.parquet"
    gdown.download(url, output, quiet=True)
    return pd.read_parquet(output)

df = load_gdrive_parquet(FILE_ID)
