import streamlit as st
import requests
import time
from typing import Dict, List

# Configuration
BACKEND_URL = "http://127.0.0.1:8000/api"  # Using 127.0.0.1 is more reliable than localhost on some Windows systems

def get_available_models() -> List[Dict]:
    try:
        response = requests.get(
            f"{BACKEND_URL}/models",
            timeout=5
        )
        response.raise_for_status()
        return response.json().get("models", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get models: {str(e)}")
        return [
            {"id": "llama3.2-vision:11b", "name": "Llama3.2 Vision (11B)"},
            {"id": "qwen2.5-coder:0.5b", "name": "Qwen2.5 Coder (0.5B)"}
        ]

def chat_completion(model: str, messages: List[Dict], temperature: float, max_tokens: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            timeout=600  # Longer timeout for LLM responses
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_msg = f"""
        Connection Error: {str(e)}
        
        Troubleshooting steps:
        1. Ensure FastAPI backend is running (python main.py)
        2. Verify Ollama is running (ollama serve)
        3. Check ports:
           - FastAPI: 8000
           - Ollama: 11434
        4. Try refreshing the page
        """
        return error_msg

def check_backend_health():
    try:
        response = requests.get(
            f"{BACKEND_URL.replace('/api', '')}/health",
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    st.title("JARVIS :)")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "model" not in st.session_state:
        st.session_state.model = "llama3.2-vision:11b"
    
    # Show warning if backend isn't available
    if not check_backend_health():
        st.warning("Backend service not available. Please ensure the FastAPI server is running.")
    
    # Sidebar for model selection and settings
    with st.sidebar:
        st.header("Settings")
        
        # Model selection
        models = get_available_models()
        model_names = [m["name"] for m in models]
        model_ids = [m["id"] for m in models]
        
        selected_model_name = st.selectbox(
            "Select Model",
            model_names,
            index=model_ids.index(st.session_state.model) if st.session_state.model in model_ids else 0
        )
        
        st.session_state.model = model_ids[model_names.index(selected_model_name)]
        
        # Parameters
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 128, 4096, 1024, 128)
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
        
        # Backend status indicator
        st.markdown("---")
        if check_backend_health():
            st.success("Backend connected")
        else:
            st.error("Backend disconnected")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Prepare messages for the API (last 6 messages for context)
            api_messages = [{"role": "system", "content": "You are a helpful assistant."}]
            api_messages.extend(st.session_state.messages[-6:])
            
            # Get response from backend with loading indicator
            with st.spinner("Thinking..."):
                response = chat_completion(
                    model=st.session_state.model,
                    messages=api_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            full_response = response
            message_placeholder.markdown(full_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()