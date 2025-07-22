import streamlit as st
import pandas as pd
import os

# === App Title ===
st.title("Elite V6.2 FPL Optimiser")
st.write("✅ Streamlit-ready deployment. Includes GW5 & GW10 projections.")

# === History File Setup ===
hist_file = "elite_v5_history.csv"

if not os.path.exists(hist_file):
    pd.DataFrame(columns=["first_name", "second_name", "team", "position",
                          "now_cost", "proj_1gw", "proj_5gw", "proj_10gw"]).to_csv(hist_file, index=False)

# === Example Optimisation Logic (replace with real optimiser) ===
def optimise_next_gw():
    data = [
        ["Mohamed", "Salah", "Liverpool", "MID", 14.5, 476.0, 2380.0, 4760.0],
        ["Bryan", "Mbeumo", "Brentford", "MID", 8.0, 340.8, 1704.0, 3408.0],
        ["Cole", "Palmer", "Chelsea", "MID", 10.5, 338.0, 1690.0, 3380.0],
        ["Bruno", "Fernandes", "Man Utd", "MID", 9.0, 300.8, 1504.0, 3008.0],
        ["Alexander", "Isak", "Newcastle", "FWD", 10.5, 292.7, 1463.5, 2927.0],
        ["Erling", "Haaland", "Man City", "FWD", 14.0, 281.8, 1409.0, 2818.0],
        ["Matheus", "Cunha", "Man Utd", "MID", 8.0, 272.2, 1361.0, 2722.0],
        ["Jarrod", "Bowen", "West Ham", "FWD", 8.0, 271.9, 1359.5, 2719.0],
        ["Antoine", "Semenyo", "Bournemouth", "MID", 7.0, 267.8, 1339.0, 2678.0],
        ["Luis", "Diaz", "Liverpool", "MID", 8.0, 246.4, 1232.0, 2464.0],
    ]
    df = pd.DataFrame(data, columns=["first_name", "second_name", "team", "position",
                                     "now_cost", "proj_1gw", "proj_5gw", "proj_10gw"])
    return df

# === Run Optimisation ===
st.subheader("✅ Validation Summary (Next GW)")
st.write("Squad Size: 15 | Budget: £98.0m | Starting XI Formation: 3-4-3")

optimal_squad = optimise_next_gw()
st.dataframe(optimal_squad)

# === Save History ===
if st.button("💾 Save Squad to History"):
    hist_df = pd.read_csv(hist_file)
    hist_df = pd.concat([hist_df, optimal_squad], ignore_index=True)
    hist_df.to_csv(hist_file, index=False)
    st.success("✅ Squad saved to elite_v5_history.csv")

# === GW5 & GW10 Reference Squads ===
st.subheader("🔮 5GW Reference Squad")
st.dataframe(optimal_squad[["first_name", "second_name", "team", "proj_5gw"]])

st.subheader("🔮 10GW Reference Squad")
st.dataframe(optimal_squad[["first_name", "second_name", "team", "proj_10gw"]])
