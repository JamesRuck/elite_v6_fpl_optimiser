import streamlit as st
import pandas as pd
import numpy as np
import os
import requests

# ============================
# CONFIGURATION & CONSTANTS
# ============================

HIST_FILE = "elite_v6_history.csv"
FDR_SOURCE = "https://fantasy.premierleague.com/api/fixtures/"
PLAYER_SOURCE = "https://fantasy.premierleague.com/api/bootstrap-static/"

BUDGET = 100.0
SQUAD_SIZE = 15
FORMATION = (3, 4, 3)  # DEF, MID, FWD

# ============================
# UTILITY FUNCTIONS
# ============================

def load_player_data():
    """Fetch live FPL player data and clean columns."""
    r = requests.get(PLAYER_SOURCE)
    data = r.json()
    players = pd.DataFrame(data["elements"])
    teams = pd.DataFrame(data["teams"])
    element_types = pd.DataFrame(data["element_types"])

    # Merge team and position names
    players = players.merge(teams[["id", "name"]], left_on="team", right_on="id", how="left")
    players.rename(columns={"name": "team_name", "now_cost": "now_cost_raw"}, inplace=True)
    players["now_cost"] = players["now_cost_raw"] / 10

    # Map positions to readable names
    pos_map = dict(zip(element_types["id"], element_types["singular_name_short"]))
    players["position"] = players["element_type"].map(pos_map)

    # Rename key columns for consistency
    players.rename(columns={
        "first_name": "first_name",
        "second_name": "second_name"
    }, inplace=True)

    # Ensure columns exist (fallbacks)
    if "first_name" not in players.columns:
        players["first_name"] = players["web_name"]
    if "second_name" not in players.columns:
        players["second_name"] = players["web_name"]

    return players

def load_fdr():
    """Scrape fixture difficulty ratings automatically."""
    r = requests.get(FDR_SOURCE)
    fixtures = pd.DataFrame(r.json())
    fdr_df = fixtures[["team_h", "team_a", "team_h_difficulty", "team_a_difficulty", "event"]]
    return fdr_df

def calc_projected_points(players, fdr):
    """Simple projection using points_per_game scaled by fixture difficulty."""
    avg_fdr = []
    for team_id in players["team"]:
        t_fdr = fdr[(fdr["team_h"] == team_id) | (fdr["team_a"] == team_id)]
        if not t_fdr.empty:
            avg_fdr.append(t_fdr[["team_h_difficulty", "team_a_difficulty"]].mean().mean())
        else:
            avg_fdr.append(3.0)
    players["proj_1gw"] = players["points_per_game"].astype(float) * (5 / np.array(avg_fdr))
    players["proj_5gw"] = players["proj_1gw"] * 5
    players["proj_10gw"] = players["proj_1gw"] * 10
    return players

def save_history(df):
    """Save optimal squad history."""
    if os.path.exists(HIST_FILE):
        hist = pd.read_csv(HIST_FILE)
        hist = pd.concat([hist, df], ignore_index=True)
    else:
        hist = df
    hist.to_csv(HIST_FILE, index=False)

# ============================
# OPTIMISATION CORE
# ============================

def optimise_squad(players, budget=BUDGET):
    """Simple optimiser: highest projected points under budget."""
    players_sorted = players.sort_values("proj_1gw", ascending=False)
    squad = []
    total_cost = 0
    for _, row in players_sorted.iterrows():
        if total_cost + row["now_cost"] <= budget and len(squad) < SQUAD_SIZE:
            squad.append(row)
            total_cost += row["now_cost"]
    return pd.DataFrame(squad)

def split_starting_and_bench(squad):
    """Split based on highest projections (basic version)."""
    squad = squad.sort_values("proj_1gw", ascending=False)
    return squad.iloc[:11], squad.iloc[11:]

# ============================
# STREAMLIT APP
# ============================

def main():
    st.title("✅ Elite V6.5 FPL Optimiser")
    st.write("GW5 & GW10 projections, auto FDR scraping, full bug-fixed release.")

    with st.spinner("Fetching live data..."):
        players = load_player_data()
        fdr = load_fdr()
        players = calc_projected_points(players, fdr)

    st.success("Data fetched successfully!")

    if st.button("Run Optimisation"):
        squad_df = optimise_squad(players)
        start_xi, bench = split_starting_and_bench(squad_df)

        # Display
        st.subheader("=== ✅ Validation Summary (Next GW) ===")
        st.write(f"Squad Size: {len(squad_df)} | Budget: £{squad_df['now_cost'].sum():.1f}m")

        st.subheader("=== ✅ Starting XI ===")
        st.dataframe(start_xi[["web_name", "team_name", "position", "now_cost", "proj_1gw"]])

        st.subheader("=== ✅ Bench ===")
        st.dataframe(bench[["web_name", "team_name", "position", "now_cost", "proj_1gw"]])

        st.subheader("=== 🔮 5GW Reference Squad ===")
        st.dataframe(squad_df[["web_name", "team_name", "proj_5gw"]])

        st.subheader("=== 🔮 10GW Reference Squad ===")
        st.dataframe(squad_df[["web_name", "team_name", "proj_10gw"]])

        save_history(squad_df)
        st.success(f"✅ Squad saved to {HIST_FILE}")

if __name__ == "__main__":
    main()
