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

options = ["01", "02", "03"]
chapter = st.selectbox("Choose a chapter:", options)
go = st.button("Go!")

if go:
    sheet = spread.worksheet("Log"+chapter)
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
