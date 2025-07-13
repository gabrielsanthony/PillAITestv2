import streamlit as st
import openai
import os
import re
import base64
import json
from deep_translator import GoogleTranslator

# Load Medsafe PDF links
@st.cache_data
def load_medsafe_links():
    try:
        with open("medsafe_source_links_cleaned.json", "r") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load Medsafe links: {e}")
        return {}

medsafe_links = load_medsafe_links()

# Page config
st.set_page_config(page_title="Pill-AI 2.0", page_icon="💊", layout="centered")

# Custom CSS
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari&family=Noto+Sans+SC&display=swap" rel="stylesheet">
    <style>
    body {
        background: linear-gradient(to bottom right, #f4f6f9, #e0f7fa);
        font-family: 'Segoe UI', sans-serif;
    }
    html[lang='zh'] body { font-family: 'Noto Sans SC', sans-serif !important; }
    .stTextInput input {
        background-color: #eeeeee !important;
        color: #000000 !important;
        font-size: 1.2em !important;
        padding: 10px !important;
        border: 2px solid black !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }
    div:empty { display: none !important; }
    .stTextInput input:focus { border: 2px solid orange !important; outline: none !important; }
    .stButton button {
        background-color: #3b82f6;
        color: white;
        font-size: 1.1em;
        padding: 0.6em 1em;
        border-radius: 8px;
        margin-top: 4px;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #2563eb;
    }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    img[src*="pillai_logo"] {
        animation: float 3s ease-in-out infinite;
    }
    .stSelectbox div[data-baseweb="select"] {
        margin-top: 6px;
        font-size: 1.05em;
        padding: 6px;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
    }
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: #999 !important;
    }
    @media (max-width: 768px) {
    .stTextInput input {
        font-size: 1em !important;
    }
    .stButton button {
        font-size: 1em !important;
        padding: 0.6em !important;
    }
    </style>
""", unsafe_allow_html=True)

# Logo
@st.cache_data
def get_base64_image(path):
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

if os.path.exists("pillai_logo.png"):
    logo_base64 = get_base64_image("pillai_logo.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_base64}' width='240'></div>", unsafe_allow_html=True)

# Language selection
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

# Language labels dictionary (shortened)
labels = {...}  # Use your existing full dictionary
L = labels.get(language, labels["English"])

# OpenAI setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

lang_codes = {"Te Reo Māori": "mi", "Samoan": "sm", "Mandarin": "zh-CN"}

# UI Section
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.write(f"### 💬 {L['prompt']}")

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("<div style='margin-top: 8px;'>", unsafe_allow_html=True)
    user_question = st.text_input("", placeholder=L["placeholder"], key="question_input")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div style='margin-top: 35px;'>", unsafe_allow_html=True)
    send_button = st.button(L["send"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

send_clicked = send_button and user_question.strip() != ""

st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

col_center = st.columns([1, 2, 1])
with col_center[1]:
    with st.container():
        st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] {
                display: flex;
                justify-content: center;
            }
            label[data-testid="stCheckbox"] {
                font-size: 1.2em;
                font-weight: 500;
            }
            </style>
        """, unsafe_allow_html=True)
        explain_like_12 = st.checkbox("🧠 Simplify the answer", value=True)

if send_clicked:
    st.session_state["question_submitted"] = user_question
    with st.spinner(f"💬 {L['thinking']}"):
        try:
            adjusted_question = user_question
            if explain_like_12:
                adjusted_question += " Please explain this in simple language suitable for a 12-year-old (I am not actually 12 though, don't use slang or colloquialisms, be encouraging)."

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": adjusted_question}],
                temperature=0.7,
                api_key=api_key
            )

            answer = response.choices[0].message.content
            cleaned = re.sub(r'【[^】]*】', '', answer).strip()

            if language in lang_codes:
                translated = GoogleTranslator(source='auto', target=lang_codes[language]).translate(cleaned)
                st.success(translated)
            else:
                st.success(cleaned)

        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# Disclaimer
st.markdown(f"""
<div style='text-align: center; color: grey; font-size: 0.9em; margin-top: 40px;'>
{L["disclaimer"]}
</div>
""", unsafe_allow_html=True)

# Privacy
with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
