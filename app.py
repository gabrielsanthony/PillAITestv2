import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# 🔧 Custom CSS with font support for all languages
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari&display=swap');
    body {
        background-color: #f4f6f9;
        font-family: 'Noto Sans', sans-serif;
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
        font-family: 'Noto Sans', 'Noto Sans Devanagari', sans-serif !important;
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
        font-family: 'Noto Sans', 'Noto Sans Devanagari', sans-serif !important;
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

# Load and show logo

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

# Language selection
language = st.selectbox("Choose answer language:", ["English", "Te Reo Māori", "Samoan", "Spanish", "Mandarin", "Hindi"])

# UI translations
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
        "placeholder": "Tuhia ōtāu pātai ki konei...",
        "send": "Tukua",
        "thinking": "E whakaaro ana...",
        "empty": "Tēnā koa whakaurua he pātai.",
        "error": "I rahua te kaiwhina ki te whakautu.",
        "disclaimer": "⚠️ Ehara a Pill-AI i te tohutohu hauora. Me pātai tonu ki tō rata, ki te rongoā hoki."
    },
    "Samoan": {
        "prompt": "Fesili i se fesili e uiga i fualaau:",
        "placeholder": "Tusi i lau fesili i lalo...",
        "send": "Auina atu",
        "thinking": "O lo’o mafaufau...",
        "empty": "Fa’amolemole tusia se fesili.",
        "error": "E le’i mafai ona tali mai le fesoasoani.",
        "disclaimer": "⚠️ E le suitulaga Pill-AI i fautuaga faafomai. Fesili i lau foma’i po’o le fale talavai."
    },
    "Spanish": {
        "prompt": "Haz una pregunta sobre medicamentos:",
        "placeholder": "Escribe tu pregunta aquí...",
        "send": "Enviar",
        "thinking": "Pensando...",
        "empty": "Por favor, escribe una pregunta.",
        "error": "El asistente no pudo completar la solicitud.",
        "disclaimer": "⚠️ Pill-AI no sustituye el consejo médico profesional. Consulta siempre a un farmacéutico o médico."
    },
    "Mandarin": {
        "prompt": "请提出有关药物的问题：",
        "placeholder": "请在此输入问题...",
        "send": "发送",
        "thinking": "思考中...",
        "empty": "请输入一个问题。",
        "error": "助手未能完成该请求。",
        "disclaimer": "⚠️ Pill-AI 不能替代专业医疗意见，请约见医生或药剂师。"
    },
    "Hindi": {
        "prompt": "कृपया दवाओं से संबंधित प्रश्न पूछें:",
        "placeholder": "यहां अपना प्रश्न लिखें...",
        "send": "भेजें",
        "thinking": "चिंतन किया जा रहा है...",
        "empty": "कृपया कोई प्रश्न दाखिएं।",
        "error": "सहायक अनुरोध पूरा नहीं कर पाया।",
        "disclaimer": "⚠️ Pill-AI वैचिकारिक चिकित्सा सलाह की जगह नहीं लेता। कृपया कृपया चिकिट्सक जा फार्मासिस्ट से सलाह लें।"
    }
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

# Input
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
                    cleaned_answer = re.sub(r'【[^】]*】', '', raw_answer).strip()

                    target_map = {
                        "Te Reo Māori": "mi",
                        "Samoan": "sm",
                        "Spanish": "es",
                        "Mandarin": "zh-CN",
                        "Hindi": "hi"
                    }
                    if language in target_map:
                        translated = GoogleTranslator(source='auto', target=target_map[language]).translate(cleaned_answer)
                        st.success(translated)
                    else:
                        st.success(cleaned_answer)
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
