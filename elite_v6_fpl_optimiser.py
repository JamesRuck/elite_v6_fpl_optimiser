import pandas as pd
import requests
import streamlit as st
import datetime

# === 1. Pull FPL API Data ===
FPL_API = "https://fantasy.premierleague.com/api/bootstrap-static/"
response = requests.get(FPL_API).json()

players_df = pd.DataFrame(response['elements'])
teams_df = pd.DataFrame(response['teams'])

# Map team names & positions
team_map = dict(zip(teams_df['id'], teams_df['name']))
positions = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
players_df['team_name'] = players_df['team'].map(team_map)
players_df['position'] = players_df['element_type'].map(positions)
players_df['now_cost'] = players_df['now_cost'] / 10

# Filter out low-minute players
players_df = players_df[players_df['minutes'] >= 180]

# === 2. Custom Transfer Score ===
players_df['transfer_score'] = (
    players_df['form'].astype(float) +
    players_df['ict_index'].astype(float) +
    (players_df['total_points'] / 10)
)

# === 3. Optimal Squad (basic top 15 by transfer score) ===
optimal_squad = players_df.sort_values(by='transfer_score', ascending=False).head(15)

# Split into starting XI (top 11) and bench (rest 4)
starting_xi = optimal_squad.head(11)
bench = optimal_squad.tail(4)

# === 4. Save historical tracking ===
week = datetime.datetime.today().strftime('%Y-%m-%d')
hist_file = "elite_v6_history.csv"
optimal_squad['date'] = week

if os.path.exists(hist_file):
    hist_df = pd.read_csv(hist_file)
    hist_df = pd.concat([hist_df, optimal_squad[['web_name','team_name','position','transfer_score','now_cost','date']]])
    hist_df.to_csv(hist_file, index=False)
else:
    optimal_squad[['web_name','team_name','position','transfer_score','now_cost','date']].to_csv(hist_file, index=False)

# === 5. Streamlit Dashboard ===
st.title("Elite v6 FPL Optimiser")

st.subheader("✅ Validation Summary (Next GW)")
st.write(f"Squad Size: {len(optimal_squad)} | Budget: £{optimal_squad['now_cost'].sum():.1f}m")

st.subheader("✅ Starting XI")
st.dataframe(starting_xi[['web_name','team_name','position','now_cost','transfer_score']])

st.subheader("✅ Bench")
st.dataframe(bench[['web_name','team_name','position','now_cost','transfer_score']])

# Simple captaincy pick: highest transfer score
captain = starting_xi.iloc[0]['web_name']
vice_captain = starting_xi.iloc[1]['web_name']
st.success(f"⭐ Captain: {captain} | Vice: {vice_captain}")

st.subheader("✅ Full Optimal Squad")
st.dataframe(optimal_squad[['web_name','team_name','position','now_cost','transfer_score']])

st.success(f"✅ Squad saved to {hist_file}")
