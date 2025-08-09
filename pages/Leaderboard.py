import streamlit as st
import pandas as pd
import random
import gspread
from datetime import datetime
import pytz
from google.oauth2 import service_account

# === CONFIGURATION ===
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JrlwY69DVRnOjFZvaE0CX_PLZNelw3_qEBu0WhgcHPQ/edit#gid=0"

# === GOOGLE SHEETS AUTH ===
def load_spread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", 'https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes = scope)
    client = gspread.authorize(creds)
    spread = client.open_by_url(SHEET_URL)
    return spread

spread = load_spread()

st.title("👑 Leaderboards")

options = ["01 Computer Architecture", "02 Data Representation", "03 Logic Gates", "04 Programming", "05 Input Validation", "06 Testing and Debugging", "07 Algorithm Design", "08 Software Engineering", "09 Spreadsheets", "10 Networking", "11 Security and Privacy", "12 Intellectual Property", "13 Impact of Computing", "14 Emerging Technology"]
chapter = st.selectbox("Choose a chapter:", options)[:2]
go = st.button("Go!")

if go:
# === LOAD OR CREATE USERLOG ===
    log = "Log"+chapter
    try:
        sheet = spread.worksheet(log)
    except:
        sheet = spread.add_worksheet(title=log, rows="1000", cols="10")
        source = spread.worksheet(chapter)
        source_data = source.get_all_records()
        df = pd.DataFrame(source_data)
        qn = [x+1 for x in range(len(df))]
        sheet.append_row(["Email", "Name", "Accuracy", "Timestamp"]+qn)
        
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    top = {}
    for i, row in df.iterrows():
        if row["Name"] in top.keys() and float(row["Accuracy"]) > top[row["Name"]]:
            top[row["Name"]] = float(row["Accuracy"])
        elif not row["Name"] in top.keys():
            top[row["Name"]] = float(row["Accuracy"])
    
    top_list = [(top[key], key) for key in top.keys()]
    top_sorted = sorted(top_list, reverse=True)
    top_ranked = [(str(i+1), top_sorted[i][1],str(round(top_sorted[i][0],2))) for i in range(len(top_sorted))] 
        
     # style
    th_props = [
    ('text-align', 'left'),
    ('font-weight', 'bold'),
    ('color', '#6d6d6d'),
    ('background-color', '#c8bbdc')
    ]

    td_props = [
    ('text-align', 'center')
    ]
                                                 
    styles = [
    dict(selector="th", props=th_props),
    dict(selector="td", props=td_props)
    ]

    # table
    df = pd.DataFrame(top_ranked[:5], columns = ["Rank","Name","Accuracy (%)"])
    df = df.style.set_properties().set_table_styles(styles)
    
    # CSS to inject contained in a string
    hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
    
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    
    # Display a static table
    st.table(df)
