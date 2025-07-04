import streamlit as st
import openai
import os
import re
import base64
from deep_translator import GoogleTranslator

# Page config
st.set_page_config(page_title="Pill-AIv2", page_icon="💊", layout="centered")

# Show welcome popup once per session
if "show_welcome" not in st.session_state:
    st.session_state["show_welcome"] = True

if st.session_state["show_welcome"]:
    st.markdown("""
        <div style='
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: #e0f2ff;
            border: 1px solid #90cdf4;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            font-family: "Segoe UI", sans-serif;
            text-align: center;
        '>
            <strong style='font-size: 1.2em;'>👋 Hello, welcome to Pill-AI!</strong><br>
            <span style='margin-top: 5px;'>This is a prototype assistant to help you understand medicines using Medsafe info from NZ.</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.button("OK, got it!", key="dismiss_welcome"):
        st.session_state["show_welcome"] = False
    st.markdown("</div>", unsafe_allow_html=True)

# Continue with the rest of your app logic below this point...
# (the rest of your Streamlit UI code would follow here)
