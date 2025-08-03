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
    st.write(top_list)
          
  
