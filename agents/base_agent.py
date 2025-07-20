import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import requests
import json
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, config, system_prompt: str):
        self.config = config
        self.system_prompt = system_prompt
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        azure_config = Config.get_azure_config()
        return AzureChatOpenAI(
            azure_endpoint=azure_config.endpoint,
            api_key=azure_config.api_key,
            api_version=azure_config.api_version,
            azure_deployment=self.config.model
        )
    
    def search_knowledge_base(self, kb_name: str, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base via MCP server"""
        try:
            url = f"http://localhost:{Config.KNOWLEDGE_SERVER_PORT}/search/{kb_name}"
            logger.info(f"Searching knowledge base '{kb_name}' with query: '{query}'")
            logger.info(f"Knowledge server URL: {url}")
            
            response = requests.post(url, json={'query': query, 'limit': 5}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                logger.info(f"Knowledge search successful: {len(results)} results")
                return results
            else:
                logger.error(f"Knowledge search failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to knowledge server: {e}")
            return []
        except requests.exceptions.Timeout as e:
            logger.error(f"Knowledge server timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query and return response"""
        pass
    
    def _generate_response(self, messages: List, reasoning_effort: str = "medium") -> str:
        """Generate response using Azure OpenAI"""
        try:
            # Handle reasoning effort for o3-mini model
            if self.config.model == "o3-mini":
                response = self.client.invoke(
                    messages,
                    model_kwargs={"reasoning_effort": reasoning_effort}
                )
            else:
                response = self.client.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error processing your request. Please contact the IT Support Service Hotline for assistance."