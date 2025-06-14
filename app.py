import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Set Streamlit page config
st.set_page_config(page_title="Pill-AI", page_icon="💊", layout="centered")

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
ASSISTANT_ID = "asst_3xS1vLEMnQyFqNXLTblUdbWS"

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
