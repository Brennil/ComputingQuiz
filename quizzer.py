import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2 import service_account

# === CONFIGURATION ===
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JrlwY69DVRnOjFZvaE0CX_PLZNelw3_qEBu0WhgcHPQ/edit#gid=0"

# === GOOGLE SHEETS AUTH ===
@st.cache_resource
def load_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes = scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_sheet()

# === RANDOMLY SELECT 10 QUESTIONS ===
questions = df.sample(n=10, random_state=random.randint(0, 10000)).reset_index(drop=True)

st.title("📝 Fill in the Blank Quiz")
st.write("Type your answers and click Submit to see your score.")

# === FORM ===
with st.form("quiz_form"):
    responses = []
    for i, row in questions.iterrows():
        st.subheader(f"Q{i+1}: {row['Question']}")
        answer = st.text_input(f"Your answer for Q{i+1}:", key=f"q{i}")
        responses.append(answer)
    submitted = st.form_submit_button("Submit")

# === FEEDBACK ===
if submitted:
    correct = 0
    st.markdown("## ✅ Results")
    for i, row in questions.iterrows():
        user_answer = responses[i].strip().lower()
        correct_answer = str(row['Answer']).strip().lower()
        if user_answer == correct_answer:
            st.success(f"Q{i+1}: Correct ✅")
            correct += 1
        else:
            st.error(f"Q{i+1}: Incorrect ❌ (Correct answer: **{row['Answer']}**)")

    st.markdown(f"### 🎯 You got **{correct} out of 10** correct.")
