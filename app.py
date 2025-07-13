import streamlit as st
from openai import OpenAI
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

# Language selector
language = st.selectbox("\U0001f310 Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Mandarin"])

# Labels
labels = {
    "English": {
        "prompt": "Ask a medicine question:",
        "placeholder": "💡 e.g: Can I take ibuprofen with Panadol?",
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
        "tagline": "Āwhinatia ngā Kiwi kia mārama ki ā rātou rongoā mā ngā kłrero mai i a Medsafe.",
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

**📩 Pātai?**  
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

**📩 Fesili?**  
Imeli: pillai.nz.contact@gmail.com

*Pill-AI e le suitulaga i fautuaga fa'apolofesa tau soifua mālōlōna.*"""
    },
    "Mandarin": {
        "prompt": "请提出一个与药物相关的问题：",
        "placeholder": "💡 例如：布洛芬和托热息病可以一起吃吗？",
        "send": "发送",
        "thinking": "思考中...",
        "tagline": "通过 Medsafe 的可靠信息帮助新西兰人了解他们的药物。",
        "empty": "请输入一个问题。",
        "error": "助手未能完成请求。",
        "disclaimer": "⚠️ Pill-AI 不能替代专业的医疗意见。请询问医生或药剂师。",
        "privacy_title": "🔐 隐私政策 – 点击展开",
        "privacy": """### 🛡️ Pill-AI 隐私政策（测试版）

欢迎使用 Pill-AI ，您值得信赖的用药助手。本工具为测试版，帮助用户通过 Medsafe 学习药品信息。

**📌 我们收集的信息**  
– 您在对话框中输入的问题  

**🔁 涉及的平台**  
– OpenAI（用于生成回答）  
– Streamlit（用于网站托管）  
– Google（托管和分析）

**👶 16岁以下用户**  
我们不会要求您的姓名、电子邮件或其他个人信息。

**🗑️ 数据处理**  
这是一个测试版。所有数据将在测试结束后删除。

**📩 联系方式**  
邮箱：pillai.nz.contact@gmail.com

*Pill-AI 并不能替代专业医疗意见。*"""
    }
}

L = labels.get(language, labels["English"])

