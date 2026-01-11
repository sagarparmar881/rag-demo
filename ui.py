import logging
from typing import Dict

import requests
import streamlit as st


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

APP_TITLE = "NIA – RAG Explorer"
APP_ICON = "🤖"

API_BASE_URL = "http://localhost:8000"
QUERY_ENDPOINT = f"{API_BASE_URL}/query"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

REQUEST_TIMEOUT = 30  # seconds


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("rag-ui")


# ------------------------------------------------------------------
# Streamlit Setup
# ------------------------------------------------------------------

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON)
st.title("NIA")
st.markdown("Ask questions based on your ingested knowledge base.")


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")

    if st.button("Check Backend Status"):
        try:
            response = requests.get(
                HEALTH_ENDPOINT,
                timeout=5,
            )

            if response.status_code == 200:
                st.success("Backend is healthy ✅")
            else:
                st.warning(f"Backend responded with {response.status_code}")

        except requests.exceptions.RequestException as exc:
            logger.error("Health check failed", exc_info=exc)
            st.error("Backend unreachable. Is the API running?")


# ------------------------------------------------------------------
# Session State
# ------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages: list[Dict[str, str]] = []


# ------------------------------------------------------------------
# Chat History
# ------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------------------------
# Chat Input
# ------------------------------------------------------------------

if prompt := st.chat_input("What would you like to know?"):
    logger.info("User query submitted")

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    QUERY_ENDPOINT,
                    json={"question": prompt},
                    timeout=REQUEST_TIMEOUT,
                )

                if response.status_code != 200:
                    logger.error(
                        "API error | status=%s body=%s",
                        response.status_code,
                        response.text,
                    )
                    st.error("Failed to get response from backend.")
                    st.stop()

                answer = response.json().get(
                    "answer",
                    "No answer returned by the backend.",
                )

                st.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })

                logger.info("Answer displayed successfully")

            except requests.exceptions.Timeout:
                logger.error("API request timed out")
                st.error("Request timed out. Please try again.")

            except requests.exceptions.RequestException as exc:
                logger.exception("API request failed")
                st.error("Connection failed. Please check backend logs.")
