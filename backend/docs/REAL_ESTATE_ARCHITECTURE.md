# Real Estate Autonomous Company — Architecture Document

## Overview

The Real Estate vertical slice is a domain demonstration built ON TOP of the
existing Mycel Operating System. It does not replace, duplicate, or bypass
any existing Mycel architecture.

---

## Architecture Diagram

```
                         USER
                            │
                  ┌─────────┴─────────┐
                  │                   │
               Phone              Browser
                  │                   │
              VoiceGateway      Web Speech API
           (GroqWhisperProvider) (BrowserVoiceProvider)
                  │                   │
                  └─────────┬─────────┘
                            │
                            ▼
                POST /api/v1/real-estate/conversations/{id}/message
                            │
                            ▼
                  RealEstateRouter.route_and_execute()
                            │
               ┌────────────┤
               ▼            │
         classify_intent()  │  (Groq LLM — llama-3.1-8b-instant)
         language_detect()  │  Multilingual: EN/HI/PA → structured JSON
               │            │
               ▼            │
         CAPABILITY_MAP     │  (Deterministic dict — no LLM)
         intent → team      │
         intent → tool      │
               │            │
               ▼            │
         SecurityGateway    │  (existing security/gateway.py)
              + ArmorIQ     │  ActionType.TOOL_EXECUTION
               │            │
               ▼            │
          ToolRegistry      │  (existing tools/registry/core.py)
               │            │
     ┌─────────┼──────────┐ │
     ▼         ▼          ▼ │
property.   property.  property.
 search      legal     investment
  (MongoDB)  (KB)      (arithmetic)
     │         │          │
     └────────-┼──────────┘
               │
               ▼
         generate_response()  (Groq LLM — natural language only)
               │
     ┌─────────┴─────────┐
     ▼                   ▼
  REST response     WebSocket broadcast
  (HTTP)            (existing ConnectionManager)
     │                   │
     ▼                   ▼
  Frontend            Live Dashboard
  (JSON)              (React events)
```

---

## Existing Components Used

| Component | Location | Integration |
|---|---|---|
| SecurityGateway | `security/gateway.py` | Called before every tool execution |
| ArmorIQAdapter | `security/providers/armoriq.py` | Via SecurityGateway provider |
| GroqEngineManager | `core/groq_engine.py` | Intent classification + response generation |
| ConnectionManager (WS) | `api/v1/routes/realtime/router.py` | Event broadcasting |
| ToolRegistry | `tools/registry/core.py` | Tool registration at startup |
| BaseTool | `tools/base.py` | All 4 RE tools implement this |
| ToolExecutionContext | `tools/context.py` | Passed to every tool.execute() |
| ToolResult | `agents/runtime/result.py` | Returned by every tool |
| MongoDBConnection | `core/mongodb.py` | Property storage + search |
| Settings | `core/config.py` | API keys, DB URLs |

---

## New Components Created

| Component | Location | Purpose |
|---|---|---|
| `RealEstateRouter` | `domains/real_estate/router.py` | Full pipeline orchestration |
| `PropertyRecord` | `domains/real_estate/models.py` | Property data model |
| `CustomerContext` | `domains/real_estate/models.py` | Customer/lead model |
| `CustomerRequirements` | `domains/real_estate/models.py` | Structured requirements |
| `IngestionJob` | `domains/real_estate/models.py` | Dataset versioning |
| `ConversationState` | `domains/real_estate/models.py` | Persistent session state |
| `VoiceGateway` | `domains/real_estate/voice.py` | STT/TTS provider abstraction |
| `PropertySearchTool` | `domains/real_estate/tools/property_search.py` | MongoDB structured search |
| `PropertyCompareTool` | `domains/real_estate/tools/property_compare.py` | Side-by-side comparison |
| `PropertyLegalTool` | `domains/real_estate/tools/property_legal.py` | Legal KB retrieval |
| `PropertyInvestmentTool` | `domains/real_estate/tools/property_investment.py` | Rental yield / ROI analysis |
| `teams/sales/team.py` | `teams/sales/team.py` | Sales team definition |
| `teams/sales/positions/__init__.py` | `teams/sales/positions/` | Property Advisor position |
| Real Estate FastAPI Router | `domains/real_estate/api.py` | All HTTP endpoints |

---

## Intent → Capability Routing (Deterministic)

```
PROPERTY_SEARCH           → sales    / property_advisor     / property.search
PROPERTY_RECOMMENDATION   → sales    / property_advisor     / property.compare
PROPERTY_INVESTMENT_ANALYSIS → finance / investment_analyst / property.investment_analysis
PROPERTY_LEGAL_QUERY      → legal    / legal_analyst        / property.legal_knowledge
PROPERTY_COMPARISON       → sales    / property_advisor     / property.compare
GENERAL_QUERY             → sales    / property_advisor     / (no tool)
```

No `if/elif` chains. No hardcoded agent dispatch. CAPABILITY_MAP dict drives all routing.

---

## Multilingual Architecture

```
"Mujhe 80 lakh ke andar 2BHK chahiye"  (Hindi)
"Mainu 80 lakh tak 2BHK chahida"        (Punjabi)
"I want 2BHK under 80 lakhs"            (English)
                    ↓
          classify_intent() via Groq LLM
                    ↓
{
  "intent": "PROPERTY_SEARCH",
  "language": "hi" / "pa" / "en",
  "requirements": { "budget_max": 8000000, "bhk": 2 }
}
                    ↓
    Same structured state — language-independent
                    ↓
   MongoDB query using structured filters (no LLM)
```

Conversation history is maintained across language switches. Requirements from Hindi
query persist when follow-up is in Punjabi.

---

## Security Integration

Every tool execution:
1. Builds `SecurityRequest` with `ActionType.TOOL_EXECUTION`
2. Sets `intent` = human-readable string (e.g. "Retrieve approved PROPERTY_LEGAL_KNOWLEDGE information")
3. Passes through `SecurityGateway.evaluate_request()`
4. ArmorIQ evaluates — returns ALLOW / DENY
5. Tool only executes on ALLOW

If DENY → `TASK_FAILED` event emitted, user receives security denial message.

---

## MongoDB Schema (Property Collection: `re_properties`)

```json
{
  "property_id": "uuid",
  "title": "string",
  "property_type": "Apartment | Villa | Plot | ...",
  "bhk": 2,
  "area_sqft": 1200.0,
  "price": 7500000.0,
  "location": "Chandigarh",
  "city": "Chandigarh",
  "locality": "Sector 34",
  "floor": 3,
  "total_floors": 10,
  "age": 2,
  "parking": 1,
  "amenities": ["gym", "pool", "security"],
  "developer": "ABC Builders",
  "availability": "Ready to move",
  "rental_yield": 4.2,
  "historical_price": 6500000.0,
  "demand_score": 78.5,
  "latitude": 30.7333,
  "longitude": 76.7794,
  "description": "...",
  "image_url": "..."
}
```

---

## Legal Knowledge Base

Seeded synthetic documents for demo (labeled clearly):
- `LKB-001`: Residential Setback Requirements — Punjab Municipal Building Bylaws
- `LKB-002`: RERA Punjab — Property Registration Requirements
- `LKB-003`: Stamp Duty & Registration Charges — Punjab/Haryana
- `LKB-004`: FAR and Coverage Rules — Chandigarh/Tricity

Retrieval: keyword-based match (no vector DB required for demo).
In production: Qdrant with sentence-transformers embeddings.

Every legal response includes:
- `source_type`: "LEGAL_KNOWLEDGE_BASE"
- `source_document`: document ID
- `confidence`: float
- `disclaimer`: always present

---

## Voice Architecture

```
Browser Mode:
  Web Speech API (client-side STT) → text → POST /message
  SpeechSynthesis API (client-side TTS) ← response text

Phone Mode (VoiceLink):
  SIP/WebSocket audio → GroqWhisperProvider.transcribe() → text → POST /message
  Response text → TTS → audio → SIP
```

`VoiceGateway` selects provider by `mode` parameter.
VoiceLink integration is isolated behind `VoiceGateway` — not spread through business logic.

---

## WebSocket Event Stream

All events broadcast via existing `ConnectionManager.broadcast()`.
Events carry: `event_type`, `conversation_id`, `domain: "real_estate"`, `payload`.

```
CONVERSATION_STARTED → LANGUAGE_DETECTED → INTENT_DETECTED →
CAPABILITY_RESOLVED → TEAM_SELECTED → MEMBER_SELECTED →
DATA_SOURCE_SELECTED → TASK_CREATED → TASK_STARTED →
RETRIEVAL_STARTED → RETRIEVAL_COMPLETED →
ANALYSIS_STARTED → ANALYSIS_COMPLETED →
RESPONSE_GENERATED → TASK_COMPLETED
```

On error: `TASK_FAILED` with reason code.

No chain-of-thought is ever broadcast. Only: intent, capability, team, member, source, stage.

---

## Dataset Versioning

Every upload creates an `IngestionJob` with:
- `dataset_id`: UUID
- `version`: int
- `filename`: original filename
- `uploaded_at`: timestamp
- `status`: PENDING → PROCESSING → COMPLETED / FAILED
- `row_count`: successfully ingested rows
- `rows_failed`: skipped rows
- `schema_fields`: detected column names

Previous datasets are preserved — MongoDB upserts by `property_id`.

---

## API Endpoints

```
POST /api/v1/real-estate/conversations
POST /api/v1/real-estate/conversations/{id}/message
GET  /api/v1/real-estate/properties?budget_max=&bhk=&location=&limit=&skip=
POST /api/v1/real-estate/data/upload
GET  /api/v1/real-estate/data/status
GET  /api/v1/real-estate/customers/{id}
GET  /api/v1/real-estate/customers

# Legacy backward-compat:
POST /real_estate/chat
POST /real_estate/upload
```

---

## Performance Constraints

- `llama-3.1-8b-instant` at T=0 for intent classification (~200-400ms)
- MongoDB structured query — no LLM for filtering
- Legal retrieval — keyword match, no vector embedding required for demo
- Investment analysis — pure Python arithmetic
- Background task for Excel ingestion — non-blocking
- Response generation: `llama-3.1-8b-instant` with max_tokens=512 (~400-700ms)
- WebSocket events — sub-50ms per broadcast
- 8GB VRAM: only inference calls; no local model loaded server-side

---

## Known Limitations

1. **Voice recording**: Browser uses text input fallback for demo reliability.
   Full VoiceLink SIP integration requires telephony infrastructure.
2. **RAG**: Legal retrieval uses keyword matching for demo.
   Qdrant + sentence-transformers would be the production replacement.
3. **Conversation persistence**: In-memory dict — dies on server restart.
   Redis integration is the production path (redis_url is in settings).
4. **Investment data**: Requires `rental_yield` and `historical_price` in uploaded Excel.
   Demo properties may lack these fields.

---

## Extension Points

1. Qdrant vector indexing for property descriptions + legal PDFs
2. Redis-backed ConversationState for multi-worker scaling
3. VoiceLink SIP integration via GroqWhisperProvider
4. Cloudinary for property images
5. Evaluation metrics: intent_accuracy, routing_accuracy, latency per stage
6. Additional intents: MORTGAGE_QUERY, SITE_VISIT_BOOKING, PRICE_NEGOTIATION
