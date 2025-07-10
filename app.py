import streamlit as st
import openai
import os
import re
import base64
import json
from deep_translator import GoogleTranslator

# Load Medsafe PDF links
try:
    with open("medsafe_source_links_cleaned.json", "r") as f:
        medsafe_links = json.load(f)
except Exception as e:
    medsafe_links = {}
    st.warning(f"Could not load Medsafe links: {e}")

# Page config
st.set_page_config(page_title="Pill-AI 2.0", page_icon="💊", layout="centered")

# Custom CSS (Orange + Teal theme)
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari&family=Noto+Sans+SC&display=swap" rel="stylesheet">
    <style>
    body {
        background: linear-gradient(to bottom right, #f4f6f9, #e0f7fa);
        font-family: 'Segoe UI', sans-serif;
    }

    html[lang='zh'] body { font-family: 'Noto Sans SC', sans-serif !important; }

    .stTextInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-size: 1.1em !important;
        padding: 10px 14px !important;
        border: 2px solid #009688 !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus {
        border: 2px solid #FF6F00 !important;
        outline: none !important;
    }

    .stButton button {
        background-color: #FF6F00 !important;
        color: white !important;
        font-size: 1.05em;
        padding: 0.5em 1.2em;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }

    .stButton button:hover {
        background-color: #F4511E !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .section {
        background-color: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 150, 136, 0.1);
        margin-bottom: 2rem;
    }

    .banner {
        background-color: #E0F2F1;
        color: #00796B;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-weight: 500;
        font-size: 1em;
    }

    .tip {
        background-color: #FFF3E0;
        color: #EF6C00;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-size: 0.95em;
        font-style: italic;
    }

    .stSelectbox > div {
        border: 2px solid #009688 !important;
        border-radius: 8px !important;
        padding: 6px;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        border: none !important;
    }

    div:empty { display: none !important; }

    .disclaimer {
        font-size: 0.9em;
        color: grey;
        text-align: center;
        margin-top: 2rem;
    }

    img[src*="pillai_logo"] {
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    </style>
""", unsafe_allow_html=True)

# Logo
def get_base64_image(path):
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

if os.path.exists("pillai_logo.png"):
    logo_base64 = get_base64_image("pillai_logo.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_base64}' width='240' style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# Language selector
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

# Multilingual labels
with open("labels.json", "r", encoding="utf-8") as f:
    all_labels = json.load(f)
L = all_labels.get(language, all_labels["English"])

# Tagline banner
st.markdown(f"<div class='banner'>💊 <strong>{L['tagline']}</strong></div>", unsafe_allow_html=True)

# API key setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = client.beta.threads.create().id

lang_codes = {"Te Reo Māori": "mi", "Samoan": "sm", "Mandarin": "zh-CN"}

# Main section
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.write(f"### 💬 {L['prompt']}")
st.markdown(f"<div class='tip'>{L['subtitle']}</div>", unsafe_allow_html=True)

# Input + Button
col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input(label="", placeholder=L["placeholder"], key="question_input")
with col2:
    send_clicked = st.button(L["send"])

# Chat handling
if send_clicked:
    if not user_question.strip():
        st.warning(L["empty"])
    else:
        with st.spinner(f"💬 {L['thinking']}"):
            try:
                client.beta.threads.messages.create(
                    thread_id=st.session_state["thread_id"],
                    role="user",
                    content=user_question
                )
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state["thread_id"],
                    assistant_id=ASSISTANT_ID
                )
                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state["thread_id"],
                        run_id=run.id
                    )
                    if run_status.status in ["completed", "failed"]:
                        break

                if run_status.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
                    latest = messages.data[0]
                    raw_answer = latest.content[0].text.value
                    cleaned = re.sub(r'【[^】]*】', '', raw_answer).strip()
                    if language in lang_codes:
                        translated = GoogleTranslator(source='auto', target=lang_codes[language]).translate(cleaned)
                        st.success(translated)
                    else:
                        st.success(cleaned)
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# Disclaimer
st.markdown(f"<div class='disclaimer'>{L['disclaimer']}</div>", unsafe_allow_html=True)

# Privacy Policy
with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
