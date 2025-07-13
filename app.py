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

# Custom CSS (unchanged)
# ... keep your existing CSS here ...

# Logo
@st.cache_data
def get_base64_image(path):
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

if os.path.exists("pillai_logo.png"):
    logo_base64 = get_base64_image("pillai_logo.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_base64}' width='240'></div>", unsafe_allow_html=True)

# Tagline
fallback_tagline = " Helping Kiwis understand their pills, safely."
st.markdown(f"""
    <div style='
        background: #e0f7fa;
        border-left: 6px solid #00acc1;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 1em;
        margin-bottom: 1.2rem;
        color: #006064;
    '>
        💊 <strong>{fallback_tagline}</strong>
    </div>
""", unsafe_allow_html=True)

# Language selector and labels
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])
labels = {...}  # Keep your existing full dictionary here
L = labels.get(language, labels["English"])

# OpenAI setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

lang_codes = {"Te Reo Māori": "mi", "Samoan": "sm", "Mandarin": "zh-CN"}

# Main UI section
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.write(f"### 💬 {L['prompt']}")

# Input and Send button in same line
col1, col2 = st.columns([6, 1])
with col1:
    user_question = st.text_input(
        label="",
        placeholder=L["placeholder"],
        key="question_input"
    )
with col2:
    st.markdown("<div style='margin-top: 32px;'>", unsafe_allow_html=True)
    send_button = st.button(L["send"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

send_clicked = send_button and user_question.strip() != ""

# Simplify checkbox
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

# Submit question
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

# Disclaimer and Privacy
st.markdown(f"""
<div style='text-align: center; color: grey; font-size: 0.9em; margin-top: 40px;'>
{L["disclaimer"]}
</div>
""", unsafe_allow_html=True)

with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
