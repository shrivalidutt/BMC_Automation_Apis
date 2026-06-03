# BMC Control-M Automation API Agent

A conversational AI agent that talks to the **BMC Control-M Automation API**.
It auto-generates LangChain tools from a YAML config (`agent/api_registry.yaml`) and uses a local Ollama LLM to understand user intent and interact with the API naturally.

*Note: The `api/` folder contains legacy code for a Flight Booking Simulator and is no longer used by this agent.*

---

## 🚀 Setup

### 1. Install System Prerequisites
* **Python**: Install Python 3.9 or higher.
* **Ollama**: Install Ollama (from `ollama.com`) and pull the required model:
  ```bash
  ollama pull llama3.2
  ```

### 2. Install Agent Dependencies
Use a **virtual environment** to install the Python dependencies.

```bash
cd agent
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup API Credentials
The agent needs credentials to log in to the Automation API.
1. In the `agent/` folder, copy the `.env.example` file to `.env`.
2. Open `.env` and fill in your BMC Automation API credentials:
   ```env
   AUTOMATION_USER=your_real_username
   AUTOMATION_PASS=your_real_password
   ```

---

## ▶️ Running the Agent

With your virtual environment activated from the `agent/` directory, simply run:
```bash
python agent.py
```
This will open the chat interface. You can now ask the agent to perform tasks, such as:
* "List all my database connection profiles"
* "Get agent parameters for agent X on server Y"
* "Set agent parameter Z to value V"

---

## ➕ Adding a New API

1. Add a new entry to `agent/api_registry.yaml` mapping to the Control-M endpoint.
2. The LangChain tool is auto-generated on the next run!
