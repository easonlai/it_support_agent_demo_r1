import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AzureOpenAIConfig:
    endpoint: str
    api_key: str
    api_version: str = "2025-03-01-preview"

@dataclass
class AgentConfig:
    name: str
    model: str
    port: int
    description: str

class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    
    # Agent Configurations
    SUPERVISOR_CONFIG = AgentConfig(
        name="Support Supervisor",
        model="o3-mini",  # Using o3-mini for reasoning tasks, please enter your model deployment name.
        port=8001,
        description="Routes and orchestrates IT support requests"
    )
    
    WINDOWS_CONFIG = AgentConfig(
        name="Windows Support",
        model="gpt-4o", # Using gpt-4o for generic tasks, please enter your model deployment name.
        port=8002,
        description="Handles Windows 11 related issues"
    )
    
    OFFICE_CONFIG = AgentConfig(
        name="Office Support", 
        model="gpt-4o", # Using gpt-4o for generic tasks, please enter your model deployment name.
        port=8003,
        description="Manages Microsoft Office problems"
    )
    
    HARDWARE_CONFIG = AgentConfig(
        name="Hardware Support",
        model="gpt-4o", # Using gpt-4o for generic tasks, please enter your model deployment name.
        port=8004,
        description="Addresses hardware-related queries"
    )
    
    # Knowledge Server Configuration
    KNOWLEDGE_SERVER_PORT = 8005
    KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
    
    # UI Configuration
    STREAMLIT_PORT = 8501
    
    @classmethod
    def get_azure_config(cls) -> AzureOpenAIConfig:
        return AzureOpenAIConfig(
            endpoint=cls.AZURE_OPENAI_ENDPOINT,
            api_key=cls.AZURE_OPENAI_API_KEY
        )