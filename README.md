
# IT Support Agent Demo

A multi-agent AI system designed to provide intelligent IT support using **Azure OpenAI**. This system uses **LangChain** as the multi-agent orchestration framework, and **Streamlit** to serve the web UI. It demonstrates how specialized AI agents can work together to resolve various IT issues including Windows 11, Microsoft Office, and hardware problems.

## 🎯 What This System Does

Imagine you have a team of IT specialists, each with their own expertise:
- **Supervisor**: The team leader who understands your problem and assigns it to the right specialist
- **Windows Expert**: Specializes in Windows 11 issues and system problems
- **Office Expert**: Handles Microsoft Office applications and productivity tools
- **Hardware Expert**: Deals with computer hardware and peripheral device issues

This system recreates this team digitally using AI agents that can collaborate to solve your IT problems!

## 🔧 How Multi-Agent Cooperation Works (In Simple Terms)

### The Magic Behind the Scenes

1. **You Ask a Question** 📝
   - You submit your IT problem through the web interface
   - Example: "Excel keeps crashing when I open large files"

2. **The Supervisor Analyzes** 🧠
   - The Supervisor Agent (like a smart receptionist) reads your question
   - It thinks: "This sounds like an Office problem, but could also be hardware-related"
   - It decides which specialist agents should help

3. **Knowledge Base Search** 📚
   - Each selected agent queries the Knowledge Server via REST API
   - The Office agent searches through Office-specific solutions
   - The Hardware agent checks if it's a performance/memory issue

4. **Agents Collaborate** 🤝
   - If multiple agents are needed, they each provide their expertise
   - The Office agent might say: "Excel crashes can be caused by corrupted add-ins"
   - The Hardware agent might add: "Large files need sufficient RAM and disk space"

5. **Supervisor Synthesizes** ✨
   - The Supervisor combines all the expert advice
   - It creates a comprehensive solution that addresses all aspects
   - Provides you with step-by-step instructions

6. **Escalation if Needed** ☎️
   - If no agent can solve the problem, the system recommends calling human IT support

### Real Example Flow

```
User: "My computer is running very slowly and Excel won't open"

Supervisor: "This needs both Windows and Office experts"
↓
Windows Agent: "Slow performance could be startup programs or disk issues"
Office Agent: "Excel won't open might be corrupted installation"
↓
Supervisor: "Here's a combined solution:
1. Check Task Manager for resource usage (Windows issue)
2. Disable unnecessary startup programs (Windows issue)  
3. Repair Office installation (Office issue)
4. Clear Excel cache (Office issue)"
```

## 🏗️ System Architecture

```
User Interface (Streamlit)
         ↓
Supervisor Agent (Port 8001)
    ↙    ↓    ↘
Windows   Office   Hardware
Agent     Agent    Agent
(8002)    (8003)   (8004)
    ↘      ↓      ↙
Knowledge Server (8005) *
         ↓
   Knowledge Bases
   (CSV files)

* Currently: REST API (simulating MCP architecture)
  Future: True MCP Server implementation
```

## 📋 Prerequisites

- Python 3.8 or higher
- Azure OpenAI account with API access
- Required Azure OpenAI models deployed:
  - `o3-mini` (for supervisor reasoning)
  - `gpt-4o` (for specialized agents)

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd it_support_agent_demo_r1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

Create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
```

### 3. Start All Services

```bash
python start_services.py
```

This will automatically start:
- Knowledge Server (Port 8005)
- Supervisor Agent (Port 8001)
- Windows Agent (Port 8002)
- Office Agent (Port 8003)
- Hardware Agent (Port 8004)
- Web UI (Port 8501)

### 4. Access the Application

Open your web browser and navigate to:
```
http://localhost:8501
```

## 🗂️ Project Structure

```
it_support_agent_demo_r1/
├── agents/                     # AI Agent implementations
│   ├── base_agent.py          # Common agent functionality
│   ├── supervisor.py          # Main orchestrator agent
│   ├── windows_agent.py       # Windows 11 specialist
│   ├── office_agent.py        # Microsoft Office specialist
│   └── hardware_agent.py      # Hardware specialist
├── config/                     # Configuration management
│   └── config.py              # Agent and Azure configurations
├── knowledge/                  # Knowledge bases (CSV files)
│   ├── windows_kb.csv         # Windows solutions database
│   ├── office_kb.csv          # Office solutions database
│   └── hardware_kb.csv        # Hardware solutions database
├── servers/                    # Backend services
│   └── knowledge_server.py    # Knowledge base REST API server
├── ui/                        # User interface
│   └── app.py                 # Streamlit web application
├── start_services.py          # Service orchestration script
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

### Agent Configuration

Each agent can be configured in `config/config.py`:

```python
SUPERVISOR_CONFIG = AgentConfig(
    name="Support Supervisor",
    model="o3-mini",      # Azure OpenAI deployment name
    port=8001,
    description="Routes and orchestrates IT support requests"
)
```

### Knowledge Base Customization

**Important Note**: The knowledge server in this demo is a custom Flask-based REST API server that **simulates** MCP-like architecture but is not a true Model Context Protocol (MCP) server. It provides simple HTTP endpoints for searching CSV-based knowledge bases.

**🚀 Future Development**: True MCP server implementation is planned for future versions, which would provide:
- Standardized JSON-RPC protocol communication
- Dynamic resource and tool discovery
- Native LLM integration capabilities
- Industry-standard context sharing mechanisms

For now, the REST API approach effectively demonstrates the multi-agent architecture and knowledge base integration patterns.

Knowledge bases are stored as CSV files in the `knowledge/` directory with the following structure:

**Windows KB Example:**
```csv
issue,category,solution,severity
Windows 11 won't boot,Boot Issues,"1. Press F8 during startup...",High
Blue Screen of Death,System Crashes,"1. Note error code...",Critical
```

**Office KB Example:**
```csv
application,issue,solution,category,severity
Excel,Crashes when opening large files,"1. Increase virtual memory...",Performance,Medium
Word,Document won't save,"1. Check file permissions...",File Access,Low
```

## 🎮 Usage Examples

### Example 1: Windows Performance Issue
**User Input:** "My Windows 11 computer is running very slowly"

**System Response:**
- Supervisor routes to Windows Agent
- Windows Agent searches performance-related solutions
- Provides step-by-step optimization guide

### Example 2: Office Application Problem
**User Input:** "PowerPoint keeps crashing during presentations"

**System Response:**
- Supervisor routes to Office Agent
- Office Agent finds PowerPoint-specific solutions
- Provides troubleshooting steps and prevention tips

### Example 3: Complex Multi-Domain Issue
**User Input:** "Excel is slow and my computer crashes when working with large spreadsheets"

**System Response:**
- Supervisor identifies need for both Office and Hardware agents
- Office Agent addresses Excel optimization
- Hardware Agent addresses system performance
- Supervisor synthesizes comprehensive solution

## 🔍 API Endpoints

### Supervisor Agent (Port 8001)
- `POST /process` - Main query processing endpoint
- `GET /health` - Health check

### Specialized Agents (Ports 8002-8004)
- `POST /process` - Process domain-specific queries
- `GET /health` - Agent health status

### Knowledge Server (Port 8005)
- `POST /search/{kb_name}` - Search specific knowledge base
- `GET /health` - Server health and knowledge base status
- `GET /knowledge-bases` - List available knowledge bases

## 🛠️ Troubleshooting

### Common Issues

1. **Services won't start**
   - Check if ports are already in use
   - Verify Azure OpenAI credentials
   - Ensure all dependencies are installed

2. **Knowledge base not found**
   - Verify CSV files exist in `knowledge/` directory
   - Check file permissions and format

3. **Azure OpenAI errors**
   - Verify API key and endpoint configuration
   - Check model deployment names match configuration
   - Ensure quota limits aren't exceeded

### Monitoring

Each service provides health endpoints for monitoring:
```bash
# Check all services
curl http://localhost:8001/health  # Supervisor
curl http://localhost:8002/health  # Windows Agent
curl http://localhost:8003/health  # Office Agent
curl http://localhost:8004/health  # Hardware Agent
curl http://localhost:8005/health  # Knowledge Server
```

## 🚧 Development

### Current Architecture vs. Future MCP Implementation

**Current Implementation (v1.0)**:
- Custom Flask REST API for knowledge base access
- HTTP endpoints with JSON payloads
- Simulates distributed knowledge server architecture
- Demonstrates multi-agent cooperation patterns

**Planned MCP Implementation (Future)**:
- True Model Context Protocol (MCP) server compliance
- Standardized JSON-RPC protocol
- Dynamic resource discovery and tool registration  
- Native integration with LLM frameworks
- Enhanced context sharing and state management

The current REST API approach effectively demonstrates the system architecture and provides a foundation for future MCP migration.

### Adding New Agents

1. Create new agent class inheriting from `BaseAgent`
2. Add configuration in `config/config.py`
3. Create corresponding knowledge base CSV
4. Update supervisor routing logic
5. Add startup logic in `start_services.py`

### Extending Knowledge Bases

1. Add new CSV files in `knowledge/` directory
2. Update `knowledge_server.py` to load new knowledge base
3. Modify relevant agents to search new knowledge base

## 📈 Performance Considerations

- **Concurrent Processing**: Agents process queries in parallel when possible
- **Caching**: Knowledge bases are loaded into memory for fast access
- **Timeout Management**: All API calls have timeout configurations
- **Resource Management**: Each agent runs as a separate process

## 🔒 Security

- API keys are managed through environment variables
- No sensitive data is stored in knowledge bases
- All inter-service communication uses localhost
- Input validation on all API endpoints

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request

## 📞 Support

If the AI agents cannot resolve your issue, the system will recommend contacting the IT Support Service Hotline for human assistance.

## 📄 License

This project is for demonstration purposes. Please review and comply with Azure OpenAI usage terms and conditions.

---

*Built with ❤️ using Azure OpenAI, LangChain, Flask, and Streamlit*
