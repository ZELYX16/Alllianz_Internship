import streamlit as st
import requests

API_URL = "http://backend:8000"

st.set_page_config(page_title="Tokenizer App", layout="wide")
st.title("AI Tokenizer & Cost Calculator")

# Fetch available models from the backend
@st.cache_data(ttl=3600) # Cache the available models .
def fetch_models():
    try:
        response = requests.get(f"{API_URL}/models")
        if response.status_code == 200:
            return response.json().get("models", [])
    except Exception:
        return []
    return []

available_models = fetch_models()

# --- Tokenization Section ---
st.subheader("Process New Text")

col1, col2 = st.columns([1, 3])

with col1:
    if available_models:
        selected_model = st.selectbox("Select Model", available_models)
    else:
        st.error("Could not load models from backend.")
        selected_model = None

with col2:
    user_text = st.text_area("Enter your text here:", height=150)

if st.button("Tokenize & Calculate"):
    if user_text.strip() and selected_model:
        payload = {"text": user_text, "model": selected_model}
        response = requests.post(f"{API_URL}/tokenize", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"**Model:** {data['model']} | **Tokens:** {data['token_count']} | **Estimated Input Cost:** ${data['cost']:.8f}")
        else:
            st.error(f"Error: {response.text}")
    else:
        st.warning("Please ensure you have entered text and selected a model.")

st.divider()

# --- History Section (CRUD) ---
st.subheader("Run History")

if st.button("Refresh History"):
    st.rerun()

try:
    history_response = requests.get(f"{API_URL}/history")
    if history_response.status_code == 200:
        history = history_response.json().get("history", [])
        
        if not history:
            st.info("No history found.")
        else:
            for item in history:
                hc1, hc2, hc3, hc4 = st.columns([1, 3, 2, 1])
                with hc1:
                    st.write(f"**ID {item['id']}**")
                with hc2:
                    st.write(f"{item['model']}: {item['text']}")
                with hc3:
                    st.write(f"Tokens: {item['token_count']} | Cost: ${item['cost']:.8f}")
                with hc4:
                    if st.button("Delete", key=f"del_{item['id']}"):
                        requests.delete(f"{API_URL}/history/{item['id']}")
                        st.rerun()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to backend.")