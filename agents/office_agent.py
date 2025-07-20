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

class OfficeAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a specialized Microsoft Office IT Support Agent. Your expertise includes:
        - Microsoft Word, Excel, PowerPoint, Outlook issues
        - Office 365 and subscription problems
        - File compatibility and format issues
        - Macro and VBA troubleshooting
        - Office installation and activation
        - SharePoint and Teams integration
        
        Provide clear, actionable solutions with specific steps when possible."""
        
        super().__init__(Config.OFFICE_CONFIG, system_prompt)
    
    def process_query(self, query: str, context: dict = None) -> dict:
        """Process Office-related queries"""
        try:
            logger.info(f"Office agent processing query: '{query}'")
            
            # Search knowledge base
            kb_results = self.search_knowledge_base('office', query)
            logger.info(f"Knowledge base search returned {len(kb_results)} results")
            
            # Log KB results for debugging
            if kb_results:
                kb_sample = [f"{r.get('application')}: {r.get('issue')}" for r in kb_results[:2]]
                logger.info(f"KB Results: {kb_sample}")
            else:
                logger.warning("No knowledge base results found - this might indicate a search issue")
            
            # Prepare context with knowledge base results
            kb_context = "\n".join([
                f"KB Entry: {result.get('application', '')} - {result.get('issue', '')} - Solution: {result.get('solution', '')}"
                for result in kb_results[:3]
            ]) if kb_results else "No specific knowledge base entries found."
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                User Query: {query}
                
                Knowledge Base Context:
                {kb_context}
                
                Please provide a helpful response for this Microsoft Office issue.
                """)
            ]
            
            response = self._generate_response(messages)
            
            result = {
                'agent': self.config.name,
                'response': response,
                'kb_results_count': len(kb_results),
                'confidence': 'high' if kb_results else 'medium'
            }
            
            logger.info(f"Office agent returning result with {result['kb_results_count']} KB results")
            return result
            
        except Exception as e:
            logger.error(f"Office agent error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'agent': self.config.name,
                'response': "I apologize, but I encountered an error. Please contact the IT Support Service Hotline.",
                'error': str(e),
                'kb_results_count': 0
            }

office_agent = OfficeAgent()

@app.route('/process', methods=['POST'])
def process_query():
    """API endpoint to process Office queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        
        result = office_agent.process_query(query, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'agent': Config.OFFICE_CONFIG.name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.OFFICE_CONFIG.port, debug=True)