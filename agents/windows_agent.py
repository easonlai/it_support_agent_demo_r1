import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from agents.base_agent import BaseAgent
from langchain.schema import SystemMessage, HumanMessage
from config.config import Config
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

class WindowsAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a specialized Windows 11 IT Support Agent. Your expertise includes:
        - Windows 11 installation and configuration
        - System troubleshooting and error resolution
        - Performance optimization
        - Security settings and updates
        - Hardware compatibility issues
        - Network connectivity problems
        
        Always provide clear, step-by-step solutions. If you cannot resolve an issue based on the knowledge base, 
        recommend contacting the IT Support Service Hotline."""
        
        super().__init__(Config.WINDOWS_CONFIG, system_prompt)
    
    def process_query(self, query: str, context: dict = None) -> dict:
        """Process Windows-related queries"""
        try:
            # Search knowledge base
            kb_results = self.search_knowledge_base('windows', query)
            
            # Prepare context with knowledge base results
            kb_context = "\n".join([
                f"KB Entry: {result.get('issue', '')} - Solution: {result.get('solution', '')}"
                for result in kb_results[:3]
            ]) if kb_results else "No specific knowledge base entries found."
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                User Query: {query}
                
                Knowledge Base Context:
                {kb_context}
                
                Please provide a helpful response for this Windows 11 issue.
                """)
            ]
            
            response = self._generate_response(messages)
            
            return {
                'agent': self.config.name,
                'response': response,
                'kb_results_count': len(kb_results),
                'confidence': 'high' if kb_results else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Windows agent error: {e}")
            return {
                'agent': self.config.name,
                'response': "I apologize, but I encountered an error. Please contact the IT Support Service Hotline.",
                'error': str(e)
            }

windows_agent = WindowsAgent()

@app.route('/process', methods=['POST'])
def process_query():
    """API endpoint to process Windows queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        
        result = windows_agent.process_query(query, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'agent': Config.WINDOWS_CONFIG.name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.WINDOWS_CONFIG.port, debug=True)