import base64
import os
import streamlit as st
import requests
import json
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL")
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
CLEAR_MEMORY_ENDPOINT = f"{API_BASE_URL}/clear_memory"
GET_HISTORY_ENDPOINT = f"{API_BASE_URL}/get_chat_history"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def send_chat_message(user_message: str) -> Dict:
    """Send user message to chat endpoint and return response"""
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"chat": user_message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with API: {str(e)}")
        return None

def clear_chat_memory():
    """Clear the chat memory via API"""
    try:
        response = requests.get(CLEAR_MEMORY_ENDPOINT)
        response.raise_for_status()
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.success("Chat memory cleared successfully!")
    except requests.exceptions.RequestException as e:
        st.error(f"Error clearing chat memory: {str(e)}")

def get_chat_history() -> List[Dict]:
    """Get the chat history from API"""
    try:
        response = requests.get(GET_HISTORY_ENDPOINT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting chat history: {str(e)}")
        return []

def create_pdf_download_link(file_path: str, display_text: str) -> str:
    """Create a clickable link to download PDF"""
    try:
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        b64 = base64.b64encode(pdf_data).decode()
        return f'<a href="data:application/pdf;base64,{b64}" download="{display_text}" style="color: inherit; text-decoration: none; font-weight: bold;">{display_text}</a>'
    except Exception as e:
        st.error(f"Error creating PDF download link: {str(e)}")
        return display_text  # Return plain text if error occurs

def display_chat_message(role: str, content: str, relevant_files: List[str] = None):
    """Display a chat message in the UI with clickable document filenames"""
    with st.chat_message(role):
        st.markdown(content, unsafe_allow_html=True)
        
        if relevant_files and role == "assistant":
            st.markdown("**Relevant Documents:**")
            for i, file in enumerate(relevant_files):
                # Extract just the filename for display
                filename = file.split("\\")[-1] if "\\" in file else file
                
                # Create clickable filename that downloads PDF
                clickable_filename = create_pdf_download_link(file, filename)
                st.markdown(clickable_filename, unsafe_allow_html=True)

def main():
    st.title("CelcomDigi Chat Assistant")
    st.caption("Ask me about CelcomDigi products and services")

    # Sidebar with clear memory button
    with st.sidebar:
        st.header("Chat Controls")
        if st.button("Clear Chat Memory"):
            clear_chat_memory()

    # Display chat messages from history
    for message in st.session_state.messages:
        display_chat_message(
            role=message["role"],
            content=message["content"],
            relevant_files=message.get("relevant_files", [])
        )

    # Chat input
    if prompt := st.chat_input("Ask me about CelcomDigi offerings..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "relevant_files": []})
        display_chat_message("user", prompt)
        
        # Get response from API
        api_response = send_chat_message(prompt)
        
        if api_response:
            # Add assistant response to chat history
            assistant_response = api_response.get("response", "Sorry, I couldn't process your request.")
            relevant_files = api_response.get("relevant_files", [])
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "relevant_files": relevant_files
            })
            
            display_chat_message("assistant", assistant_response, relevant_files)
            
            # Update chat history from API
            st.session_state.chat_history = get_chat_history()

if __name__ == "__main__":
    main()