import os
import random
import pandas as pd
import streamlit as st

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "..", "data", "filename.csv")
    file_path = os.path.abspath(file_path)

    df = pd.read_csv(file_path)

    # Keep original data untouched
    df = df.reset_index(drop=True)

    # Create valid subset for quiz usage only
    valid_df = df[
        df["word"].notna() &
        df["meaning"].notna() &
        (df["word"].astype(str).str.strip() != "") &
        (df["meaning"].astype(str).str.strip() != "")
    ].reset_index(drop=True)

    return df, valid_df


df, valid_df = load_data()

# Dictionary only from valid data
words = dict(zip(valid_df["word"], valid_df["meaning"]))

# ---------------------------
# Session State Initialization
# ---------------------------
defaults = {
    "page": "home",
    "score": 0,
    "unused_words": [],
    "question_history": [],
    "current_index": 0,
    "user_answers": {},
    "mistakes": {},  # {word: wrong_count}
    "current_set_total": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------
# Start Practice
# ---------------------------
def start_practice(word_list):
    clean_words = [w for w in word_list if w in words]

    random.shuffle(clean_words)

    st.session_state.unused_words = clean_words
    st.session_state.question_history = []
    st.session_state.current_index = 0
    st.session_state.user_answers = {}
    st.session_state.score = 0
    st.session_state.current_set_total = len(clean_words)

    generate_new_question()


# ---------------------------
# Generate New Question
# ---------------------------
def generate_new_question():

    if len(st.session_state.unused_words) == 0:
        st.success("🎉 You completed this set!")
        return

    word = st.session_state.unused_words.pop()
    correct_meaning = words[word]

    wrong_meanings = random.sample(
        [m for w, m in words.items() if w != word],
        min(3, len(words) - 1)
    )

    options = wrong_meanings + [correct_meaning]
    random.shuffle(options)

    question_data = {
        "word": word,
        "correct": correct_meaning,
        "options": options
    }

    st.session_state.question_history.append(question_data)
    st.session_state.current_index = len(st.session_state.question_history) - 1


# ---------------------------
# Homepage
# ---------------------------
if st.session_state.page == "home":
    st.title("📘 TOEFL / GRE Vocab Trainer")

    if st.button("📝 Practice"):
        st.session_state.page = "practice"
        start_practice(list(words.keys()))
        st.rerun()

    if st.button("❌ Mistakes"):
        st.session_state.page = "mistakes"
        st.rerun()


# ---------------------------
# Practice Page
# ---------------------------
elif st.session_state.page == "practice":

    st.title("📝 Practice Mode")

    if len(st.session_state.question_history) == 0:
        st.warning("No words available.")
        st.stop()

    q = st.session_state.question_history[st.session_state.current_index]

    st.write(
        f"### Question {st.session_state.current_index + 1} "
        f"of {st.session_state.current_set_total}"
    )

    st.markdown(f"## **{q['word']}**")

    selected_option = st.radio(
        "Choose the correct meaning:",
        q["options"],
        key=f"radio_{st.session_state.current_index}"
    )

    col1, col2, col3 = st.columns(3)

    # Submit
    with col1:
        if st.button("Submit"):
            if selected_option == q["correct"]:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {q['correct']}")

                # Track mistakes
                word = q["word"]
                if word not in st.session_state.mistakes:
                    st.session_state.mistakes[word] = 1
                else:
                    st.session_state.mistakes[word] += 1

    # Previous
    with col2:
        if st.button("⬅ Previous"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.rerun()

    # Next
    with col3:
        if st.button("Next ➡"):
            if st.session_state.current_index < len(st.session_state.question_history) - 1:
                st.session_state.current_index += 1
            else:
                generate_new_question()
            st.rerun()

    st.write(f"### 🏆 Score: {st.session_state.score}")

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()


# ---------------------------
# Mistakes Page
# ---------------------------
elif st.session_state.page == "mistakes":

    st.title("❌ Mistake Review")

    if len(st.session_state.mistakes) == 0:
        st.write("No mistakes yet 🎉")
    else:
        for word, count in st.session_state.mistakes.items():
            st.write(f"**{word}** — Wrong {count} times")

        if st.button("Practice Mistakes"):
            mistake_words = list(st.session_state.mistakes.keys())
            st.session_state.page = "practice"
            start_practice(mistake_words)
            st.rerun()

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()