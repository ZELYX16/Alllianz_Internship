import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Structured Research Agent", page_icon="🤖")
st.title("🤖 Chat-Based Research Assistant")

# Initialize message state inside Streamlit's runtime memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render conversation logs automatically upon state refreshes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture new input
if user_query := st.chat_input("Ask a question about your documents..."):
    
    with st.chat_message("user"):
        st.markdown(user_query)
        
    # Prepare payload with explicit roles matching backend expectations
    payload = {
        "query": user_query,
        "chat_history": st.session_state.messages
    }
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.spinner("Executing agent reasoning loop..."):
        try:
            res = requests.post(f"{BACKEND_URL}/chat", json=payload)
            
            if res.status_code == 200:
                backend_response = res.json().get("answer", "No answer processed.")
            else:
                backend_response = f"Backend Error Code: {res.status_code}"
                
            with st.chat_message("assistant"):
                st.markdown(backend_response)
                
            st.session_state.messages.append({"role": "assistant", "content": backend_response})
            
        except requests.exceptions.ConnectionError:
            error_text = "Connection Error: Please verify that your Uvicorn service is actively listening on port 8000."
            st.error(error_text)
            st.session_state.messages.append({"role": "assistant", "content": error_text})