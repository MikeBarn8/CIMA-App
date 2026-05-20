import streamlit as st
import random
import json
import os
import hashlib
from tinydb import TinyDB, Query

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="CIMA App", layout="wide")

# ---------------------------------------------------
# TINYDB SETUP (PERSISTENT)
# ---------------------------------------------------
db = TinyDB("db.json")
Users = Query()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    hashed = hash_password(password)
    db.insert({"username": username, "password": hashed, "scores": []})

def get_user(username):
    result = db.search(Users.username == username)
    return result[0] if result else None

def update_user(username, data):
    db.update(data, Users.username == username)

# ---------------------------------------------------
# SESSION STATE INITIALISATION
# ---------------------------------------------------
defaults = {
    "screen": "module_select",
    "user": None,
    "user_data": None,
    "difficulty": None,
    "questions": [],
    "current_index": 0,
    "score": 0,
    "selected_option": None,
    "show_result": False,
    "answers": [],
    "review": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def rounded_thousand(min_val=1000, max_val=150000):
    return random.randint(min_val // 1000, max_val // 1000) * 1000

def make_options(correct):
    options = {correct}
    while len(options) < 4:
        wrong_raw = correct * random.uniform(0.6, 1.4)
        wrong = (int(wrong_raw) // 1000) * 1000
        if wrong != correct and wrong > 0:
            options.add(wrong)
    options = list(options)
    random.shuffle(options)
    return options

# ---------------------------------------------------
# QUESTION GENERATORS
# ---------------------------------------------------
def generate_straight_line_question():
    cost = rounded_thousand(1000, 150000)
    residual = rounded_thousand(0, cost // 2)
    life = random.randint(3, 8)
    raw_answer = (cost - residual) / life
    answer = (int(raw_answer) // 1000) * 1000

    explanation = (
        "Straight‑line depreciation = (Cost − Residual Value) ÷ Useful Life\n"
        f"= (£{cost:,} − £{residual:,}) ÷ {life}\n"
        f"= £{answer:,} per year (rounded)."
    )

    q = (
        f"A machine costs £{cost:,}, residual value £{residual:,}, "
        f"useful life {life} years. What is the annual straight‑line depreciation?"
    )
    return q, answer, explanation

def generate_reducing_balance_question():
    value = rounded_thousand(1000, 150000)
    rate = random.choice([10, 20, 25])
    raw_answer = value * (rate / 100)
    answer = (int(raw_answer) // 1000) * 1000

    explanation = (
        "Reducing balance depreciation = Book Value × Rate\n"
        f"= £{value:,} × {rate}%\n"
        f"= £{answer:,} (rounded)."
    )

    q = (
        f"An asset has a book value of £{value:,} and is depreciated at {rate}% "
        f"reducing balance. What is the depreciation for Year 1?"
    )
    return q, answer, explanation

def generate_mixed_question():
    q_type = random.choice([1, 2, 3])

    if q_type == 1:
        return generate_straight_line_question()
    if q_type == 2:
        return generate_reducing_balance_question()

    cost = rounded_thousand(1000, 150000)
    units_total = rounded_thousand(1000, 150000)
    units_year = rounded_thousand(1000, units_total)

    raw_answer = (cost / units_total) * units_year
    answer = (int(raw_answer) // 1000) * 1000

    explanation = (
        "Units‑of‑production depreciation = (Cost ÷ Total Units) × Units Produced\n"
        f"= (£{cost:,} ÷ {units_total:,}) × {units_year:,}\n"
        f"= £{answer:,} (rounded)."
    )

    q = (
        f"A machine costing £{cost:,} will produce {units_total:,} units. "
        f"It produces {units_year:,} units this year. What is the depreciation?"
    )
    return q, answer, explanation

# ---------------------------------------------------
# CACHED QUIZ GENERATION
# ---------------------------------------------------
@st.cache_data
def cached_question_set(difficulty: str):
    generator = {
        "Straight Line": generate_straight_line_question,
        "Reducing Balance": generate_reducing_balance_question,
        "Mixed": generate_mixed_question,
    }[difficulty]

    questions = []
    for _ in range(10):
        q, a, explanation = generator()
        options = make_options(a)
        questions.append((q, a, options, explanation))
    return questions

def start_quiz():
    st.session_state.questions = cached_question_set(st.session_state.difficulty)
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.show_result = False
    st.session_state.answers = []
    st.session_state.review = False

# ---------------------------------------------------
# LOGIN / SIGNUP
# ---------------------------------------------------
if st.session_state.user is None:
    st.title("CIMA Practice App – Login")

    tab_login, tab_signup = st.tabs(["Login", "Create Account"])

    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = get_user(username)
            if not user:
                st.error("User does not exist.")
            else:
                if user["password"] == hash_password(password):
                    st.session_state.user = username
                    st.session_state.user_data = user
                    st.session_state.screen = "module_select"
                    st.rerun()
                else:
                    st.error("Incorrect password.")

    with tab_signup:
        new_username = st.text_input("Create Username")
        new_password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Create Account"):
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif new_username.strip() == "":
                st.error("Username cannot be empty.")
            else:
                if get_user(new_username):
                    st.error("Username already exists.")
                else:
                    create_user(new_username, new_password)
                    st.success("Account created! You can now log in.")

    st.stop()

# ---------------------------------------------------
# MODULE SELECT
# ---------------------------------------------------
if st.session_state.screen == "module_select":
    st.title(f"Welcome, {st.session_state.user}")

    if st.button("F1"):
        st.session_state.screen = "f1_home"

    if st.button("Progress Dashboard"):
        st.session_state.screen = "dashboard"

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.user_data = None
        st.session_state.screen = "module_select"

    st.stop()

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
if st.session_state.screen == "dashboard":
    st.title(f"{st.session_state.user}'s Progress Dashboard")

    data = st.session_state.user_data["scores"]

    if not data:
        st.info("No quiz attempts yet.")
    else:
        st.write("### Score History")

        table = []
        percents = []
        for entry in data:
            pct = round((entry["score"] / entry["total"]) * 100)
            percents.append(pct)
            table.append({
                "Module": entry["module"],
                "Topic": entry["topic"],
                "Score": f"{entry['score']} / {entry['total']}",
                "Percent": f"{pct}%"
            })

        st.dataframe(table, hide_index=True)
        st.write("### Performance Over Time")
        st.line_chart(percents)

    if st.button("Back"):
        st.session_state.screen = "module_select"

    st.stop()

# ---------------------------------------------------
# F1 HOME
# ---------------------------------------------------
if st.session_state.screen == "f1_home":
    st.title("F1 – Financial Reporting")

    if st.button("Depreciation"):
        st.session_state.screen = "depreciation_menu"

    if st.button("Back"):
        st.session_state.screen = "module_select"

    st.stop()

# ---------------------------------------------------
# DEPRECIATION MENU
# ---------------------------------------------------
if st.session_state.screen == "depreciation_menu":
    st.title("Depreciation Practice")

    def reset_quiz_state():
        st.session_state.questions = []
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.answers = []
        st.session_state.review = False
        st.session_state.show_result = False

    if st.button("Straight Line Depreciation"):
        st.session_state.difficulty = "Straight Line"
        reset_quiz_state()
        st.session_state.screen = "quiz"

    if st.button("Reducing Balance Depreciation"):
        st.session_state.difficulty = "Reducing Balance"
        reset_quiz_state()
        st.session_state.screen = "quiz"

    if st.button("Mixed"):
        st.session_state.difficulty = "Mixed"
        reset_quiz_state()
        st.session_state.screen = "quiz"

    if st.button("Back"):
        st.session_state.screen = "f1_home"

    st.stop()

# ---------------------------------------------------
# QUIZ
# ---------------------------------------------------
if st.session_state.screen == "quiz":

    if not st.session_state.questions:
        start_quiz()

    # QUIZ COMPLETE
    if st.session_state.current_index >= len(st.session_state.questions):
        st.write("### Quiz Complete!")
        st.write(f"Score: **{st.session_state.score} / {len(st.session_state.questions)}**")

        user = get_user(st.session_state.user)
        user["scores"].append({
            "module": "F1",
            "topic": st.session_state.difficulty,
            "score": st.session_state.score,
            "total": len(st.session_state.questions)
        })
        update_user(st.session_state.user, user)

        if st.button("Review Answers"):
            st.session_state.review = True

        if st.button("Back"):
            st.session_state.screen = "depreciation_menu"
            st.session_state.difficulty = None

        st.stop()

    # REVIEW MODE
    if st.session_state.review:
        st.write("## Review Mode")

        summary_data = []
        correct_count = 0

        for i, (q, selected, correct, explanation) in enumerate(st.session_state.answers, start=1):
            is_correct = selected == correct
            summary_data.append({
                "Q#": i,
                "Your Answer": f"£{selected:,}",
                "Correct Answer": f"£{correct:,}",
                "Result": "Correct" if is_correct else "Incorrect"
            })
            if is_correct:
                correct_count += 1

        st.dataframe(summary_data, hide_index=True)

        total = len(st.session_state.answers)
        percentage = round((correct_count / total) * 100)

        st.write(f"### Score: {correct_count}/{total} ({percentage}%)")

        incorrect_questions = [
            (q, correct, explanation)
            for (q, selected, correct, explanation) in st.session_state.answers
            if selected != correct
        ]

        if incorrect_questions:
            if st.button("Retry Incorrect Only"):
                st.session_state.questions = []
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.answers = []
                st.session_state.review = False

                for q, correct, explanation in incorrect_questions:
                    options = make_options(correct)
                    st.session_state.questions.append((q, correct, options, explanation))

                st.session_state.screen = "quiz"

        if st.button("Back"):
            st.session_state.screen = "depreciation_menu"
            st.session_state.review = False
            st.session_state.difficulty = None

        st.stop()

    # NORMAL QUESTION MODE
    q, correct, options, explanation = st.session_state.questions[st.session_state.current_index]

    st.write(f"### Question {st.session_state.current_index + 1}")
    st.write(q)

    st.session_state.selected_option = st.radio("Choose:", options)

    if st.button("Submit"):
        st.session_state.show_result = True
        st.session_state.answers.append((q, st.session_state.selected_option, correct, explanation))

        if st.session_state.selected_option == correct:
            st.success("Correct!")
            st.session_state.score += 1
        else:
            st.error(f"Incorrect — correct answer: £{correct:,}")

    if st.session_state.show_result:
        if st.button("Next"):
            st.session_state.current_index += 1
            st.session_state.show_result = False

    st.write(f"### Score: {st.session_state.score}")
