# ✈️ Flight Booking Agent — LangChain + Ollama

A conversational AI agent that talks to the Flight Booking Simulator API.
It auto-generates LangChain tools from a YAML config and uses a local Ollama LLM to understand user intent and interact with the API naturally.

---

## 📁 Project Structure

```
flight-agent/
├── api_registry.yaml     ← All API definitions (endpoints, params, descriptions)
├── tool_generator.py     ← Reads YAML → auto-generates LangChain Tool objects
├── agent.py              ← Main agent: Ollama LLM + ReAct loop + chat CLI
├── requirements.txt
└── README.md
```

---

## ⚙️ How It Works

```
api_registry.yaml
      │
      ▼
tool_generator.py  ──→  Generates one LangChain Tool per API
      │
      ▼
agent.py (LangChain ReAct Agent)
      │
      ├── Understands user intent using Ollama LLM
      ├── Confirms which tool it wants to use with the user
      ├── Collects required + optional parameters (never assumes values)
      ├── Calls the tool (which hits the real Node.js API)
      └── Returns response in natural language
```

### The 4 Behaviour Rules
1. **Confirm first** — tells the user which API it will call and asks yes/no
2. **Collect params** — asks for required params, then optional ones
3. **Never assume** — will not invent flight IDs, passenger IDs, or any values
4. **Natural language response** — interprets JSON and explains it in plain English

---

## 🚀 Setup

### Step 1 — Start the Flight API
Make sure the Node.js server is running:
```bash
cd ../flight-booking-simulator
npm start
# → http://localhost:3000/api
```

### Step 2 — Install Ollama
Download from https://ollama.com and then pull a model:
```bash
ollama pull llama3.2
```

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the agent
```bash
python agent.py
```

---

## 💬 Example Conversations

### Booking a flight
```
You: I want to book a flight

🤖 Assistant: I can help you book a flight using the "Create a Flight Booking" tool.
              Shall I proceed? (yes/no)

You: yes

🤖 Assistant: Great! I'll need a few details:
              - What is the Flight ID you want to book? (e.g. FL001)
              - What is your Passenger ID?
              - Which seat class would you prefer: economy or business?

You: FL002, P001, economy

🤖 Assistant: Would you also like to add:
              - A special meal preference? (e.g. vegetarian, vegan, halal)
              - Extra baggage? (adds ₹1,500 to the fare)

You: vegetarian meal, no extra baggage

🤖 Assistant: ✅ Booking confirmed! Here are your details:
              Booking ID  : BK003
              Flight      : 6E-301 (IndiGo) — BOM → BLR
              Seat        : 22D (Economy)
              Meal        : Vegetarian
              Total Fare  : ₹3,200
              Status      : Confirmed
```

### Searching flights
```
You: Show me flights from Delhi to Dubai

🤖 Assistant: I'll use the Search Flights tool to find DEL → DXB flights.
              Shall I proceed? (yes/no)

You: yes

🤖 Assistant: Do you want to filter by date, airline, seat class, or price? Or should I show all available flights?

You: just show all

🤖 Assistant: Found 1 flight from Delhi (DEL) to Dubai (DXB):
              • UK-955 (Vistara) — Departs Apr 11 at 2:15 AM, arrives 4:30 AM
                Economy: ₹18,000  |  Business: ₹55,000  |  60 seats available
```

---

## 🔧 Customising

### Change the Ollama model
In `agent.py`, update:
```python
OLLAMA_MODEL = "llama3.2"   # Change to mistral, gemma3, phi4, etc.
```

### Add a new API
Just add a new entry in `api_registry.yaml` following the existing format — the tool is auto-generated, no Python changes needed.

### Hide agent reasoning steps
In `agent.py`, set:
```python
verbose=False
```

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Ollama (local) — llama3.2 |
| Agent framework | LangChain ReAct Agent |
| Tool generation | Auto-generated from YAML |
| API calls | Python `requests` |
| Backend API | Node.js + Express |
| Config | YAML |
