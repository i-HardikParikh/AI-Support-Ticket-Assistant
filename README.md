# AI Support Ticket Assistant

FastAPI backend + Streamlit UI for support ticket analysis.

## Setup

### 1) Create and activate virtual environment (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Add `.env` in project root

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
LOG_LEVEL=INFO
```

## Run

### Terminal 1 - FastAPI

```bash
uvicorn src.main:app --reload
```

### Terminal 2 - Streamlit

```bash
streamlit run src/streamlit_app.py
```

## URLs

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Streamlit UI: `http://localhost:8501`

## Test API

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Analyze ticket (PowerShell)

```powershell
$body = @{ ticket = "I was double-charged this month." } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/analyze-ticket" `
  -ContentType "application/json" `
  -Body $body
```




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

