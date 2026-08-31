# Mycel

> A virtual office where you can watch your AI agents work in real-time.

**TEAM**: EVOLVE AI &nbsp;|&nbsp; A solution by Evolve AI for AUTOMATE-INDIA Hackathon 

**Mycel** is a modern, real-time monitoring dashboard and execution environment for your AI agents. Instead of running agents blindly in the background, you can watch them "sit at their desks" in a retro pixel-art office, complete with live status updates, roles, and animations as they power through their tasks.

---

## 🌟 Key Features

### 1. Robust Groq Multi-Agent Engine
- **Native Groq Integration**: Features highly capable internal agents powered natively by the **Groq API**, defaulting to `llama-3.3-70b-versatile` for blazing-fast, top-tier output quality.
- **Failover System**: Built-in resiliency that manages a pool of two Groq API keys (`GROQ_API_KEY_1` and `GROQ_API_KEY_2`). If the primary key hits a rate limit (HTTP 429) or quota threshold, it silently fails over to the secondary key without dropping the agent's task.

### 2. Live Pixel-Art Virtual Office
- **Real-Time WebSockets**: As agents work on tasks, they instantly push their status (`working`, `idle`, `complete`) to the frontend via GraphQL WebSockets.
- **Visual Tracking**: Watch your agents as pixel characters on screen. See exactly what they are thinking and doing at any given moment.

### 3. Enterprise Security with ArmorIQ
- **Intent Verification**: Native integration with the **ArmorIQ SDK** ensures that all agent actions and task intents are validated and logged before execution, keeping your autonomous systems secure.

---

## 🏗️ Architecture

- **Backend Engine**: Built on **FastAPI** (Python). 
- **Agent Framework**: Custom lightweight framework (`backend/agents/base_agent.py`) that wraps Groq's async client.
- **State & Messaging**: Uses **MongoDB** for persistent session storage and **RabbitMQ** for internal event messaging.
- **Frontend Dashboard**: A responsive **React / Vite** application styled with TailwindCSS, rendering a beautiful retro pixel-art UI.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for MongoDB and RabbitMQ)

### 1. Start Infrastructure
Run the included docker-compose file to spin up MongoDB and RabbitMQ:
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure your `.env` file in the `backend` directory:
```env
# MongoDB & RabbitMQ
MONGODB_URL=mongodb://admin:secret@localhost:27017/office
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# ArmorIQ Security
ARMORIQ_API_KEY=your_armoriq_api_key_here

# Groq API Keys (For failover support)
GROQ_API_KEY_1=your_first_groq_api_key
GROQ_API_KEY_2=your_second_groq_api_key
```

Start the FastAPI backend:
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to enter **Mycel**.

---

## 🤖 Running an Agent

To see the system in action, you can run the included verification script. This script spins up an internal Groq Researcher agent and assigns it a complex task.

In a new terminal:
```bash
cd backend
python run_agent.py
```

Look at your frontend dashboard — you will see your new agent appear in the office, update its status to "working", and finally "complete" once the Groq LLM finishes processing!