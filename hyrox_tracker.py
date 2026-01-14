import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL_STRENGTH = 50
GOAL_CARDIO = 50
TEAM_MEMBERS = ["Me", "Friend 1", "Friend 2", "Friend 3"] 

# --- PAGE SETUP ---
st.set_page_config(page_title="HYROX Team Tracker", page_icon="💪")
st.title("🏋️‍♂️ HYROX November Team Tracker")

# --- CONNECT TO GOOGLE SHEET ---
# This creates a connection object. We use a specific TTL (time to live) to keep cache fresh.
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Read data from the Google Sheet
    try:
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2], ttl=5)
        # Ensure correct column names if sheet is empty
        if df.empty:
             return pd.DataFrame(columns=["Date", "Name", "Type"])
        return df
    except Exception:
        return pd.DataFrame(columns=["Date", "Name", "Type"])

df = load_data()

# --- SIDEBAR: LOG WORKOUT ---
st.sidebar.header("Log a Workout")
with st.sidebar.form("log_form", clear_on_submit=True):
    name_input = st.selectbox("Who are you?", TEAM_MEMBERS)
    date_input = st.date_input("Date", date.today())
    type_input = st.radio("Workout Type", ["Strength", "Cardio"])
    submitted = st.form_submit_button("Record Workout")

    if submitted:
        # Create new row
        new_entry = pd.DataFrame([[str(date_input), name_input, type_input]], 
                                 columns=["Date", "Name", "Type"])
        
        # Combine old and new data
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        
        # Update Google Sheet
        conn.update(worksheet="Sheet1", data=updated_df)
        
        st.sidebar.success("Saved to Google Sheet!")
        st.rerun() # Refresh to show new data

# --- MAIN DASHBOARD (Same as before) ---
st.header("🏆 Leaderboard")

if not df.empty:
    # Clean data (ensure no empty rows affect stats)
    df = df.dropna(subset=['Name', 'Type'])
    
    stats = df.groupby(['Name', 'Type']).size().unstack(fill_value=0)
    for member in TEAM_MEMBERS:
        if member not in stats.index: stats.loc[member] = 0
    if 'Strength' not in stats.columns: stats['Strength'] = 0
    if 'Cardio' not in stats.columns: stats['Cardio'] = 0

    stats['Strength Left'] = GOAL_STRENGTH - stats['Strength']
    stats['Cardio Left'] = GOAL_CARDIO - stats['Cardio']
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

st.header("📅 Recent Activity")
if not df.empty:
    st.dataframe(df.sort_values("Date", ascending=False).head(10), use_container_width=True)