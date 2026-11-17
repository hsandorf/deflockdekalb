import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


st.set_page_config(page_title="Welcome to Deflock DeKalb!", page_icon="❓", layout="wide")
st.title("Welcome to Deflock DeKalb!")
st.write("Use the sidebar navigation to switch between different pages.")


st.write("""

You are probably here because you've seen news about Flock and how damaging ALPR use can be to communities and civil liberties. 
This app is meant for DeKalb County residents to explore ALPR use in our home and show why we should Deflock DeKalb.


Additonal Resources:  

https://deflock.org/ - see where ALPR cameras are near you!

https://haveibeenflocked.com/ - see if your license plate has been searched (Flock has declined to update this but promises a September update)

https://www.aclu.org/press-releases/aclu-applauds-important-supreme-court-decision-making-clear-location-data-is-protected-by-fourth-amendment - ALPR use can violate the 4th Amendment

https://www.jalopnik.com/2238664/atlanta-flock-5000-flock-cameras-fbi-crime-data-worse-police-crime-resolving/ - ALPRs do not help solve crimes

https://www.muckrock.com/foi/ - See what FOIA requests have already been submitted for your area and download data!
""")


        st.info(comment)
else:
    st.caption("No comments yet. Be the first to leave one!")
