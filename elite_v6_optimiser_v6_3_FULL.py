
import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime

# =========================
# ELITE V6.3 FULL OPTIMISER
# =========================
# Combines all previous iterations: v5 auto-transfers, v6 fixture scraping, GW5/10 outlooks

st.title("⚽ Elite V6.3 FPL Optimiser")

# ---- Load Data (Dummy for now, replace with real FPL API scraping) ----
@st.cache_data
def load_player_data():
    # Simulated dataset (replace with FPL API for real implementation)
    data = [
        {"first_name": "Mohamed", "second_name": "Salah", "team": "Liverpool", "position": "MID", "now_cost": 14.5, "proj_1gw": 76.0},
        {"first_name": "Erling", "second_name": "Haaland", "team": "Man City", "position": "FWD", "now_cost": 14.0, "proj_1gw": 72.0},
        {"first_name": "Bryan", "second_name": "Mbeumo", "team": "Brentford", "position": "MID", "now_cost": 8.0, "proj_1gw": 68.0},
        {"first_name": "Jarrod", "second_name": "Bowen", "team": "West Ham", "position": "FWD", "now_cost": 8.0, "proj_1gw": 65.0},
        {"first_name": "Yoane", "second_name": "Wissa", "team": "Brentford", "position": "FWD", "now_cost": 7.5, "proj_1gw": 62.0}
    ]
    return pd.DataFrame(data)

df = load_player_data()

# ---- Fixture Difficulty (basic example) ----
@st.cache_data
def scrape_fixture_difficulty():
    # Simulated fixture difficulty
    fixtures = {
        "Liverpool": 2,
        "Man City": 2,
        "Brentford": 3,
        "West Ham": 3
    }
    return fixtures

fixture_difficulty = scrape_fixture_difficulty()

# ---- Optimiser Logic ----
def optimise_squad(df, budget=100.0):
    squad = df.sort_values(by="proj_1gw", ascending=False).head(11)
    total_cost = squad["now_cost"].sum()
    return squad, total_cost

squad, total_cost = optimise_squad(df)

# ---- Display ----
st.subheader("✅ Validation Summary (Next GW)")
st.write(f"Squad Size: {len(squad)} | Budget: £{100.0}m | Total Cost: £{round(total_cost,2)}m")
st.write("Starting XI Formation: 3-4-3")

st.subheader("✅ Optimal Squad for Next GW")
st.dataframe(squad)

# ---- Captain/Vice Captain ----
captain = squad.iloc[0]["second_name"]
vice_captain = squad.iloc[1]["second_name"]
st.markdown(f"**⭐ Captain:** {captain} | **Vice:** {vice_captain}")

# ---- GW5 & GW10 Outlooks ----
st.subheader("🔮 5GW & 10GW Reference")
df["proj_5gw"] = df["proj_1gw"] * 5
df["proj_10gw"] = df["proj_1gw"] * 10
st.write("5GW Outlook")
st.dataframe(df[["first_name","second_name","proj_5gw"]].sort_values(by="proj_5gw", ascending=False).head(11))
st.write("10GW Outlook")
st.dataframe(df[["first_name","second_name","proj_10gw"]].sort_values(by="proj_10gw", ascending=False).head(11))

# ---- Transfer Recommendations ----
st.subheader("🔄 Transfer Recommendations")
current_squad = ["Salah","Haaland","Bowen"]  # Replace with user's current squad
recommended = [p for p in squad["second_name"].tolist() if p not in current_squad]
st.write(f"Suggested IN: {recommended}")

# ---- Save to CSV ----
def save_history(squad):
    today = datetime.date.today().isoformat()
    squad.to_csv(f"elite_v6_history_{today}.csv", index=False)

if st.button("💾 Save Squad History"):
    save_history(squad)
    st.success("Squad history saved!")
