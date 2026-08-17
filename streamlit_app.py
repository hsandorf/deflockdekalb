import gdown
import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Streamlit Google Drive Parquet Streamer")

#st.title("Streamlit Google Drive Parquet Streamer")

import pandas as pd
import streamlit as st

DATA_URL = "https://www.dropbox.com/scl/fi/oqk2y6nnp6vcxrf67hwy6/1_25-5_26-Combined-Network.parquet?rlkey=xul1b4j7hnjhipm6fv6ah3snx&st=1jg7kjqn&dl=1"

#@st.cache_data
def load_parquet(url: str) -> pd.DataFrame:
    return pd.read_parquet(url)

df = load_parquet(DATA_URL)

print(df.head())
