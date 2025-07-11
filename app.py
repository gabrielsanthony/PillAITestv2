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
    .stButton > button {
        width: 100% !important;
        font-size: 1.1em;
        padding: 0.6em;
        border-radius: 6px;
        margin-top: 10px;
        background-color: #3b82f6;
        color: white;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
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

# Initial tagline (before language selection)
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

# Language selector
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

labels = {
    "English": {
        "prompt": "Ask a medicine question:",
        "placeholder": "e.g: Can I take ibuprofen with Panadol?",
        "send": "Send",
        "thinking": "Thinking...",
        "tagline": "Helping Kiwis understand medicines, safely.",
        "empty": "Please enter a question.",
        "error": "The assistant failed to complete the request.",
        "disclaimer": "⚠️ Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP.",
        "privacy_title": "🔐 Privacy Policy – Click to expand",
        "privacy": """### 🛡️ Pill-AI Privacy Policy (Prototype Version)

Welcome to Pill-AI — your trusted medicines advisor. This is a prototype tool designed to help people learn about their medicines using trusted Medsafe resources.

**📌 What we collect**  
– The questions you type into the chat box  

**🔁 Who else is involved**  
– OpenAI (for generating answers)  
– Streamlit (to host the app)  
– Google (for hosting and analytics)

**👶 Users under 16**  
We don’t ask for names, emails, or any personal information.

**🗑️ Temporary data**  
All data will be deleted after testing. This is a prototype.

**📬 Questions?**  
Contact us: pillai.nz.contact@gmail.com

*Pill-AI is not a substitute for professional medical advice.*"""
    },
    "Te Reo Māori": {
        "prompt": "Pātaihia tētahi pātai e pā ana ki te rongoā:",
        "placeholder": "💡 Hei tauira: Ka pai rānei te tango i te ibuprofen me te Panadol?",
        "send": "Tukua",
        "thinking": "E whakaaro ana...",
        "tagline": "Āwhinatia ngā Kiwi kia mārama ki ā rātou rongoā mā ngā kōrero mai i a Medsafe.",
        "empty": "Tēnā koa, tuhia he pātai.",
        "error": "I rahua te kaiawhina ki te whakaoti i te tono.",
        "disclaimer": "⚠️ Ehara a Pill-AI i te kaiārahi hauora tōtika. Me toro atu ki te rata, te kai rongoā rānei.",
        "privacy_title": "🔐 Kaupapahere Tūmataiti – Pāwhiritia kia kite",
        "privacy": """### 🛡️ Kaupapahere Tūmataiti o Pill-AI (Putanga Whakamātau)

Nau mai ki a Pill-AI — tō kaiāwhina rongoā pono. He putanga whakamātau tēnei hei āwhina i te iwi kia mārama ki ā rātou rongoā mā ngā rauemi Medsafe.

**📌 Ka kohia**  
– Ngā pātai ka tuhia e koe  

**🔁 Ko wai anō e uru ana**  
– OpenAI (hei hanga whakautu)  
– Streamlit (hei tuku i te pae tukutuku)  
– Google (hei manaaki me te aromātai)

**👶 Tamariki i raro i te 16**  
Kāore mātou e tono mō ō ingoa, īmēra, rānei.

**🗑️ Raraunga poto noa**  
Ka mukua katoatia ngā raraunga i muri i te wā whakamātau. He putanga whakamātau tēnei.

**📬 Pātai?**  
Whakapā mai: pillai.nz.contact@gmail.com

*Ehara a Pill-AI i te whakakapi mō ngā tohutohu hauora.*"""
    },
    "Samoan": {
        "prompt": "Fesili i se fesili e uiga i fualaau:",
        "placeholder": "💡 Fa'ata'ita'iga: E mafai ona ou inuina le ibuprofen ma le Panadol?",
        "send": "Auina atu",
        "thinking": "O mafaufau...",
        "tagline": "Fesoasoani i tagata Niu Sila ia malamalama i a latou fualaau e ala i fa'amatalaga fa'atuatuaina mai le Medsafe.",
        "empty": "Fa'amolemole tusia se fesili.",
        "error": "Le mafai e le fesoasoani ona tali atu.",
        "disclaimer": "⚠️ E le suitulaga Pill-AI i se foma'i moni. Fa'amolemole fa'afeso'ota'i se foma'i po'o se fomai fai fualaau.",
        "privacy_title": "🔐 Faiga Fa'alilolilo – Kiliki e faitau",
        "privacy": """### 🛡️ Faiga Fa'alilolilo a Pill-AI (Fa'ata'ita'iga)

Afio mai i Pill-AI — lau fesoasoani i fualaau. O se fa'ata'ita'iga lenei e fesoasoani i tagata ia malamalama i fualaau e fa'aaogaina ai fa'amatalaga mai Medsafe.

**📌 Mea matou te pueina**  
– Fesili e te tusia i le pusa fesili  

**🔁 O ai e fesoasoani**  
– OpenAI (mo tali atamai)  
– Streamlit (mo le upega tafa'ilagi)  
– Google (mo le talimalo ma le iloiloga)

**👶 I lalo o le 16 tausaga**  
Matou te le aoina ni igoa, imeli, po'o fa'amatalaga patino.

**🗑️ Fa'amatalaga le tumau**  
O fa'amatalaga uma o le a tapea pe a uma le vaitaimi o le fa'ata'ita'iga.

**📬 Fesili?**  
Imeli: pillai.nz.contact@gmail.com

*Pill-AI e le suitulaga i fautuaga fa'apolofesa tau soifua mālōlōina.*"""
    },
    "Mandarin": {
        "prompt": "请提出一个与药物有关的问题：",
        "placeholder": "💡 例如：布洛芬和扑热息痛可以一起吃吗？",
        "send": "发送",
        "thinking": "思考中...",
        "tagline": "通过 Medsafe 的可靠信息帮助新西兰人了解他们的药物。",
        "empty": "请输入一个问题。",
        "error": "助手未能完成请求。",
        "disclaimer": "⚠️ Pill-AI 不能替代专业医疗建议。请咨询医生或药剂师。",
        "privacy_title": "🔐 隐私政策 – 点击展开",
        "privacy": """### 🛡️ Pill-AI 隐私政策（测试版）

欢迎使用 Pill-AI —— 您值得信赖的用药助手。本工具为测试版本，帮助用户通过 Medsafe 学习药品信息。

**📌 我们收集的信息**  
– 您在对话框中输入的问题  

**🔁 涉及的平台**  
– OpenAI（用于生成回答）  
– Streamlit（用于网站托管）  
– Google（托管和分析）

**👶 16岁以下用户**  
我们不会索取您的姓名、电邮或其他个人信息。

**🗑️ 数据处理**  
这是一个测试版本。所有数据将在测试结束后删除。

**📬 联系方式**  
邮箱：pillai.nz.contact@gmail.com

*Pill-AI 并不能替代专业医疗建议。*"""
    }
}


# Get selected labels
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

lang_codes = {"Te Reo Māori": "mi", "Samoan": "sm", "Mandarin": "zh-CN"}

# UI Section
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.write(f"### 💬 {L['prompt']}")

with st.form(key="question_form"):
    user_question = st.text_input(
        label="",
        placeholder=L["placeholder"],
        key="question_input"
    )

    explain_like_12 = st.checkbox("🧠 Simplify the answer", value=True)

    # Make the button full width
    st.markdown("""
        <style>
        .full-width-button > button {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    submit = st.form_submit_button(label=L["send"], help="Click to send your question.", type="primary")

send_clicked = submit and user_question.strip()


if send_clicked:
    st.session_state["question_submitted"] = user_question


if send_clicked:
    if not user_question.strip():
        st.warning(L["empty"])
    else:
        with st.spinner(f"💬 {L['thinking']}"):
            try:
                adjusted_question = user_question
                if explain_like_12:
                    adjusted_question += " Please explain this in simple language suitable for a 12-year-old (MY AGE ISN'T 12 THOUGH)."

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
st.markdown(f"""
<div style='text-align: center; color: grey; font-size: 0.9em; margin-top: 40px;'>
{L["disclaimer"]}
</div>
""", unsafe_allow_html=True)

# Privacy
with st.expander(L["privacy_title"]):
    st.markdown(L["privacy"])
