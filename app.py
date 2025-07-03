import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# Custom CSS for styling
st.markdown("""
    <style>
    body {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput > div > div > input {
        font-size: 1.2em;
        padding: 10px;
    }
    .stButton button {
        background-color: #3b82f6;
        color: white;
        font-size: 1.1em;
        padding: 0.6em 1.2em;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #2563eb;
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

# Function to load and encode logo
def get_base64_image(path):
    with open(path, "rb") as img_file:
        b64 = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{b64}"

# Load logo
logo_base64 = get_base64_image("pillai_logo.png")
st.markdown(f"""
<div style='text-align: center;'>
    <img src='{logo_base64}' width='180' style='margin-bottom: 10px;'>
    <h3 style='color: #333;'>Your Trusted Medicines Chatbot</h3>
</div>
""", unsafe_allow_html=True)

# API Setup
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"

# Session state thread
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id

# Input Section
with st.container():
    st.markdown("<div class='section'>", unsafe_allow_html=True)

    st.write("### 💬 Ask a medicine-related question:")
    user_question = st.text_input("Type your question below:", key="question_input")

    language = st.selectbox("🌐 Choose answer language:", ["English", "Te Reo Māori", "Samoan"])

    if st.button("Send"):
        if not user_question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                try:
                    # Add user message
                    client.beta.threads.messages.create(
                        thread_id=st.session_state["thread_id"],
                        role="user",
                        content=user_question
                    )

                    # Run assistant
                    run = client.beta.threads.runs.create(
                        thread_id=st.session_state["thread_id"],
                        assistant_id=ASSISTANT_ID
                    )

                    # Wait for completion
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

                        if language == "Te Reo Māori":
                            translated = GoogleTranslator(source='auto', target='mi').translate(cleaned_answer)
                            st.success(translated)
                        elif language == "Samoan":
                            translated = GoogleTranslator(source='auto', target='sm').translate(cleaned_answer)
                            st.success(translated)
                        else:
                            st.success(cleaned_answer)
                    else:
                        st.error("The assistant failed to complete the request.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# Disclaimer Section
st.markdown("""
<div style='text-align: center; color: grey; font-size: 0.9em; margin-top: 40px;'>
⚠️ Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP.
</div>
""", unsafe_allow_html=True)

# Privacy Policy Section
with st.expander("🔐 Privacy Policy – Click to expand"):
    st.markdown("""
    ### 🛡️ Pill-AI Privacy Policy (Prototype Version)

    Welcome to Pill-AI — your trusted medicines advisor. This is a prototype tool designed to help people learn about their medicines using trusted Medsafe resources.

    **📌 What we collect**  
    When you use Pill-AI, we store:  
    – The questions you type into the chat box  
    This helps us understand how people are using the tool and improve it during testing.

    **🔁 Who else is involved**  
    Pill-AI uses services from:  
    – OpenAI (for generating answers)  
    – Streamlit (to host the app)  
    – Google (possibly for hosting, analytics, or error logging)  
    These platforms may collect some technical data like your device type or browser, but not your name.

    **👶 Users under 16**  
    Pill-AI can be used by people under 16. We don’t ask for names, emails, or personal details — just medicine-related questions.  
    If you're under 16, please ask a parent or guardian before using Pill-AI.

    **🗑️ Data won’t be kept forever**  
    This is just a prototype. All stored data (like your questions) will be deleted once the testing is over.  
    No long-term tracking, no selling of data — ever.

    **📬 Questions?**  
    Contact us at: pillai.nz.contact@gmail.com

    *Pill-AI is not a substitute for professional medical advice. Always check with a doctor or pharmacist if you're unsure.*
    """)

