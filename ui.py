import streamlit as st
import requests
import time

# Define the Flask API URL
FLASK_API_URL = "http://127.0.0.1:5001/start"

st.title("🎙️ AI Voice Assistant")
st.markdown("Click the button to start speaking and let AI respond.")

if st.button("Start Talking"):
    with st.spinner("Connecting to the AI agent..."):
        try:
            response = requests.get(FLASK_API_URL)
            if response.status_code == 200:
                st.success("Speech conversation started! Speak into the microphone.")
            else:
                st.error("Failed to start the conversation.")
        except requests.exceptions.RequestException:
            st.error("Could not connect to the AI agent. Make sure Flask is running.")

st.write("🎤 Speak into your microphone, and AI will listen, respond, and speak back.")

