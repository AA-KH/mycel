# Mycel — Backend API

> FastAPI-powered backend for the Mycel multi-agent monitoring platform.

**Author**: Kaushal Jindal
**Project**: Mycel
**Country**: India 🇮🇳
**Timezone**: IST (Asia/Kolkata, UTC+5:30)

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.129 | High-performance Python web framework |
| **Uvicorn** | 0.41 | ASGI server |
| **Motor** | 3.7 | Async MongoDB driver |
| **aio-pika** | 9.6 | Async RabbitMQ client |
| **Groq** | latest | LLM engine for internal agents |
| **ArmorIQ SDK** | latest | Agent intent security & verification |
| **Pydantic** | 2.12 | Data validation |
| **Loguru** | 0.7 | Structured logging |
| **PyJWT** | 2.11 | JWT authentication |
| **passlib + bcrypt** | 1.7.4 / 3.2.2 | Password hashing |

---

## 📁 Directory Structure

```
backend/
├── main.py                  # FastAPI application entry point
├── consumer_worker.py       # RabbitMQ background worker
├── run_agent.py             # Test script to run a Groq agent
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (gitignored)
├── Dockerfile               # Docker container definition
│
├── core/                    # Shared core modules
│   ├── config.py            # Settings (loaded from .env)
│   ├── logger.py            # Loguru logging setup
│   ├── mongodb.py           # Async MongoDB connection
│   ├── rabbitmq.py          # RabbitMQ connection & publisher
│   └── groq_engine.py       # RobustGroqClient with API key failover
│
├── agents/                  # Internal Groq-powered AI agents
│   ├── __init__.py
│   └── base_agent.py        # BaseAgent class with status reporting
│
└── modules/                 # Feature modules
    ├── auth/                # Authentication (register, login, JWT)
    ├── realtime/            # WebSocket real-time updates
    └── api_router.py        # REST API endpoints (sessions, keys)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for MongoDB & RabbitMQ)

### Step 1: Start Infrastructure
```bash
# From the project root
docker-compose up -d mongodb rabbitmq
```

### Step 2: Setup Python Environment
```bash
cd backend
python -m venv ../venv
..\venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Step 3: Configure Environment
Create a `.env` file in the `backend/` folder:

```env
# Application
APP_NAME=Mycel

# JWT
JWT_SECRET_KEY=your-strong-secret-key-here
JWT_ALGORITHM=HS256

# MongoDB
MONGODB_URL=mongodb://localhost:27017/mycel

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=

# ArmorIQ Security
ARMORIQ_API_KEY=your_armoriq_api_key_here

# Groq API Keys (with failover)
GROQ_API_KEY_1=your_first_groq_api_key
GROQ_API_KEY_2=your_second_groq_api_key
```

### Step 4: Run the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🤖 Groq Agent Engine

The core of Mycel is the **RobustGroqClient** (`core/groq_engine.py`), which manages a pool of two Groq API keys:

- If `GROQ_API_KEY_1` hits a rate limit (HTTP 429) or quota error, it **silently fails over** to `GROQ_API_KEY_2`.
- This ensures agents never crash mid-task due to API limits.

### Running a Test Agent
```bash
python run_agent.py
```

This spawns a "Groq Researcher" agent using `llama-3.3-70b-versatile`, assigns it a task, and streams its `working → complete` status live to the Mycel frontend office.

---

## 🔐 Authentication API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and get JWT token |
| `GET` | `/api/data/sessions` | Get active agent sessions |
| `GET` | `/api/data/keys` | List your API keys |
| `POST` | `/api/data/keys` | Create a new API key |
| `DELETE` | `/api/data/keys/{id}` | Delete an API key |
| `GET` | `/health` | Server health check |

---

## 📡 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚠️ Known Issues

### bcrypt version conflict
`passlib 1.7.4` is incompatible with `bcrypt >= 4.0`. Pin to `bcrypt==3.2.2` in `requirements.txt` (already done). If you face errors, run:
```bash
pip install bcrypt==3.2.2 --force-reinstall
```

---

*Built with ❤️ in India by Kaushal Jindal*
