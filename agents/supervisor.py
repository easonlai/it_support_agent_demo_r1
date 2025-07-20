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
import requests
import json
import logging
from typing import List, Dict, Any

app = Flask(__name__)
logger = logging.getLogger(__name__)

class SupervisorAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are the IT Support Supervisor Agent. Your role is to:
        1. Analyze user queries and determine which specialized agents should handle them
        2. Route queries to appropriate sub-agents (Windows, Office, Hardware)
        3. Coordinate responses when multiple agents are needed
        4. Provide final synthesized responses to users
        5. Escalate to IT Support Service Hotline when issues cannot be resolved
        
        Available sub-agents:
        - Windows Support: Windows 11 issues, system problems, updates
        - Office Support: Microsoft Office applications, Office 365, productivity tools
        - Hardware Support: Computer hardware, peripherals, performance issues
        
        You must determine which agent(s) to consult and orchestrate the response."""
        
        super().__init__(Config.SUPERVISOR_CONFIG, system_prompt)
        self.sub_agents = {
            'windows': f"http://localhost:{Config.WINDOWS_CONFIG.port}",
            'office': f"http://localhost:{Config.OFFICE_CONFIG.port}",
            'hardware': f"http://localhost:{Config.HARDWARE_CONFIG.port}"
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine which agents should be involved"""
        messages = [
            SystemMessage(content=f"""Analyze the following IT support query and determine which specialized agents should handle it.
            
            Available agents:
            - windows: Windows 11 operating system issues
            - office: Microsoft Office applications and Office 365
            - hardware: Computer hardware and peripheral devices
            
            Return a JSON response with:
            - agents: list of agent names that should handle this query
            - reasoning: explanation of why these agents were selected
            - priority: primary agent if multiple agents are needed
            """),
            HumanMessage(content=f"Query: {query}")
        ]
        
        try:
            response = self._generate_response(messages, reasoning_effort="high")
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback analysis with improved keyword matching
                query_lower = query.lower()
                agents = []
                
                # Windows-related keywords
                windows_keywords = ['windows', 'system', 'boot', 'update', 'registry', 'startup', 'blue screen', 'bsod']
                # Office-related keywords (expanded)
                office_keywords = ['office', 'word', 'excel', 'powerpoint', 'outlook', 'teams', 'sharepoint', 
                                 'crashes', 'opening', 'large files', 'macro', 'vba', 'formatting', 'activation']
                # Hardware-related keywords
                hardware_keywords = ['hardware', 'printer', 'monitor', 'memory', 'disk', 'cpu', 'gpu', 
                                   'keyboard', 'mouse', 'performance', 'slow']
                
                if any(keyword in query_lower for keyword in windows_keywords):
                    agents.append('windows')
                if any(keyword in query_lower for keyword in office_keywords):
                    agents.append('office')
                if any(keyword in query_lower for keyword in hardware_keywords):
                    agents.append('hardware')
                
                # Special case: if Excel is mentioned, prioritize office agent
                if 'excel' in query_lower:
                    if 'office' not in agents:
                        agents.append('office')
                    priority = 'office'
                else:
                    priority = agents[0] if agents else 'windows'
                
                return {
                    'agents': agents if agents else ['windows'],  # Default to windows
                    'reasoning': f'Fallback keyword-based analysis. Keywords found: {[kw for kw in office_keywords + windows_keywords + hardware_keywords if kw in query_lower]}',
                    'priority': priority
                }
        except Exception as e:
            logger.error(f"Error in query analysis: {e}")
            return {
                'agents': ['windows'],
                'reasoning': 'Error in analysis, defaulting to Windows agent',
                'priority': 'windows'
            }
    
    def consult_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Consult a specific sub-agent"""
        try:
            url = f"{self.sub_agents[agent_name]}/process"
            response = requests.post(
                url, 
                json={'query': query}, 
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'agent': agent_name,
                    'response': f"Agent {agent_name} is currently unavailable.",
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error consulting {agent_name}: {e}")
            return {
                'agent': agent_name,
                'response': f"Unable to reach {agent_name} agent.",
                'error': str(e)
            }
    
    def synthesize_response(self, query: str, agent_responses: List[Dict[str, Any]]) -> str:
        """Synthesize final response from multiple agent inputs"""
        if not agent_responses:
            return "I apologize, but I was unable to process your request. Please contact the IT Support Service Hotline for assistance."
        
        # Prepare context from agent responses
        agent_context = "\n\n".join([
            f"{resp['agent']} Response: {resp.get('response', 'No response available')}"
            for resp in agent_responses
        ])
        
        messages = [
            SystemMessage(content="""Synthesize a comprehensive response based on the inputs from specialized IT support agents. 
            Create a unified, helpful response that addresses the user's query. If the agents couldn't resolve the issue, 
            recommend contacting the IT Support Service Hotline."""),
            HumanMessage(content=f"""
            Original User Query: {query}
            
            Agent Responses:
            {agent_context}
            
            Please provide a synthesized response that best addresses the user's needs.
            """)
        ]
        
        try:
            return self._generate_response(messages, reasoning_effort="high")
        except Exception as e:
            logger.error(f"Error synthesizing response: {e}")
            return "I apologize, but I encountered an error processing the responses. Please contact the IT Support Service Hotline for assistance."
    
    def process_query(self, query: str, context: dict = None) -> dict:
        """Main method to process user queries"""
        try:
            # Step 1: Analyze query
            analysis = self.analyze_query(query)
            
            # Step 2: Consult relevant agents
            agent_responses = []
            for agent_name in analysis.get('agents', []):
                if agent_name in self.sub_agents:
                    response = self.consult_agent(agent_name, query)
                    agent_responses.append(response)
            
            # Step 3: Synthesize final response
            final_response = self.synthesize_response(query, agent_responses)
            
            return {
                'analysis': analysis,
                'agent_responses': agent_responses,
                'final_response': final_response,
                'agents_consulted': [resp['agent'] for resp in agent_responses]
            }
            
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            return {
                'error': str(e),
                'final_response': "I apologize, but I encountered an error. Please contact the IT Support Service Hotline for assistance."
            }

supervisor_agent = SupervisorAgent()

@app.route('/process', methods=['POST'])
def process_query():
    """API endpoint to process user queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        
        result = supervisor_agent.process_query(query, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'agent': Config.SUPERVISOR_CONFIG.name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.SUPERVISOR_CONFIG.port, debug=True)