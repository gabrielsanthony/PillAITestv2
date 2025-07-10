import streamlit as st
import openai
import os
import re
import base64
import json
from deep_translator import GoogleTranslator

# Load Medsafe links
try:
    with open("medsafe_source_links_cleaned.json", "r") as f:
        medsafe_links = json.load(f)
except Exception as e:
    medsafe_links = {}
    st.warning(f"Could not load Medsafe links: {e}")

# App settings
st.set_page_config(page_title="Pill-AI 2.0", page_icon="💊", layout="centered")

# Base64 logo (from uploaded image)
logo_base64 = "iVBORw0KGgoAAAANSUhEUgAAA7IAAANGCAYAAADAg7L7AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMA"
st.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{logo_base64}' width='220' style='margin-bottom:10px'></div>", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    body {
        background: linear-gradient(to bottom right, #f4f6f9, #e0f7fa);
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput input {
        background-color: #f9f9f9 !important;
        font-size: 1.1em !important;
        padding: 10px !important;
        border: 2px solid #ccc !important;
        border-radius: 8px !important;
    }
    .stButton button {
        background-color: #3b82f6;
        color: white;
        font-size: 1.1em;
        padding: 0.45em 1.2em;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #2563eb;
    }
    .section {
        background-color: #fff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Language selector
language = st.selectbox("🌐 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

# Load translation labels
lang_codes = {"Te Reo Māori": "mi", "Samoan": "sm", "Mandarin": "zh-CN"}
labels = { ... }  # Keep your existing `labels` dictionary here (unchanged)
L = labels.get(language, labels["English"])

# Header
st.markdown(f"""
<div style='
    background: #e0f7fa;
    border-left: 6px solid #00acc1;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 1em;
    color: #006064;
    margin-bottom: 20px;
'>
💊 <strong>{L["tagline"]}</strong>
</div>
""", unsafe_allow_html=True)

# Input section
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown(f"### 💬 {L['prompt']}")
st.markdown(f"""
<div style='
    background-color: #e0f7f7;
    padding: 8px 12px;
    border-left: 4px solid #008080;
    border-radius: 6px;
    font-size: 0.95em;
    color: #004d4d;
    margin-bottom: 10px;
'>
{L['subtitle']}
</div>
""", unsafe_allow_html=True)

# Simple language checkbox
explain_like_12 = st.checkbox("🧒 Explain in simple language", value=False)

# Input + button
col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input("", placeholder=L["placeholder"], key="question_input")
with col2:
    send_clicked = st.button(L["send"])

# OpenAI key + thread setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = client.beta.threads.create().id

# When user submits
if send_clicked:
    if not user_question.strip():
        st.warning(L["empty"])
    else:
        with st.spinner(f"💬 {L['thinking']}"):
            try:
                adjusted_question = user_question
                if explain_like_12:
                    adjusted_question += " Please explain this in simple language suitable for a 12-year-old."

                client.beta.threads.messages.create(
                    thread_id=st.session_state["thread_id"],
                    role="user",
                    content=adjusted_question
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
st.markdown(f"<div style='text-align:center; color:gray; font-size:0.9em; margin-top:40px'>{L['disclaimer']}</div>", unsafe_allow_html=True)

# Privacy section
with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
