# ai_c_tutor.py

import os
import json
import streamlit as st
import requests
from dotenv import load_dotenv

# -------------------------------
# 🌐 Setup: API + Model Selection
# -------------------------------
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "deepseek/deepseek-chat-v3-0324:free"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost"
}
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ----------------------------
# 📚 Roadmap and C Domains
# ----------------------------
CORE_C_TOPICS = [
    "C Setup: GCC, IDEs (VS Code, Code::Blocks), CLI Compilation",
    "Data Types and Variables",
    "Operators (Arithmetic, Logical, Bitwise)",
    "Control Flow (if, else, switch)",
    "Loops (for, while, do-while)",
    "Functions and Recursion",
    "Arrays and Strings",
    "Pointers and Dynamic Memory",
    "Structures and Unions",
    "File Handling",
    "Header Files and Modular C",
    "Makefile and Compilation Units",
    "Preprocessor Directives",
    "Command Line Arguments",
    "Debugging with GDB and Valgrind"
]

C_DOMAINS = {
    "None": [],
    "Systems Programming": [
        "Processes and Forking",
        "Signals and Pipes",
        "Sockets (TCP/UDP Basics)",
        "Multithreading with pthreads",
        "Daemon Processes and IPC"
    ],
    "Embedded Systems": [
        "Bitwise Operations for Port Manipulation",
        "Microcontroller Programming (e.g., Arduino)",
        "Interrupt Handling",
        "Timer and Delay Logic",
        "Serial Communication (UART)"
    ],
    "Operating Systems": [
        "Process Scheduling Concepts",
        "Virtual Memory and Paging",
        "Writing a Shell",
        "Lexers and Parsers (Flex & Bison)",
        "Toy Compiler and File System Simulator"
    ],
    "Reverse Engineering": [
        "Buffer Overflow and Stack Smashing",
        "Format String Vulnerabilities",
        "Binary Exploitation with GDB",
        "Shellcode Basics"
    ],
    "Game Development": [
        "Graphics with SDL2",
        "Game Loops and Timers",
        "Collision Detection",
        "2D Game Physics",
        "Sound Integration (SDL_Mixer)"
    ],
    "DSA in C": [
        "Linked Lists and Trees",
        "Stacks and Queues",
        "Graphs (DFS, BFS)",
        "Sorting and Searching Algorithms",
        "Hashing and Map Implementation"
    ]
}

# ------------------------
# 📀 Load/Save Progress
# ------------------------
USER_DIR = "user_data_c"
if not os.path.exists(USER_DIR):
    os.makedirs(USER_DIR)

def get_user_file(username):
    return os.path.join(USER_DIR, f"{username}_progress.json")

def load_progress(topics, username):
    path = get_user_file(username)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return {topic: data.get(topic, False) for topic in topics}
    return {topic: False for topic in topics}

def save_progress(progress, username):
    with open(get_user_file(username), "w") as f:
        json.dump(progress, f)

def reset_progress(topics, username):
    save_progress({topic: False for topic in topics}, username)

# ---------------------------
# 💬 Prompt: Tutor Explanation
# ---------------------------
def get_explanation(concept, quiz=False, example=False):
    instruction = "Explain the C programming concept clearly with code examples."
    if quiz:
        instruction = "Create a multiple choice quiz (3-4 options) with correct answer for:"
    elif example:
        instruction = "Give a real-world example with code and explanation for:"

    messages = [
        {"role": "system", "content": "You are a helpful C programming tutor."},
        {"role": "user", "content": f"{instruction} {concept}"}
    ]
    payload = {"model": MODEL, "messages": messages}
    res = requests.post(API_URL, headers=HEADERS, json=payload)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    return f"❌ Error {res.status_code}: {res.text}"

# ---------------------------
# 🎛️ Streamlit App UI
# ---------------------------
st.set_page_config(page_title="C Programming Tutor", page_icon="🌱")
st.title("🌱 AI C Programming Tutor")

# Login UI
if "username" not in st.session_state:
    with st.form("login_form"):
        st.subheader("🔐 Login")
        username = st.text_input("Enter your name")
        submitted = st.form_submit_button("Login")
        if submitted and username.strip():
            st.session_state.username = username.strip()
            st.rerun()
    st.stop()

username = st.session_state.username
st.success(f"Welcome, {username}!")
domain = st.sidebar.selectbox("👨‍💼 Select C Domain (Optional)", list(C_DOMAINS.keys()), index=0)

# ✅ MODIFIED HERE: Only show domain topics if a domain is selected
if domain == "None":
    ROADMAP = CORE_C_TOPICS
else:
    ROADMAP = C_DOMAINS[domain]  # no more core concepts included

progress = load_progress(ROADMAP, username)

# Progress Bar
completed = sum(progress.values())
total = len(ROADMAP)
percent = int((completed / total) * 100)
st.sidebar.metric("📊 Progress", f"{percent}%")
st.sidebar.progress(percent / 100)

# Display topics
st.sidebar.header("🌱 Your C Learning Roadmap")
for topic in ROADMAP:
    status = "✅" if progress[topic] else "⬜"
    st.sidebar.markdown(f"{status} {topic}")

if st.sidebar.button("🔄 Reset Progress"):
    reset_progress(ROADMAP, username)
    st.rerun()

# Concept selector
available_concepts = [c for c in ROADMAP if not progress[c]]
if available_concepts:
    selected = st.selectbox("Choose a C concept to learn:", available_concepts, index=0)
    if st.button("📚 Teach Me!"):
        st.session_state.selected_concept = selected
        st.session_state.explanation = get_explanation(selected)
        st.session_state.quiz = None
        st.session_state.example = None

if "selected_concept" in st.session_state:
    concept = st.session_state.selected_concept
    st.subheader(f"🌱 Concept: {concept}")

    st.markdown(st.session_state.explanation)

    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 2])

    if col1.button("🔁 Regenerate"):
        st.session_state.explanation = get_explanation(concept)
        st.rerun()

    if col2.button("✅ Mark Done"):
        progress[concept] = True
        save_progress(progress, username)
        st.session_state.pop("selected_concept")
        st.rerun()

    if col3.button("➡️ Next"):
        idx = available_concepts.index(concept) + 1 if concept in available_concepts else 0
        if idx < len(available_concepts):
            st.session_state.selected_concept = available_concepts[idx]
            st.session_state.explanation = get_explanation(available_concepts[idx])
            st.rerun()

    if col4.button("📄 Export Log"):
        with open("learning_log_c.txt", "a") as f:
            f.write(f"\n\n---\n{concept}\n{st.session_state.explanation}\n")
        st.success("Exported explanation to learning_log_c.txt")

    # Examples & Quizzes
    if st.button("💡 Show Example"):
        st.session_state.example = get_explanation(concept, example=True)
    if st.session_state.get("example"):
        st.markdown("**💡 Example:**")
        st.markdown(st.session_state.example)

    if st.button("🧪 Give Me a Quiz"):
        st.session_state.quiz = get_explanation(concept, quiz=True)
    if st.session_state.get("quiz"):
        st.markdown("**🧪 Quiz:**")
        st.markdown(st.session_state.quiz)

else:
    st.info("You're done with all current topics! Try a different C domain or reset your progress.")
