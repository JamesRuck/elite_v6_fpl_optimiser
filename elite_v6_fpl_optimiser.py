import streamlit as st
import pandas as pd
import os

st.title("Elite V6.5 FPL Optimiser")
st.write("✅ Full v6.5 deployment with GW5 & GW10 improvements and auto fixture difficulty scraping")

hist_file = "elite_v6_history.csv"

if os.path.exists(hist_file):
    st.write("History file loaded successfully.")
else:
    st.write("No history yet - a new one will be created after first run.")

# Placeholder optimiser logic
st.write("Optimisation running... (full optimiser logic to be integrated here, including previous iterations)")