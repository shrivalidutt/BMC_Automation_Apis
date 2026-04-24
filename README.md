
---

## 🚀 Setup (one time)

### 1. Install API dependencies
```bash
cd api
npm install
```

### 2. Install Agent dependencies

Use a **virtual environment** so packages are not installed into Homebrew’s Python (PEP 668 blocks `pip install` there).

```bash
cd agent
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If `venv/` already exists from the repo, skip `python3 -m venv venv` and only run `source venv/bin/activate` then `pip install -r requirements.txt` if anything is missing.

### 3. Pull an Ollama model (if not done yet)
```bash
ollama pull llama3.2
```

---

## ▶️ Running the full stack

Open **two terminals**:

**Terminal 1 — Start the API:**
```bash
cd api
npm start
# → Running on http://localhost:3000
```

**Terminal 2 — Start the Agent:**
```bash
cd agent
source venv/bin/activate   # so `python` uses the venv, not system Python
python agent.py            # or: ./venv/bin/python agent.py without activating
# → Chat interface opens
```

---

## 🔁 How They Connect

```
You (chat)
   │
   ▼
agent/agent.py          ← LangChain ReAct agent, powered by Ollama
   │
   ├── reads api_registry.yaml   ← single config describing all APIs
   │
   ├── tool_generator.py         ← auto-creates one Tool per API
   │
   ▼
HTTP requests → api/index.js     ← Node.js Express server
                    │
                    └── src/data/db.js   ← in-memory mock database
```

The agent reads `api_registry.yaml`, generates LangChain tools automatically, then uses Ollama to understand what the user wants, confirm intent, collect parameters, call the real API, and reply in natural language.

---

## 💬 Example Session

```
You: I want to book a flight

🤖 I can help you with that using the "Create a Flight Booking" tool.
   Shall I proceed? (yes/no)

You: yes

🤖 I'll need the following required details:
   - Flight ID (e.g. search flights first to find one)
   - Passenger ID (register first if you don't have one)
   - Seat class: economy or business

You: FL001, P001, economy

🤖 Would you also like to add:
   - A special meal? (vegetarian, vegan, halal, gluten-free)
   - Extra baggage? (adds ₹1,500)

You: vegetarian, no extra baggage

🤖 ✅ Booking confirmed!
   Booking ID : BK003
   Flight     : AI-202 (Air India) — DEL → BOM
   Departure  : Apr 10, 2026 at 6:00 AM
   Seat       : 14C (Economy)
   Meal       : Vegetarian
   Total Fare : ₹4,500
```

---

## 🔧 Changing the Ollama Model

In `agent/agent.py`:
```python
OLLAMA_MODEL = "llama3.2"   # swap for mistral, gemma3, phi4, etc.
```

## ➕ Adding a New API

1. Add a new entry to `agent/api_registry.yaml`
2. That's it — the tool is auto-generated on next run
