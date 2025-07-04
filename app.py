import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# 🔧 Custom CSS
st.markdown("""
    <style>
    body {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput input {
        background-color: #eeeeee !important;
        color: #000000 !important;
        font-size: 1.2em !important;
        padding: 10px !important;
        border: 2px solid black !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        transition: border 0.3s ease-in-out;
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
    div[data-testid="column"] {
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# 🖼 Load and show logo
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

# 🌐 Language selection with flags
language_display_names = {
    "English": "🇬🇧 English",
    "Te Reo Māori": "🇳🇿 Te Reo Māori",
    "Samoan": "🇼🇸 Samoan",
    "Spanish": "🇪🇸 Spanish",
    "Mandarin": "🇨🇳 Mandarin"
}
display_to_lang = {v: k for k, v in language_display_names.items()}

selected_display = st.selectbox(
    "🌐 Choose answer language:",
    list(language_display_names.values())
)
language = display_to_lang[selected_display]

# UI text translations
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
    "Te Reo Māori": {
        "prompt": "Pātai he pātai mō te rongoā:",
        "placeholder": "Tuhia tō pātai ki konei...",
        "send": "Tukua",
        "thinking": "E whakaaro ana...",
        "empty": "Tēnā, whakaurua he pātai.",
        "error": "I rahua te kaiwhina ki te whakautu.",
        "disclaimer": "⚠️ Ehara a Pill-AI i te tohutohu hauora mō te tangata. Me pātai tonu ki tō rata, ki te rongoā hoki."
    },
    "Samoan": {
        "prompt": "Fesili i se fesili e
