import streamlit as st
import openai
import os
import re
import base64
import json
from deep_translator import GoogleTranslator
from difflib import get_close_matches

# Load Medsafe PDF links
try:
    with open("medsafe_source_links_cleaned.json", "r") as f:
        medsafe_links = json.load(f)
except Exception as e:
    medsafe_links = {}
    st.warning(f"Could not load Medsafe links: {e}")

# Page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# Custom CSS
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari&family=Noto+Sans+SC&display=swap" rel="stylesheet">
    <style>
    body { background-color: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
    html[lang='zh'] body { font-family: 'Noto Sans SC', sans-serif !important; }
    html[lang='hi'] body { font-family: 'Noto Sans Devanagari', sans-serif !important; }
    .stTextInput input {
        background-color: #eeeeee !important;
        color: #000000 !important;
        font-size: 1.2em !important;
        padding: 10px !important;
        border: 2px solid black !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus { border: 2px solid orange !important; outline: none !important; }
    .stButton button {
        background-color: #3b82f6;
        color: white;
        font-size: 1.1em;
        padding: 0.5em 1.2em;
        border-radius: 8px;
        margin-top: 14px !important;
    }
    .stButton button:hover { background-color: #2563eb; }
    div[data-testid="column"] {
        display: flex; align-items: flex-start; gap: 10px;
    }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Logo
def get_base64_image(path):
    with open(path, "rb") as img_file:
        b64 = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{b64}"

logo_base64 = get_base64_image("pillai_logo.png")
st.markdown(f"""
<div style='text-align: center;'>
    <img src='{logo_base64}' width='240' style='margin-bottom: 10px;'>
</div>
""", unsafe_allow_html=True)

# Language select
language = st.selectbox("🌐 Choose answer language:",
    ["English", "Te Reo Māori", "Samoan", "Spanish", "Mandarin", "Hindi"]
)

# Labels
labels = {
    "English": {
        "prompt": "Ask a medicine-related question:",
        "placeholder": "Type your question here...",
        "send": "Send",
        "thinking": "Thinking...",
        "empty": "Please enter a question.",
        "error": "The assistant failed to complete the request.",
        "disclaimer": "⚠️ Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP."
    }
    # (Add other languages here if needed)
}
L = labels[language]

# OpenAI setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id

# Fuzzy Medsafe link matcher
def find_medsafe_link(answer_text):
    answer_text_lower = answer_text.lower()
    possible_keys = [k.lower().replace("source_", "").replace("_", " ") for k in medsafe_links]
    
    # Try exact partial match first
    for original_key, key_clean in zip(medsafe_links.keys(), possible_keys):
        if key_clean in answer_text_lower:
            return medsafe_links[original_key]

    # Try fuzzy match
    close = get_close_matches(answer_text_lower, possible_keys, n=1, cutoff=0.5)
    if close:
        match_index = possible_keys.index(close[0])
        match_key = list(medsafe_links.keys())[match_index]
        return medsafe_links[match_key]

    return None

# UI
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.write(f"### 💬 {L['prompt']}")

col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input(label="", placeholder=L["placeholder"], key="question_input")
with col2:
    send_clicked = st.button(L["send"])

if send_clicked:
    if not user_question.strip():
        st.warning(L["empty"])
    else:
        with st.spinner(L["thinking"]):
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

                    # Translate if needed
                    lang_codes = {
                        "Te Reo Māori": "mi",
                        "Samoan": "sm",
                        "Spanish": "es",
                        "Mandarin": "zh-CN",
                        "Hindi": "hi"
                    }
                    if language in lang_codes:
                        translated = GoogleTranslator(source='auto', target=lang_codes[language]).translate(cleaned)
                        st.success(translated)
                    else:
                        st.success(cleaned)

                    # Show PDF link
                    pdf = find_medsafe_link(cleaned)
                    if pdf:
                        st.markdown(f"📄 [View full Medsafe Consumer Info PDF]({pdf})", unsafe_allow_html=True)
                else:
                    st.error(L["error"])
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
with st.expander("🔐 Privacy Policy – Click to expand"):
    st.markdown("""
    ### 🛡️ Pill-AI Privacy Policy (Prototype Version)

    Welcome to Pill-AI - your trusted medicines advisor. This is a prototype tool designed to help people learn about their medicines using trusted Medsafe resources.

    **📌 What we collect**  
    When you use Pill-AI, we store:  
    – The questions you type into the chat box  
    This helps us understand how people are using the tool and improve it during testing.

    **🔁 Who else is involved**  
    Pill-AI uses services from:  
    – OpenAI (for generating answers)  
    – Streamlit (to host the app)  
    – Google (possibly for hosting, analytics, or error logging)

    **👶 Users under 16**  
    Pill-AI can be used by people under 16. We don’t ask for names, emails, or personal details.  
    If you're under 16, please ask a parent or guardian before using Pill-AI.

    **🗑️ Data won’t be kept forever**  
    This is just a prototype. All stored data will be deleted once testing is over.

    **📬 Questions?**  
    Contact: pillai.nz.contact@gmail.com

    *Always check with a healthcare professional if unsure.*
    """)
