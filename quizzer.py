import streamlit as st
import pandas as pd
import random
import gspread
from datetime import datetime
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

# === LOAD OR CREATE USERLOG ===
try:
    responses_ws = spread.worksheet("UserLog")
except:
    responses_ws = spread.add_worksheet(title="UserLog", rows="1000", cols="10")
    responses_ws.append_row(["Email", "Name", "Chapter", "Score", "Timestamp"])

def login_screen():
    st.subheader("Please log in to play.")
    st.button("Log in with Google", on_click=st.login)

st.title("📝 Keywords Quiz")

if not st.user.is_logged_in:
    login_screen()
else:
    st.subheader(f"Welcome, {st.user.name}!")
    st.write("Type your answers and click Submit to see your score.")
    st.write("Answers are not case-sensitive. However, they are punctuation-sensitive. Please remember to include any dashes as necessary.")

    options = ["01", "02", "03"]
    chapter = st.selectbox("Choose a chapter:", options)
    if st.button("Go!"):
        sheet = spread.worksheet(chapter)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # === STORE SELECTED QUESTIONS IN SESSION STATE ===
        if "questions" not in st.session_state:
            st.session_state.questions = df.sample(n=min(len(df),10), random_state=random.randint(0, 99999)).reset_index(drop=True)

        questions = st.session_state.questions

        # === FORM ===
        with st.form("quiz_form"):
            responses = []
            for i, row in questions.iterrows():
                st.subheader(f"Q{i+1}: {row['Definition']}")
                answer = st.text_input(f"Your answer for Q{i+1}:", key=f"q{i}")
                responses.append(answer)
            submitted = st.form_submit_button("Submit")

        # === FEEDBACK ===
        if submitted:
            correct = 0
            st.markdown("## ✅ Results")
            for i, row in questions.iterrows():
                user_answer = responses[i].strip().lower()
                correct_answer = str(row['Key Word']).strip().lower()
                if user_answer == correct_answer:
                    st.success(f"Q{i+1}: Correct ✅")
                    correct += 1
                else:
                    st.error(f"Q{i+1}: Incorrect ❌ (Correct answer: **{row['Key Word']}**)")

            st.markdown(f"### 🎯 You got **{correct} out of 10** correct.")

            # === LOG RESULT ===
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            responses_ws.append_row([st.user.email, st.user.name, chapter, correct, timestamp])
            st.success("📥 Your attempt has been recorded.")

            if st.button("🔁 Start a New Quiz"):
                del st.session_state.questions
                st.experimental_rerun()
    
    st.button("Log out", on_click=st.logout)
