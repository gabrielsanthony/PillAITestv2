import streamlit as st
import openai
import os
import re
import base64
import json
from deep_translator import GoogleTranslator

# --- Load Medsafe PDF links ---
try:
    with open("medsafe_source_links_cleaned.json", "r") as f:
        medsafe_links = json.load(f)
except Exception as e:
    medsafe_links = {}
    st.warning(f"Could not load Medsafe links: {e}")

# --- Page config ---
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# --- Custom CSS ---
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
        box-shadow: none !important;
    }
    .stTextInput input:focus {
        border: 2px solid orange !important;
        outline: none !important;
    }
    .stButton button {
        background-color: #3b82f6;
        color: white;
        font-size: 1.1em;
        padding: 0.5em 1.2em;
        border-radius: 8px;
        margin-top: 14px !important;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #2563eb;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Logo ---
def get_base64_image(path):
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

if os.path.exists("pillai_logo.png"):
    logo_base64 = get_base64_image("pillai_logo.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_base64}' width='240' style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# --- Language selector ---
language = st.selectbox("🌐 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Spanish", "Mandarin", "Hindi"])

labels = {
    "English": {
        "prompt": "Ask a medicine-related question:",
        "placeholder": "Type your question here...",
        "send": "Send",
        "thinking": "Thinking...",
        "empty": "Please enter a question.",
        "error": "The assistant failed to complete the request.",
        "disclaimer": "⚠️ Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP."
    },
}
L = labels[language]

# --- API Setup ---
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = client.beta.threads.create().id

# --- Find PDF link helper ---
def find_medsafe_link(answer_text):
    for key, url in medsafe_links.items():
        key_clean = key.lower().replace("source_", "").replace("_", " ")
        if key_clean in answer_text.lower():
            return url
    return None

# --- UI input section ---
st.markdown("### 💬 " + L["prompt"])
col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input(label="", placeholder=L["placeholder"], key="question_input")
with col2:
    send_clicked = st.button(L["send"])

# --- Handle interaction ---
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
                    cleaned_answer = re.sub(r'【[^】]*】', '', raw_answer).strip()

                    lang_codes = {
                        "Te Reo Māori": "mi",
                        "Samoan": "sm",
                        "Spanish": "es",
                        "Mandarin": "zh-CN",
                        "Hindi": "hi"
                    }
                    if language in lang_codes:
                        translated = GoogleTranslator(source='auto', target=lang_codes[language]).translate(cleaned_answer)
                        st.success(translated)
                    else:
                        st.success(cleaned_answer)

                    pdf_url = find_medsafe_link(cleaned_answer)
                    if pdf_url:
                        st.markdown(f"📄 [View full Medsafe Consumer Info PDF]({pdf_url})", unsafe_allow_html=True)
                else:
                    st.error(L["error"])
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- Disclaimer ---
st.markdown(f"""
<div style='text-align: center; color: grey; font-size: 0.9em; margin-top: 40px;'>
{L["disclaimer"]}
</div>
""", unsafe_allow_html=True)

# --- Privacy policy ---
with st.expander("🔐 Privacy Policy – Click to expand"):
    st.markdown("""
    ### 🛡️ Pill-AI Privacy Policy (Prototype Version)

    **📌 What we collect**  
    – The questions you type into the chat box

    **🔁 Who else is involved**  
    – OpenAI (answers), Streamlit (host), Google (possible hosting/logging)

    **👶 Users under 16**  
    – Ask a parent before using. No names/emails are collected.

    **🗑️ Data won’t be kept forever**  
    – This is a prototype. Your questions will be deleted after testing ends.

    **📬 Questions?**  
    Email: pillai.nz.contact@gmail.com

    *Always check with a doctor or pharmacist if you're unsure.*
    """)
