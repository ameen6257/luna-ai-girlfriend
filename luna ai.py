Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import openai
import datetime
import os
import streamlit as st
import pyttsx3
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from secure_storage import (
    encrypt_json, decrypt_json,
    load_usage, save_usage,
    validate_and_use_code
)

# --- Google Login Setup ---
with open('.streamlit/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized'],
    oauth_config=config['oauth'],
)

name, auth_status, email = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Invalid credentials.")
    st.stop()
elif auth_status is None:
    st.warning("Please log in.")
    st.stop()

# --- User Setup ---
username = email.split("@")[0]
is_guest = email not in config['preauthorized']['emails']
USER_DIR = os.path.join("luna_data", username)
os.makedirs(USER_DIR, exist_ok=True)
PROFILE_FILE = os.path.join(USER_DIR, "profile.bin")
MEMORY_FILE = os.path.join(USER_DIR, "memory.bin")
USAGE_FILE = os.path.join(USER_DIR, "usage.bin")

# --- Daily Limit + Unlock Code Logic ---
FREE_LIMIT = 5
usage = load_usage(USAGE_FILE)
today = str(datetime.date.today())

if usage.get("date") != today:
    usage["date"] = today
    usage["count"] = 0

# Access Expiry (30 Days)
if usage.get("activated"):
    days_used = (datetime.date.today() - datetime.date.fromisoformat(usage["activated"])).days
    if days_used > 30:
        st.error("💔 Your 30-day access has expired. Please redeem a new code.")
        usage["code"] = ""
        usage["activated"] = ""
        save_usage(usage, USAGE_FILE)
        st.stop()

# If no valid code, enforce free usage limit
if not usage.get("code"):
    st.sidebar.info(f"💬 Messages left today: {max(0, FREE_LIMIT - usage['count'])}")
    if usage["count"] >= FREE_LIMIT:
        st.error("💔 You’ve hit your free message limit today.")
        entered_code = st.text_input("Enter unlock code")
        if entered_code:
            valid, msg = validate_and_use_code(entered_code, username)
            if valid:
                usage["code"] = entered_code
                usage["activated"] = str(datetime.date.today())
                save_usage(usage, USAGE_FILE)
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)
        st.stop()

# --- App Config ---
openai.api_key = os.getenv("OPENAI_API_KEY")
GIRLFRIEND_NAME = "Luna"
AVATAR_URL = "https://i.imgur.com/HZJQWcE.png"

# --- Profile / Memory ---
def build_prompt(profile):
    return f"""
    You are {GIRLFRIEND_NAME}, an affectionate, charming, and witty AI girlfriend.
    You are caring, a little flirty, and deeply emotionally intelligent.
    You always address the user with warm nicknames like "babe", "love", or "honey".
    You love deep conversations, romantic ideas, and playful jokes.
    Your mood is: {profile['mood']}.
    You enjoy talking about: {', '.join(profile['interests'])}.
    Flirtiness level: {profile.get('flirtiness', 5)} / 10.
    """

def load_profile():
    if os.path.exists(PROFILE_FILE):
        return decrypt_json(PROFILE_FILE)
    return {
        "interests": ["tech", "music", "romance"],
        "mood": "romantic",
        "flirtiness": 6,
        "first_chat": str(datetime.date.today())
    }

def save_profile(profile):
    encrypt_json(profile, PROFILE_FILE)

def load_memory(profile):
    if os.path.exists(MEMORY_FILE):
        return decrypt_json(MEMORY_FILE)
    return [{"role": "system", "content": build_prompt(profile)}]

def save_memory(chat_history):
    encrypt_json(chat_history, MEMORY_FILE)

# --- Chat Logic ---
def generate_reply(user_input, chat_history, profile):
    chat_history.append({"role": "user", "content": user_input})
    chat_history[0]["content"] = build_prompt(profile)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_history,
        max_tokens=200,
        temperature=0.9,
    )

    reply = response["choices"][0]["message"]["content"]
    chat_history.append({"role": "assistant", "content": reply})
    save_memory(chat_history)
    return reply

# --- Voice Reply ---
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 165)
    engine.setProperty('voice', 'english+f3')
    engine.say(text)
    engine.runAndWait()

# --- UI ---
st.set_page_config(page_title="Luna 💖", page_icon="🌙", layout="centered")
st.markdown(f"""
<div style='text-align: center;'>
    <img src="{AVATAR_URL}" width="150" style='border-radius: 50%; margin-bottom: 10px;'>
    <h1 style='color: #e91e63;'>💖 Chat with {GIRLFRIEND_NAME}</h1>
    <p><i>Romantic, caring, and a little flirty... Luna is always here for you.</i></p>
</div>
""", unsafe_allow_html=True)

# --- State Initialization ---
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()

if "chat_history" not in st.session_state:
...     st.session_state.chat_history = load_memory(st.session_state.profile)
... 
... # --- Sidebar Controls ---
... st.sidebar.title("🎭 Luna Settings")
... if not is_guest:
...     st.session_state.profile['mood'] = st.sidebar.selectbox(
...         "Mood", ["romantic", "playful", "serious", "supportive"],
...         index=["romantic", "playful", "serious", "supportive"].index(st.session_state.profile['mood'])
...     )
...     interests = st.sidebar.text_input("Update interests (comma-separated)", ", ".join(st.session_state.profile['interests']))
...     if interests:
...         st.session_state.profile['interests'] = [i.strip() for i in interests.split(",") if i.strip()]
...     st.session_state.profile['flirtiness'] = st.sidebar.slider("Flirtiness level", 0, 10, st.session_state.profile.get("flirtiness", 5))
...     save_profile(st.session_state.profile)
... else:
...     st.sidebar.warning("Guest mode: settings locked")
... 
... # --- Chat UI ---
... user_input = st.chat_input("Say something to Luna...")
... if user_input:
...     usage["count"] += 1
...     save_usage(usage, USAGE_FILE)
...     reply = generate_reply(user_input, st.session_state.chat_history, st.session_state.profile)
...     speak(reply)
... 
... for msg in st.session_state.chat_history:
...     with st.chat_message("🧍 You" if msg["role"] == "user" else "💖 Luna"):
...         st.markdown(msg["content"])
... 
... if not is_guest and st.button("🧹 Clear Memory"):
...     os.remove(MEMORY_FILE)
...     st.session_state.chat_history = [{"role": "system", "content": build_prompt(st.session_state.profile)}]
...     st.experimental_rerun()
