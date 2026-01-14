import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL_STRENGTH = 50
GOAL_CARDIO = 50
TEAM_MEMBERS = ["王总", "朱弟", "二条", "小牛"] 

# --- PAGE SETUP ---
st.set_page_config(page_title="HYROX GOGOGO", page_icon="💪")
st.title("🏋️‍♂️ HYROX GOGOGO Team Tracker")

# --- CONNECT TO GOOGLE SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # ttl=0 ensures we get fresh data every time (no caching)
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2], ttl=0)
        if df.empty:
             return pd.DataFrame(columns=["Date", "Name", "Type"])
        return df
    except Exception:
        return pd.DataFrame(columns=["Date", "Name", "Type"])

df = load_data()

# --- INPUT FORM (MOVED TO MAIN PAGE) ---
# We use an expander so it doesn't take up space when not in use.
# It starts closed (expanded=False). When you open it, it stays open 
# until you hit "Record", which triggers a rerun and closes it again.
with st.expander("➕ Log a Workout (Click to Open)", expanded=False):
    with st.form("log_form", clear_on_submit=True):
        name_input = st.selectbox("Who are you?", TEAM_MEMBERS)
        date_input = st.date_input("Date", date.today())
        type_input = st.radio("Workout Type", ["Strength", "Cardio"], horizontal=True)
        submitted = st.form_submit_button("Record Workout", use_container_width=True)

        if submitted:
            new_entry = pd.DataFrame([[str(date_input), name_input, type_input]], 
                                     columns=["Date", "Name", "Type"])
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success(f"Jiayou {name_input}! Saved.")
            st.rerun()

# --- LEADERBOARD ---
st.header("🏆 Leaderboard")

if not df.empty:
    df = df.dropna(subset=['Name', 'Type'])
    current_team_df = df[df['Name'].isin(TEAM_MEMBERS)]

    if not current_team_df.empty:
        stats = current_team_df.groupby(['Name', 'Type']).size().unstack(fill_value=0)
    else:
        stats = pd.DataFrame()

    for member in TEAM_MEMBERS:
        if member not in stats.index: stats.loc[member] = 0
    
    if 'Strength' not in stats.columns: stats['Strength'] = 0
    if 'Cardio' not in stats.columns: stats['Cardio'] = 0

    stats['Total Completed'] = stats['Strength'] + stats['Cardio']
    stats = stats.sort_values('Total Completed', ascending=False)

    for name, row in stats.iterrows():
        with st.container():
            st.subheader(f"{name}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Strength", f"{int(row['Strength'])}/{GOAL_STRENGTH}")
                st.progress(min(row['Strength'] / GOAL_STRENGTH, 1.0))
            with col2:
                st.metric("Cardio", f"{int(row['Cardio'])}/{GOAL_CARDIO}")
                st.progress(min(row['Cardio'] / GOAL_CARDIO, 1.0))
            with col3:
                st.metric("Total", f"{int(row['Total Completed'])}")
            st.divider()
else:
    st.info("No workouts logged yet.")

# --- RECENT ACTIVITY ---
st.header("📅 Recent Activity")
if not df.empty:
    st.dataframe(df.sort_values("Date", ascending=False).head(10), use_container_width=True)
