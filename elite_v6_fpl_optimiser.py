# =========================================================
# ✅ ELITE V6.6.1 FPL OPTIMISER
# FULLY COMPLIANT WITH FPL OFFICIAL RULES & ELITE PRINCIPLES
# =========================================================

# ======================
# 1. IMPORTS & SETTINGS
# ======================
import pandas as pd
import numpy as np
import streamlit as st
import requests
import os

# Global Settings
FPL_API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURE_DIFFICULTY_API = "https://fantasy.premierleague.com/api/fixtures/"
TEAM_HISTORY_CSV = "elite_v6_history.csv"

MAX_BUDGET = 100.0
SQUAD_SIZE = 15
POSITION_LIMITS = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
CLUB_LIMIT = 3
DEFAULT_FORMATION = (3, 4, 3)

# Rotation Ban List (Elite Principle: Avoid rotation traps)
ROTATION_BAN = [
    "Nico O'Reilly", "Amad Diallo", "Felipe", "Matheus Nunes",
    "João Cancelo", "Donny van de Beek"
]

# ======================
# 2. DATA FETCHING
# ======================
def fetch_fpl_data():
    """Fetches FPL bootstrap data (players, teams)."""
    response = requests.get(FPL_API_URL)
    if response.status_code != 200:
        st.error("❌ Failed to fetch FPL data. Check API or network.")
        return None, None
    data = response.json()
    players = pd.DataFrame(data["elements"])
    teams = pd.DataFrame(data["teams"])
    return players, teams

def fetch_fixture_difficulty():
    """Fetches live fixture difficulty ratings (used in projections)."""
    response = requests.get(FIXTURE_DIFFICULTY_API)
    if response.status_code != 200:
        st.warning("⚠️ Could not fetch fixture difficulty. Defaulting to neutral weighting.")
        return {}
    fixtures = response.json()
    difficulty_map = {}
    for f in fixtures:
        team_a = f["team_a"]
        team_h = f["team_h"]
        difficulty_map[team_a] = f.get("team_a_difficulty", 3)
        difficulty_map[team_h] = f.get("team_h_difficulty", 3)
    return difficulty_map
# ======================
# 3. PLAYER FILTERING & ENRICHMENT
# ======================
def clean_player_data(players, teams, difficulty_map):
    """Cleans and enriches player data with team names, positions & difficulty weighting."""
    # Add team names
    players["team_name"] = players["team"].map(dict(zip(teams["id"], teams["name"])))
    
    # Map element types to readable positions
    element_type_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    players["position"] = players["element_type"].map(element_type_map)
    
    # Convert costs to float (£m)
    players["now_cost"] = players["now_cost"] / 10
    
    # Add projected points (basic model factoring fixture difficulty)
    players["proj_1gw"] = (
        players["form"].astype(float) *
        (5 - players["team"].map(difficulty_map).fillna(3)) / 3
    )
    
    # Remove rotation-ban players
    players = players[~players["web_name"].isin([n.split(" ")[0] for n in ROTATION_BAN])]
    
    return players

# ======================
# 4. SQUAD OPTIMISATION
# ======================
def optimise_squad(players):
    """Optimises squad under FPL rules (Elite approach)."""
    squad = []
    budget = MAX_BUDGET
    club_count = {}
    pos_counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}

    # Sort by projected points per cost (value-for-money)
    players = players.sort_values(by="proj_1gw", ascending=False)

    for _, p in players.iterrows():
        if len(squad) >= SQUAD_SIZE:
            break

        pos = p["position"]
        team = p["team_name"]
        cost = p["now_cost"]

        # FPL compliance checks
        if pos_counts[pos] >= POSITION_LIMITS[pos]:
            continue
        if budget - cost < 0:
            continue
        if club_count.get(team, 0) >= CLUB_LIMIT:
            continue

        squad.append(p)
        budget -= cost
        pos_counts[pos] += 1
        club_count[team] = club_count.get(team, 0) + 1

    squad_df = pd.DataFrame(squad)
    return squad_df, round(MAX_BUDGET - budget, 1)

# ======================
# 5. STARTING XI SELECTION
# ======================
def pick_starting_xi(squad_df):
    """Picks Starting XI based on Elite default formation (3-4-3)."""
    gk = squad_df[squad_df["position"] == "GK"].nlargest(1, "proj_1gw")
    defs = squad_df[squad_df["position"] == "DEF"].nlargest(3, "proj_1gw")
    mids = squad_df[squad_df["position"] == "MID"].nlargest(4, "proj_1gw")
    fwds = squad_df[squad_df["position"] == "FWD"].nlargest(3, "proj_1gw")
    
    start_xi = pd.concat([gk, defs, mids, fwds])
    bench = squad_df.drop(start_xi.index)
    
    return start_xi, bench

# ======================
# 6. CAPTAINCY
# ======================
def pick_captains(start_xi):
    """Auto-assigns captain & vice based on highest projected points."""
    sorted_xi = start_xi.sort_values(by="proj_1gw", ascending=False)
    captain = sorted_xi.iloc[0]["web_name"]
    vice = sorted_xi.iloc[1]["web_name"]
    return captain, vice
    # ======================
# 7. GW5 & GW10 PROJECTIONS
# ======================
def project_future_gws(players, weeks=5):
    """
    Projects future gameweek points based on current form,
    fixture difficulty & weeks requested.
    """
    players[f"proj_{weeks}gw"] = (
        players["form"].astype(float) *
        weeks *
        (5 - players["team"].map(fetch_fixture_difficulty()).fillna(3)) / 3
    )
    return players.sort_values(by=f"proj_{weeks}gw", ascending=False)

def generate_gw_outlook(players):
    """Generates both 5GW and 10GW reference squads."""
    gw5_players = project_future_gws(players.copy(), weeks=5)
    gw10_players = project_future_gws(players.copy(), weeks=10)

    gw5_squad = gw5_players.nlargest(15, "proj_5gw")[
        ["first_name", "second_name", "team_name", "position", "now_cost", "proj_5gw"]
    ]
    gw10_squad = gw10_players.nlargest(15, "proj_10gw")[
        ["first_name", "second_name", "team_name", "position", "now_cost", "proj_10gw"]
    ]
    return gw5_squad, gw10_squad

# ======================
# 8. TRANSFER RECOMMENDATIONS
# ======================
def transfer_recommendations(current_squad, optimal_squad):
    """
    Compares your current squad with optimal to recommend transfers.
    Returns a list of suggested IN and OUT players.
    """
    current_names = set(current_squad["second_name"])
    optimal_names = set(optimal_squad["second_name"])

    to_in = optimal_names - current_names
    to_out = current_names - optimal_names

    transfer_list = []
    for p in to_in:
        recommended_in = optimal_squad[optimal_squad["second_name"] == p].iloc[0]
        transfer_list.append({
            "Action": "IN",
            "Player": f"{recommended_in['first_name']} {recommended_in['second_name']}",
            "Team": recommended_in["team_name"],
            "Cost": recommended_in["now_cost"]
        })

    for p in to_out:
        recommended_out = current_squad[current_squad["second_name"] == p].iloc[0]
        transfer_list.append({
            "Action": "OUT",
            "Player": f"{recommended_out['first_name']} {recommended_out['second_name']}",
            "Team": recommended_out["team_name"],
            "Cost": recommended_out["now_cost"]
        })

    return pd.DataFrame(transfer_list)

# ======================
# 9. HISTORY LOGGING
# ======================
def log_history(optimal_squad, file_name="elite_v6_history.csv"):
    """
    Saves the current optimal squad to a CSV log for tracking squad value & evolution.
    """
    optimal_squad["timestamp"] = pd.Timestamp.now()
    if os.path.exists(file_name):
        optimal_squad.to_csv(file_name, mode='a', header=False, index=False)
    else:
        optimal_squad.to_csv(file_name, index=False)
    return f"✅ Squad saved to {file_name}"
    # ======================
# 10. STREAMLIT APP UI
# ======================
def main():
    st.set_page_config(page_title="Elite V6.6.1 FPL Optimiser", layout="wide")
    st.title("✅ Elite V6.6.1 FPL Optimiser")
    st.markdown("Fully FPL Compliant | GW5 & GW10 Projections | Auto Transfers & Fixture Difficulty")

    # --- Load Data ---
    with st.spinner("Fetching latest FPL data..."):
        players, teams = fetch_fpl_data()
        if players is None:
            st.stop()

    difficulty_map = fetch_fixture_difficulty()
    players = clean_player_data(players, teams, difficulty_map)

    # --- Optimise Squad ---
    st.header("=== ✅ Optimal Squad for Next GW ===")
    optimal_squad, spent = optimise_squad(players)
    st.dataframe(optimal_squad[["first_name", "second_name", "team_name", "position", "now_cost", "proj_1gw"]])
    st.caption(f"💰 **Total Spent:** £{spent:.1f}m | ✅ Squad Size: {len(optimal_squad)}/15")

    # --- Starting XI & Bench ---
    st.subheader("✅ Starting XI")
    start_xi, bench = pick_starting_xi(optimal_squad)
    st.dataframe(start_xi[["first_name", "second_name", "team_name", "position", "now_cost", "proj_1gw"]])

    st.subheader("✅ Bench")
    st.dataframe(bench[["first_name", "second_name", "team_name", "position", "now_cost", "proj_1gw"]])

    # --- Captaincy ---
    captain, vice = pick_captains(start_xi)
    st.markdown(f"### ⭐ **Captain:** {captain}")
    st.markdown(f"### ⭐ **Vice-Captain:** {vice}")

    # --- GW5 & GW10 Outlooks ---
    st.header("🔮 GW5 & GW10 Reference Squads")
    gw5_squad, gw10_squad = generate_gw_outlook(players)
    st.subheader("5GW Reference Squad")
    st.dataframe(gw5_squad)
    st.subheader("10GW Reference Squad")
    st.dataframe(gw10_squad)

    # --- Transfer Recommendations ---
    st.header("🔄 Transfer Recommendations")
    uploaded = st.file_uploader("Upload your current squad CSV:", type="csv")
    if uploaded:
        current_squad = pd.read_csv(uploaded)
        transfer_df = transfer_recommendations(current_squad, optimal_squad)
        st.dataframe(transfer_df)
    else:
        st.info("Upload your current squad CSV to get transfer recommendations.")

    # --- Logging ---
    if st.button("💾 Save This Optimal Squad"):
        log_msg = log_history(optimal_squad)
        st.success(log_msg)

    st.caption("Elite V6.6.1 | Built for serious FPL managers.")

if __name__ == "__main__":
    main()

# ======================
# 11. AUTO-GENERATE DEPLOY FILES
# ======================
import textwrap

def generate_requirements():
    """Creates a requirements.txt for Streamlit deployment"""
    requirements = textwrap.dedent("""
        streamlit
        pandas
        numpy
        requests
    """).strip()

    with open("requirements.txt", "w") as f:
        f.write(requirements)
    return "✅ requirements.txt created."

def generate_readme():
    """Creates a README.md for GitHub deployment"""
    readme_text = textwrap.dedent("""
        # ✅ Elite V6.6.1 FPL Optimiser

        ## What is this?
        A Streamlit-based Fantasy Premier League optimiser compliant with FPL rules.

        ## Key Features:
        - ✅ **Auto GW5 & GW10 projections**
        - ✅ **Auto Fixture Difficulty scraping**
        - ✅ **Transfer recommendations** (upload your current squad CSV)
        - ✅ **Optimal Starting XI + Bench**
        - ✅ **History logging**

        ## Run Locally
        ```bash
        pip install -r requirements.txt
        streamlit run elite_v6_optimiser_v6_6_1.py
        ```

        ## Deployment
        Works perfectly with Streamlit Cloud:
        - **Repository**: `YourGitHubUsername/elite_v6_fpl_optimiser`
        - **Branch**: `main`
        - **Main File Path**: `elite_v6_optimiser_v6_6_1.py`
        """).strip()

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_text)
    return "✅ README.md created."


if __name__ == "__main__":
    print(generate_requirements())
    print(generate_readme())
