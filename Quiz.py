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

def login_screen():
    st.subheader("Please log in to play.")
    st.button("Log in with Google", on_click=st.login)

def reset_quiz():
    # clear previous questions and inputs
    st.session_state.questions = None
    st.session_state.quiz_id += 1   # NEW namespace for all widget keys

def all_filled(input_keys):
    return all((st.session_state.get(k, "") or "").strip() != "" for k in input_keys)

def quiz():
    # === LOAD OR CREATE USERLOG ===
    log = "Log"+chapter
    try:
        responses_ws = spread.worksheet(log)
    except:
        responses_ws = spread.add_worksheet(title=log, rows="1000", cols="10")
        qn = [x+1 for x in range(len(df))]
        responses_ws.append_row(["Email", "Name", "Accuracy", "Timestamp"]+qn)

    # === FIND HISTORY OF STUDENT'S ATTEMPTS ===
    logsheet = spread.worksheet(log)
    logdata = logsheet.get_all_records()
    records = pd.DataFrame(logdata)
    history = [0]*len(df)
    attempt_count = 0
    for i, row in records.iterrows():
        if row['Email'] == st.user.email:
            attempt_count += 1
            for x in range(4, len(row)):
                if row.iloc[x] == "NA": history[x-4] += 0
                else: history[x-4] += int(row.iloc[x].strip().lower() == df['Key Word'][x-4].strip().lower())
        
    if attempt_count > 0:
        history = list(history)
        for i in range(len(history)):
            mistakes = (attempt_count - history[i])/attempt_count
            history[i] = mistakes + 0.1
    else: history = list([1/len(df)] * len(df))
                
    # === STORE SELECTED QUESTIONS IN SESSION STATE ===
    if "questions" not in st.session_state or st.session_state.questions is None:
        st.session_state.questions = df.sample(n=min(len(df),10), weights=history, random_state=random.randint(0, 99999)).reset_index(drop=True)

    quiz_id = st.session_state.quiz_id
    
    questions = st.session_state.questions
    N = len(questions)
    # Track keys for THIS quiz only
    input_keys = [f"ans_{i}_{quiz_id}" for i in range(N)]

    # One-time guard to stop repeated submits/logging for this quiz
    if "graded_quiz_ids" not in st.session_state:
        st.session_state.graded_quiz_ids = set()

    # === FORM ===
    with st.form(f"quiz_form_{st.session_state.quiz_id}"):
        responses = []
        for i, row in questions.iterrows():
            st.subheader(f"Q{i+1}: {row['Definition']}")
            answer = st.text_input(f"Your answer for Q{i+1}:", key=f"ans_{i}_{st.session_state.quiz_id}", autocomplete="off")
            responses.append(answer)

        # Dynamically disable until all filled, and also after grading once
        already_graded = quiz_id in st.session_state.graded_quiz_ids
        submit_disabled = (not all_filled(input_keys)) or already_graded
        submitted = st.form_submit_button("Submit", disabled=submit_disabled)

    
    # Hint for users if not all filled
    if not all_filled(input_keys):
        st.info("Please answer all questions to enable Submit.")


    # === FEEDBACK ===
    # Grade exactly once
    if submitted and (quiz_id not in st.session_state.graded_quiz_ids):
        correct = 0
        ans_list = ["NA"] * len(df)
        st.markdown("## ✅ Results")
        for i, row in questions.iterrows():
            user_answer = responses[i].strip().lower()
            correct_answer = str(row['Key Word']).strip().lower()
            ans_list[int(row['Question'])-1] = user_answer
            if user_answer == correct_answer:
                st.success(f"Q{i+1}: Correct ✅")
                correct += 1
            else:
                st.error(f"Q{i+1}: Incorrect ❌ (Correct answer: **{row['Key Word']}**)")

        st.markdown(f"### 🎯 You got **{correct} out of {len(questions)}** correct.")

        # === LOG RESULT ===
        utc_now = datetime.now(pytz.utc)
        local_tz = pytz.timezone('ETC/GMT-8')
        local_time = utc_now.astimezone(local_tz)
        timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
        responses_ws.append_row([st.user.email, st.user.name, correct/len(questions)*100, timestamp]+ans_list)
        st.success("📥 Your attempt has been recorded. Refresh the page to get a new quiz.")

        if st.button("🔁 Start a New Quiz", on_click=reset_quiz):
            if "questions" in st.session_state:
                del st.session_state.questions
            for k in list(st.session_state.input_keys):
                st.session_state.pop(k, None)
            st.session_state.input_keys.clear()
            st.rerun()

st.title("📝 Computing Keywords Quizzer")

if not st.user.is_logged_in:
    login_screen()
else:
    st.subheader(f"Welcome, {st.user.name}!")
    st.write("**How to Play**")
    st.write("Type your answers and click Submit to see your score.")
    st.write("Answers are not case-sensitive. However, they are punctuation-sensitive. Please remember to include any dashes or brackets as necessary.")
    st.write("The questions are taken randomly from the set of keyword definitions for the chapter/chapters you have selected to play.")
    st.write("As you keep playing the same chapter/chapters, the webapp learns your strengths and weaknesses. You will be more likely to see questions you have not tried before, or questions you have gotten wrong before.")
    st.write("Happy playing/learning!")    
    
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.questions = None  

    if "quiz_id" not in st.session_state:
        st.session_state.quiz_id = 0
        
    options = ["01 Computer Architecture", "02-03 Data Representation; Logic Gates", "04 Programming", "05-08 Input Validation; Testing and Debugging; Algorithm Design; Software Engineering", "09 Spreadsheets", "10 Networking", "11 Security and Privacy", "12-14 Intellectual Property; Impact of Computing; Emerging Technologies"]
    chapter_sel = st.selectbox("Choose a chapter:", options)
    chapter = chapter_sel[:chapter_sel.find(" ")]
    go = st.button("Go!", on_click=reset_quiz)

    if go: 
        st.session_state.quiz_started = True
        st.session_state.questions = None  
        if "input_keys" in st.session_state:
            for key in list(st.session_state.input_keys):
                st.session_state.pop(key, None)
            st.session_state.input_keys.clear()

    if st.session_state.quiz_started:
        sheet = spread.worksheet(chapter)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        quiz()
            
    
    st.button("Log out", on_click=st.logout)
