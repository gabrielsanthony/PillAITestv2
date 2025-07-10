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
        padding: 0.5em 1.2em;
        border-radius: 8px;
        margin-top: 14px !important;
    }
    .stButton button:hover { background-color: #2563eb; }
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
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

if os.path.exists("pillai_logo.png"):
    logo_base64 = get_base64_image("pillai_logo.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_base64}' width='240' style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 1.1em; margin-bottom: 1rem; color: #333;'>
        💊 <i>Helping New Zealanders understand their medicines using trusted Medsafe info.</i>
    </div>
""", unsafe_allow_html=True)

# Language select
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

# Labels (multilingual UI)
labels = {
    "English": {
        "prompt": "Ask a medicine-related question:",
        "placeholder": "Type your question here...",
        "send": "Send",
        "thinking": "Thinking...",
        "empty": "Please enter a question.",
        "error": "The assistant failed to complete the request.",
        "disclaimer": "⚠️ Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP.",
        "privacy_title": "🔐 Privacy Policy – Click to expand",
        "privacy": """
### 🛡️ Pill-AI Privacy Policy (Prototype Version)

Welcome to Pill-AI — your trusted medicines advisor. This is a prototype tool designed to help people learn about their medicines using trusted Medsafe resources.

**📌 What we collect**  
– The questions you type into the chat box  

**🔁 Who else is involved**  
– OpenAI (for generating answers)  
– Streamlit (to host the app)  
– Google (hosting/analytics)

**👶 Users under 16**  
No names, emails or personal details are asked.  

**🗑️ Temporary data**  
This is a prototype. All data will be deleted after testing.  

**📬 Questions?**  
Contact us: pillai.nz.contact@gmail.com

*Pill-AI is not a substitute for professional medical advice.*
"""
    },
    "Te Reo Māori": {
        "prompt": "Pātaihia tētahi pātai e pā ana ki te rongoā:",
        "placeholder": "Tuhia tō pātai ki konei...",
        "send": "Tukua",
        "thinking": "E whakaaro ana...",
        "empty": "Tēnā koa, tuhia he pātai.",
        "error": "I rahua te kaiawhina ki te whakaoti i te tono.",
        "disclaimer": "⚠️ Ehara a Pill-AI i te kaiārahi hauora tōtika. Me toro atu ki te rata, te kai rongoā rānei.",
        "privacy_title": "🔐 Kaupapahere Tūmataiti – Pāwhiritia kia kite",
        "privacy": """
### 🛡️ Kaupapahere Tūmataiti o Pill-AI (Putanga Whakamātau)

Nau mai ki a Pill-AI — tō kaiāwhina rongoā pono. He putanga whakamātau tēnei hei āwhina i te iwi kia mārama ki ā rātou rongoā mā ngā rauemi Medsafe.

**📌 Ka kohia**  
– Ngā pātai e patopato ai koe  

**🔁 Ko wai anō e uru ana**  
– OpenAI (hei waihanga whakautu)  
– Streamlit  
– Google (hei whakahaere, aromatawai hoki)

**👶 Tamariki i raro i te 16**  
Kāore mātou e kohi i ngā ingoa, īmēra, aha atu rānei.

**🗑️ Raraunga poto noa**  
Ka mukua ngā raraunga i muri i te wā whakamātau.

**📬 Pātai?**  
Whakapā mai: pillai.nz.contact@gmail.com

*Ehara a Pill-AI i te kaiāwhina rongoā tōtika.*
"""
    },
    "Samoan": {
        "prompt": "Fesili i se fesili e uiga i fualaau:",
        "placeholder": "Tusi i lau fesili iinei...",
        "send": "Auina atu",
        "thinking": "O mafaufau...",
        "empty": "Fa'amolemole tusia se fesili.",
        "error": "Le mafai e le fesoasoani ona tali atu.",
        "disclaimer": "⚠️ E le suitulaga Pill-AI i se foma'i moni. Fa'amolemole fa'afeso'ota'i se foma'i po'o se fomai fai fualaau.",
        "privacy_title": "🔐 Faiga Fa'alilolilo – Kiliki e faitau",
        "privacy": """
### 🛡️ Faiga Fa'alilolilo a Pill-AI (Fa'ata'ita'iga)

Afio mai i Pill-AI — lau fesoasoani i fualaau. O se fa'ata'ita'iga lenei e fesoasoani i tagata ia malamalama i fualaau e fa'aaogaina ai fa'amatalaga mai Medsafe.

**📌 Mea matou te pueina**  
– Fesili e te tusia  

**🔁 O ai e fesoasoani**  
– OpenAI  
– Streamlit  
– Google  

**👶 I lalo o le 16 tausaga**  
Matou te le aoina ni igoa po'o ni fa'amatalaga patino.

**🗑️ Fa'amatalaga le tumau**  
O le fa'ata'ita'iga lenei. O le a tapea uma a matou fa'amaumauga.

**📬 Fesili?**  
Fa'afeso'ota'i mai: pillai.nz.contact@gmail.com

*E le suitulaga Pill-AI i se foma'i moni.*
"""
    },
    "Mandarin": {
        "prompt": "请提出一个与药物有关的问题：",
        "placeholder": "在此输入您的问题...",
        "send": "发送",
        "thinking": "思考中...",
        "empty": "请输入一个问题。",
        "error": "助手未能完成请求。",
        "disclaimer": "⚠️ Pill-AI 不能替代专业医疗建议。请咨询医生或药剂师。",
        "privacy_title": "🔐 隐私政策 – 点击展开",
        "privacy": """
### 🛡️ Pill-AI 隐私政策（测试版）

欢迎使用 Pill-AI — 您值得信赖的用药助手。本工具为测试版本，帮助用户通过 Medsafe 学习药品信息。

**📌 我们收集**  
– 您输入的问题  

**🔁 相关平台**  
– OpenAI  
– Streamlit  
– Google  

**👶 16 岁以下用户**  
我们不收集姓名、电邮或个人信息。

**🗑️ 数据临时保存**  
测试结束后将删除所有数据。

**📬 问题联系**  
邮箱：pillai.nz.contact@gmail.com

*Pill-AI 不能替代专业医疗建议。*
"""
    }
}

L = labels.get(language, labels["English"])

# OpenAI setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = client.beta.threads.create().id

# Lang code map
lang_codes = {
    "Te Reo Māori": "mi",
    "Samoan": "sm",
    "Mandarin": "zh-CN"
}

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

                    if language in lang_codes:
                        translated = GoogleTranslator(source='auto', target=lang_codes[language]).translate(cleaned)
                        st.success(translated)
                    else:
                        st.success(cleaned)

                    pdf_matches = find_medsafe_links(cleaned)
                    if pdf_matches:
                        st.markdown("\n**📄 Related Medsafe Consumer Info PDFs:**")
                        for score, name, url in pdf_matches:
                            display_name = name.title()
                            st.markdown(f"- [{display_name}]({url})", unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        🔍 No direct Medsafe PDF found for this topic.  
                        👉 [Medsafe CMI Search](https://www.medsafe.govt.nz/Consumers/CMI/CMI.asp)
                        """, unsafe_allow_html=True)
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

# Privacy Policy
with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
