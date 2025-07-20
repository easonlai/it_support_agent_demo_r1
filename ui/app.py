import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import requests
import json
from datetime import datetime
import time
from config.config import Config

# Configure page
st.set_page_config(
    page_title="IT Support Agent",
    page_icon="🛠️",
    layout="wide"
)

# Initialize session state
if 'messages' in st.session_state:
    pass
else:
    st.session_state.messages = []

def call_supervisor(query: str) -> dict:
    """Call the supervisor agent API"""
    try:
        response = requests.post(
            f"http://localhost:{Config.SUPERVISOR_CONFIG.port}/process",
            json={'query': query},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f"API Error: {response.status_code}",
                'final_response': "Service temporarily unavailable. Please try again later."
            }
    
    except requests.exceptions.Timeout:
        return {
            'error': 'Request timeout',
            'final_response': "Request timed out. Please try a simpler query or contact IT Support Service Hotline."
        }
    except Exception as e:
        return {
            'error': str(e),
            'final_response': "Unable to connect to support system. Please contact IT Support Service Hotline."
        }

def display_process_details(result: dict):
    """Display the processing details with expandable sections"""
    
    # Query Analysis
    if 'analysis' in result:
        with st.expander("🔍 **Query Analysis**", expanded=False):
            analysis = result['analysis']
            st.write("**Reasoning:**", analysis.get('reasoning', 'N/A'))
            st.write("**Agents Selected:**", ", ".join(analysis.get('agents', [])))
            if 'priority' in analysis:
                st.write("**Primary Agent:**", analysis['priority'])
    
    # Agent Communications
    if 'agent_responses' in result and result['agent_responses']:
        with st.expander("🤖 **Agent Communications**", expanded=False):
            for i, response in enumerate(result['agent_responses']):
                st.subheader(f"{response.get('agent', f'Agent {i+1}')}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Response:**")
                    st.info(response.get('response', 'No response'))
                
                with col2:
                    if 'kb_results_count' in response:
                        st.metric("KB Results", response['kb_results_count'])
                    if 'confidence' in response:
                        confidence_color = {
                            'high': '🟢', 
                            'medium': '🟡', 
                            'low': '🔴'
                        }.get(response['confidence'], '⚪')
                        st.write(f"**Confidence:** {confidence_color} {response['confidence'].title()}")
                
                if i < len(result['agent_responses']) - 1:
                    st.divider()

def main():
    # Header
    st.title("🛠️ IT Support Agent")
    st.markdown("*Powered by Azure OpenAI with Multi-Agent Architecture in LangChain*")
    
    # Sidebar with system status
    with st.sidebar:
        st.header("System Status")
        
        # Check agent health
        agents = [
            ("Supervisor", Config.SUPERVISOR_CONFIG.port),
            ("Windows Support", Config.WINDOWS_CONFIG.port),
            ("Office Support", Config.OFFICE_CONFIG.port),
            ("Hardware Support", Config.HARDWARE_CONFIG.port),
            ("Knowledge Server", Config.KNOWLEDGE_SERVER_PORT)
        ]
        
        for name, port in agents:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ {name}")
                else:
                    st.error(f"❌ {name}")
            except:
                st.error(f"❌ {name}")
        
        st.divider()
        st.markdown("### How to Use")
        st.markdown("""
        1. **Ask your question** in the chat
        2. **View the analysis** process 
        3. **See agent communications**
        4. **Get your final answer**
        
        **Example queries:**
        - "Windows 11 won't boot"
        - "Excel crashes when opening large files"
        - "Printer not responding"
        """)
    
    # Chat interface
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show process details for assistant messages
            if message["role"] == "assistant" and "process_details" in message:
                display_process_details(message["process_details"])
    
    # Chat input
    if prompt := st.chat_input("Describe your IT issue..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with supervisor agent
        with st.chat_message("assistant"):
            # Show processing indicator
            with st.status("Processing your request...", expanded=True) as status:
                st.write("🔍 Analyzing your query...")
                time.sleep(1)
                
                st.write("🤖 Consulting specialized agents...")
                result = call_supervisor(prompt)
                
                st.write("🔄 Synthesizing response...")
                time.sleep(1)
                
                status.update(label="✅ Request processed!", state="complete")
            
            # Display final response
            final_response = result.get('final_response', 'Unable to process request.')
            st.markdown(final_response)
            
            # Display process details
            display_process_details(result)
            
            # Add assistant message to session state
            st.session_state.messages.append({
                "role": "assistant", 
                "content": final_response,
                "process_details": result
            })
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "If you cannot find a solution, please contact the IT Support Service Hotline: 📞 +852-1234-IT-HELP"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()