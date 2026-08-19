import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

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

DATA_URL = "https://www.dropbox.com/scl/fi/3ci7grragut6ortlh4q34/1_25-5_26-Combined_PD-Audit_v2.csv?rlkey=maujt3ko3la40ekx7pn3j0zj0&st=7n4qswb6&dl=1"

@st.cache_data
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

df = load_csv(DATA_URL)

print(df.head())
