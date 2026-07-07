import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Local LLM Playground",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Local LLM Playground")


# ----------------------------------------------------------------------
# Sidebar Controls
# ----------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration")

# --- NEW: Model Selection Dropdown ---
selected_model = st.sidebar.selectbox(
    "Select Model",
    options=["mistral", "coder-bot"],
    index=0,
    help="Choose which local model to run."
)

temperature = st.sidebar.slider(
    "Temperature", min_value=0.0, max_value=1.5, value=0.7, step=0.1,
    help="Higher values make output more creative; lower values make it more deterministic."
)

st.sidebar.subheader("Advanced Settings")

num_ctx = st.sidebar.number_input(
    "Context Window Size (num_ctx)", 
    min_value=10, 
    max_value=32768, 
    value=2048, 
    step=512,
    help="Type a custom number or use the arrows. Higher uses more RAM/VRAM."
)

repeat_penalty = st.sidebar.slider(
    "Repeat Penalty", min_value=1.0, max_value=2.0, value=1.1, step=0.05,
    help="Prevents the model from repeating the same words. 1.0 means no penalty."
)

top_k = st.sidebar.slider(
    "Top-K", min_value=1, max_value=100, value=40, step=1,
    help="Limits the model to picking from the top K most probable next words."
)

top_p = st.sidebar.slider(
    "Top-P (Nucleus Sampling)", min_value=0.0, max_value=1.0, value=0.9, step=0.05,
    help="Limits the vocabulary pool to words whose combined probability adds up to P."
)

st.sidebar.divider()
st.sidebar.markdown("### 💡 Experiment Tips")
st.sidebar.info(
    "- **Coding/Math:** Set Temp to **0.0 - 0.2**\n"
    "- **General Chat:** Set Temp to **0.7**\n"
    "- **Creative Writing:** Set Temp to **1.0+**"
)

# ----------------------------------------------------------------------
# Main UI Interface
# ----------------------------------------------------------------------
user_prompt = st.text_area(
    "Enter your prompt:",
    placeholder="e.g., Write a python script to reverse a string...",
    height=150
)

if st.button("🚀 Generate Response", type="primary"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        # Spinner now dynamically shows which model is thinking
        with st.spinner(f"Sending request to FastAPI backend running {selected_model}..."):
            
            # Prepare payload for FastAPI 
            payload = {
                "prompt": user_prompt,
                "model": selected_model,  # <-- Now uses the dropdown selection
                "temperature": temperature,
                "num_predict": 512,
                "num_ctx": num_ctx,
                "repeat_penalty": repeat_penalty,
                "top_k": top_k,
                "top_p": top_p
            }
            
            try:
                res = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=180)
                
                if res.status_code == 200:
                    result = res.json()
                    
                    st.subheader("📝 Response")
                    st.write(result["response"])

                    # Metrics Logging Dashboard
                    st.divider()
                    st.subheader("📊 Performance Metrics")
                    
                    m = result["metrics"]
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(label="Input Tokens", value=m["input_tokens"])
                    with col2:
                        st.metric(label="Output Tokens", value=m["output_tokens"])
                    with col3:
                        st.metric(label="Elapsed Time", value=f"{m['elapsed_time']:.2f}s", delta=f"{m['tps']:.1f} tok/s")
                    with col4:
                        st.metric(label="Inference Cost", value=f"${m['cost']:.2f}", delta="Local HW", delta_color="off")
                else:
                    st.error(f"Backend returned an error ({res.status_code}): {res.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to communicate with FastAPI backend. Ensure it is running on port 8000. Error: {e}")