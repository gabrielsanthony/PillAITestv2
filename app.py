import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Set Streamlit page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# Centered logo with subtitle (tight spacing)
def get_base64_image(path):
    with open(path, "rb") as img_file:
        b64 = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{b64}"

# ✅ Get the encoded logo
logo_base64 = get_base64_image("pillai_logo.png")

st.markdown(f"""
<div style='text-align: center; line-height: 1;'>
    <img src='{logo_base64}' width='200' style='margin: 0; padding: 0; display: block;'>
</div>
""", unsafe_allow_html=True)

# Load OpenAI API key
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# Assistant ID (replace with your actual assistant ID)
ASSISTANT_ID = "asst_dslQlYKM5FYGVEWj8pu7afAt"

# Store thread across Streamlit sessions
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id

# Language toggle
language = st.radio("Choose language for the answer:", ["English", "Te Reo Māori", "Samoan"])

# Input box
st.write("Ask a medicine-related question below. Remember, answers come only from loaded Medsafe resources!")

user_question = st.text_input("Type your medicine question here:")

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
                    # Get latest assistant message
                    messages = client.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
                    latest = messages.data[0]
                    raw_answer = latest.content[0].text.value

                    # Strip citations
                    cleaned_answer = re.sub(r'【[^】]*】', '', raw_answer).strip()

                    # Translate if needed
                    if language == "Te Reo Māori":
                        translated = GoogleTranslator(source='auto', target='mi').translate(cleaned_answer)
                        st.write(translated)
                    elif language == "Samoan":
                        translated = GoogleTranslator(source='auto', target='sm').translate(cleaned_answer)
                        st.write(translated)
                    else:
                        st.write(cleaned_answer)
                else:
                    st.error("Sorry, the assistant failed to complete the request.")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Disclaimer
st.markdown("""
<div style='text-align: center; color: grey; margin-top: 30px;'>
Pill-AI is not a substitute for professional medical advice. Always consult a pharmacist or GP.
</div>
""", unsafe_allow_html=True)

import streamlit as st

# At the end of your app, below everything else
with st.expander("Privacy Policy – Click to expand"):
    st.markdown("""
    ### 🛡️ Pill-AI Privacy Policy (Prototype Version)

    Welcome to Pill-AI — your trusted medicines advisor. This is a prototype tool designed to help people learn about their medicines using trusted Medsafe resources.

    **We care about your privacy. Here's what you need to know:**

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
