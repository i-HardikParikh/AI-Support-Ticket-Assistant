
###  Part 1 (Solution design - No code)


1.  What is the core problem you are solving? 

Agents are doing the same thinking over and over, like 400 times a day. They read the ticket, figure out what kind of problem it is, write basically the same reply they wrote yesterday, and decide if it needs a manager. That whole thinking loop is the actual bottleneck — not the typing itself. If I can just cut that loop and put a ready answer in front of the agent for them to approve, I've saved most of the time without taking the human out of the picture.


2.  Walk through your workflow step by step.

Email comes in → hits POST /analyze-ticket via webhook from the email provider → system pulls 2-3 similar old tickets from the knowledge base → sends everything to Gemini with a tight prompt → if Gemini fails, it automatically retries with Groq → comes back with: category, draft reply, escalation yes/no, and the reason why → if escalation is true, it goes to the senior agent queue with the reason already written → if not, the agent just sees the draft, tweaks it if needed, and hits send.

Point is — the agent doesn't start from a blank page. They open the ticket and the heavy lifting is already done. They're just checking if it looks right.


3.  What AI model(s) or API would you use, and why?

Gemini 1.5 Flash is the primary. It's fast, it's cheap, and it has native JSON mode — which means I'm not trying to parse free text and hoping the model formatted it right. For something like classification plus a short reply, you don't need a massive model. Flash handles it fine and won't blow through budget when volume picks up.

Groq with LLaMA 3 8B is the fallback. If Gemini goes down on a busy Friday afternoon with 400 tickets coming in, I need something that just works — immediately. Groq is fast, the API format is compatible, and it handles the same JSON structure. I'm not saying it's better than Gemini. It's just reliably there.

No vector database for RAG. Kept it keyword-based on purpose. With 10 sample tickets, setting up Pinecone would be complete overkill. Simple word overlap works fine at this scale, it's easy to debug, and if the knowledge base actually grows, adding vector search is a one-day job for v2.


4.  What are the 2 biggest failure points in production, and how would you handle them? 

First one: LLM returns broken JSON. In testing it barely happens. In production it happens enough to be a real problem. My fix — Pydantic validates every response right away. If it fails validation, try Groq. If Groq also fails, the ticket goes to a human queue with a flag on it. It never silently disappears. That part matters more than anything.

Second one: wrong classification but high confidence. This one is sneaky. A ticket that touches both a login issue and a billing problem — the model picks one, gives you 0.91 confidence, and it's just wrong. LLMs don't know what they don't know. I dealt with this in the prompt by telling it to classify by the most urgent issue and explain its reasoning in the escalation reason field. Not a perfect fix, but at least the agent can see that something was ambiguous and make a call.


5.  What would you NOT automate in this system, and why?

Actually sending the reply. The draft is there for the agent to review — not to fire off on its own. One confidently wrong email to an enterprise client does more damage than a slow response time. The CEO said don't replace agents, so I didn't.

Escalation actions. The system flags escalations, it doesn't act on them. If a customer mentions legal action or a data breach, a human has to decide what happens next. The AI has no idea what that customer's contract looks like or what the business relationship actually is.

Closing tickets. The agent does that manually. That action also tells us whether the AI draft was actually useful — which is data we really need.










# AI Support Ticket Assistant

A production-grade AI support assistant that automatically classifies incoming support tickets, generates draft replies, detects escalations, and tracks agent feedback — with a real-time agent dashboard and email webhook integration.

**Live demo:** `your-app.vercel.app`  
**Backend API docs:** `your-backend.railway.app/docs`

---

## What It Does

- **Classifies** tickets into: billing, bug report, feature request, account issue, other
- **Drafts** a professional reply the agent can approve or edit
- **Detects escalations** with a specific reason (not just a flag)
- **Saves every ticket** to Supabase with full audit trail
- **Captures agent feedback** — approved, edited, escalated, dismissed
- **Shows live stats** — accuracy rate, escalation rate, category breakdown
- **Accepts emails** via webhook (Postmark / SendGrid inbound)
- **Gemini primary → Groq fallback** with automatic retry logic

---

## Project Structure

```
support-ticket-assistant/
├── src/                        ← FastAPI backend
│   ├── main.py                 ← App entry point, CORS, routers
│   ├── models.py               ← All Pydantic models
│   ├── db/
│   │   └── database.py         ← All Supabase DB operations
│   ├── routers/
│   │   └── tickets.py          ← All API endpoints
│   ├── services/
│   │   ├── llm_service.py      ← Gemini + Groq with retry logic
│   │   └── ticket_analyzer.py  ← Main AI pipeline
│   ├── utils/
│   │   └── prompt_templates.py ← All LLM prompts
│   └── data/
│       └── sample_tickets.json ← RAG knowledge base
├── frontend/                   ← Next.js agent dashboard
│   └── src/
│       ├── app/
│       │   └── page.tsx        ← Main dashboard page
│       ├── components/
│       │   ├── TicketAnalyzer.tsx
│       │   ├── TicketList.tsx
│       │   ├── StatsCards.tsx
│       │   ├── CategoryChart.tsx
│       │   ├── CategoryBadge.tsx
│       │   └── ConfidenceBar.tsx
│       └── lib/
│           └── api.ts          ← All backend API calls
├── supabase_schema.sql         ← Run this once in Supabase SQL editor
├── railway.toml                ← Backend deployment config
├── requirements.txt
└── .env
```

---

## Setup — Local Development

### 1. Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env .env.local
# Edit .env with your API keys

# Run backend
uvicorn src.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 2. Database (Supabase)

1. Go to [supabase.com](https://supabase.com) → create a free project
2. Open **SQL Editor** → paste contents of `supabase_schema.sql` → Run
3. Go to **Project Settings → API** → copy `Project URL` and `service_role` key
4. Add both to your `.env`

### 3. Frontend

```bash
cd frontend
npm install

# Set backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
# → http://localhost:3000
```

---

## Environment Variables

**Backend `.env`:**
```
GEMINI_API_KEY=         # Google AI Studio → aistudio.google.com
GROQ_API_KEY=           # Groq console → console.groq.com
SUPABASE_URL=           # https://your-project.supabase.co
SUPABASE_SERVICE_KEY=   # service_role key from Supabase settings
FRONTEND_URL=           # your Vercel URL (for CORS)
```

**Frontend `frontend/.env.local`:**
```
NEXT_PUBLIC_API_URL=    # your Railway backend URL
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tickets/analyze` | Analyze a ticket — main AI endpoint |
| GET | `/tickets/` | List all tickets (filter by status) |
| GET | `/tickets/stats` | Dashboard statistics |
| GET | `/tickets/{id}` | Get a single ticket |
| POST | `/tickets/feedback` | Submit agent feedback |
| POST | `/tickets/webhook/email` | Inbound email webhook |
| GET | `/health` | Health check |

### Example curl requests

```bash
# Analyze a ticket
curl -X POST http://localhost:8000/tickets/analyze \
     -H "Content-Type: application/json" \
     -d '{"ticket": "I was charged twice this month. Please refund immediately."}'

# Submit feedback
curl -X POST http://localhost:8000/tickets/feedback \
     -H "Content-Type: application/json" \
     -d '{"ticket_id": "abc-123", "action": "approved"}'

# Get stats
curl http://localhost:8000/tickets/stats

# Health check
curl http://localhost:8000/health
```

### Example response

```json
{
  "id": "a3f9b2c1-...",
  "category": "billing",
  "draft_reply": "We apologise for the duplicate charge and have raised a refund request. You should see it credited within 3-5 business days. The Support Team",
  "escalation": false,
  "reason": "Standard billing dispute. No legal language, amount not specified as large.",
  "confidence": 0.93,
  "status": "pending"
}
```

---

## Email Webhook Setup (Postmark)

1. Sign up at [postmarkapp.com](https://postmarkapp.com) — free tier available
2. Go to **Inbound** → set webhook URL to:  
   `https://your-backend.railway.app/tickets/webhook/email`
3. Any email sent to your Postmark inbound address auto-creates a ticket

---

## Deploy to Production

### Backend → Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up

# Add environment variables in Railway dashboard
```

### Frontend → Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

vercel
# Follow prompts — it auto-detects Next.js

# Add NEXT_PUBLIC_API_URL in Vercel dashboard → Environment Variables
```

---

## Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Backend | FastAPI + Python | Fast, async, great for AI APIs |
| Primary LLM | Gemini 1.5 Flash | Cheap, fast, native JSON mode |
| Fallback LLM | Groq LLaMA 3 | Always-on backup, sub-second response |
| Database | Supabase (PostgreSQL) | Free tier, REST API, no ORM needed |
| Frontend | Next.js 14 + Tailwind | Fast to build, easy to deploy |
| Deployment | Railway + Vercel | Free tiers, deploy from GitHub |

