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

# --- SOUL SEARCHING REMINDER ---
st.markdown("""
> **朋友，log之前请灵魂拷问：**
> * **今日算不算一次cardio**——费力了没？还是休闲娱乐动一动？Cardio到成为一名自己满意的hyrox选手、实现本年度运动目标的量了没？
> * **今日算不算一次strength**——进步了没？练到了正确的地方没？为完成hyrox的两项任务努力了没？
""")

# --- CONNECT TO GOOGLE SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2], ttl=0)
        if df.empty:
             return pd.DataFrame(columns=["Date", "Name", "Type"])
        return df
    except Exception:
        return pd.DataFrame(columns=["Date", "Name", "Type"])

df = load_data()

st.write("") # Add a little breathing room

# --- INPUT FORM (High Visibility Version) ---
# We use a container with a border to create a "Box" effect
with st.container(border=True):
    # Add a loud header inside the box
    st.markdown("### 📝 **WORKOUT LOG**")
    
    # Make the expander label BOLD and clear
    with st.expander("👇 **CLICK HERE TO OPEN FORM**", expanded=False):
        with st.form("log_form", clear_on_submit=True):
            # Start empty so users must choose
            name_input = st.selectbox("Who are you?", TEAM_MEMBERS, index=None, placeholder="Select your name...")
            date_input = st.date_input("Date", date.today())
            type_input = st.radio("Workout Type", ["Strength", "Cardio"], horizontal=True)
            
            # Make the button span the full width
            submitted = st.form_submit_button("✅ Save Entry", use_container_width=True)

            if submitted:
                if not name_input:
                    st.error("⚠️ Please select your name first!")
                else:
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
st.header("Recent Activity - Till Nov🏁 ")
if not df.empty:
    st.dataframe(
        df.sort_values("Date", ascending=False).head(10), 
        use_container_width=True,
        hide_index=True
    )

