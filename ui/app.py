"""Streamlit chat UI for QABuddy.ai."""
import os

import requests
import streamlit as st

API_BASE = os.environ.get("QABUDDY_API_URL", "http://localhost:8000")

st.set_page_config(page_title="QABuddy.ai", page_icon="🧪", layout="wide")
st.title("🧪 QABuddy.ai")
st.caption("Ask anything about your Selenium/Playwright framework, test cases, JIRA tickets, or QA docs.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander(f"📎 {len(msg['citations'])} source(s)"):
                for c in msg["citations"]:
                    st.markdown(f"**[{c['source_type']}]** `{c['source_file']}`")
                    st.text(c.get("text_preview", "")[:300])

# Input
if prompt := st.chat_input("Ask QABuddy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/chat",
                    json={"question": prompt, "top_k": 8},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["answer"]
                citations = data.get("citations", [])
            except Exception as e:
                answer = f"Error connecting to QABuddy API: {e}"
                citations = []

        st.markdown(answer)
        if citations:
            with st.expander(f"📎 {len(citations)} source(s)"):
                for c in citations:
                    st.markdown(f"**[{c['source_type']}]** `{c['source_file']}`")
                    st.text(c.get("text_preview", "")[:300])

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "citations": citations}
    )
