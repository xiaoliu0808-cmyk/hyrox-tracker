import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL_STRENGTH = 50
GOAL_CARDIO = 50
TEAM_MEMBERS = ["王总", "朱弟", "二条", "小牛"] 

# --- PAGE SETUP ---
st.set_page_config(page_title="HYROX GOGOGO", page_icon="💪", layout="wide")
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

st.write("") 

# --- INPUT FORM ---
# This is the ONLY place where st.form("log_form") should appear
with st.container(border=True):
    st.markdown("### 📝 **RECORD WORKOUT**")
    
    with st.expander("👇 **CLICK HERE TO OPEN FORM**", expanded=False):
        with st.form("log_form", clear_on_submit=True):
            name_input = st.selectbox("Who are you?", TEAM_MEMBERS, index=None, placeholder="Select your name...")
            date_input = st.date_input("Date", date.today())
            type_input = st.radio("Workout Type", ["Strength", "Cardio"], horizontal=True)
            
            submitted = st.form_submit_button("✅ Record Workout", use_container_width=True)

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

# --- LEADERBOARD (TRANSPOSED VIEW) ---
# 1. Changed Header Icon to Military Medal
st.header("🎖️ Leaderboard")

# 2. Added Legend
st.markdown("""
<small>
🥇 : <b>Strength Leader</b> <br>
🏆 : <b>Cardio Leader</b> 
</small>
""", unsafe_allow_html=True)

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

    # Calculations
    stats['Strength_Pct'] = stats['Strength'] / GOAL_STRENGTH
    stats['Cardio_Pct'] = stats['Cardio'] / GOAL_CARDIO
    stats['Completion_Score'] = (stats['Strength_Pct'] + stats['Cardio_Pct']) / 2
    
    # Identify Leaders
    max_strength = stats['Strength'].max()
    max_cardio = stats['Cardio'].max()

    # Sort
    stats = stats.sort_values('Completion_Score', ascending=False)

    # Balance Helper
    def get_balance_text(row):
        total = row['Strength'] + row['Cardio']
        if total == 0: return 1.0, "Start!"
        ratio = row['Strength'] / total
        balance_val = 1 - (abs(ratio - 0.5) * 2)
        
        advice = ""
        if balance_val >= 0.8: advice = "✅ Good Mix"
        elif row['Strength'] > row['Cardio']: advice = "⚠️ Need Cardio"
        else: advice = "⚠️ Need Strength"
        
        return balance_val, advice

    # Build Table Data
    transposed_data = {}
    
    for name, row in stats.iterrows():
        display_name = name
        
        # Apply Logic: Gold Medal for Strength, Trophy for Cardio
        if row['Strength'] == max_strength and max_strength > 0:
            display_name = "🥇 " + display_name
            
        if row['Cardio'] == max_cardio and max_cardio > 0:
            display_name = "🏆 " + display_name

        bal_score, bal_advice = get_balance_text(row)
        
        transposed_data[display_name] = [
            f"{int(row['Strength'])} / {GOAL_STRENGTH}",       
            f"{int(row['Cardio'])} / {GOAL_CARDIO}",           
            f"{row['Completion_Score']*100:.1f}%",             
            f"{bal_score*100:.0f}% ({bal_advice})"             
        ]

    display_df = pd.DataFrame(transposed_data, index=[
        "Strength Goal", 
        "Cardio Goal", 
        "Completion Rate", 
        "Balance Advice"
    ])

    st.dataframe(display_df, use_container_width=True)

else:
    st.info("No workouts logged yet.")

# --- RECENT ACTIVITY ---
st.header("Recent Activity - 🏁 Nov Target ")
if not df.empty:
    df['Name'] = pd.Categorical(df['Name'], categories=TEAM_MEMBERS, ordered=True)
    sorted_df = df.sort_values(by=['Name', 'Date'], ascending=[True, False])
    
    st.dataframe(
        sorted_df, 
        use_container_width=True,
        hide_index=True
    )





