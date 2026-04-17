###  Part 3 (Vibe coding)


6.  What vibe coding tool(s) did you use?

Claude. Used it through claude.ai while building this out.


7.  Show us one specific moment where the tool helped.

I was writing the system prompt and kept ending up with vague escalation rules like "escalate if the customer seems very frustrated." That's useless — every agent would interpret it differently, and the model would too.

So I asked Claude: "Give me specific, concrete escalation triggers for a B2B SaaS support ticket system. Not vague ones — actual conditions with clear thresholds."

It came back with things like: billing amount over $1000, customer mentions legal action, production system down, data breach suspected, issue unresolved over 48 hours. That's exactly what I needed. Conditions the model can actually check, not just vibes.

I kept most of that list. Cut the one about escalating if the customer uses all caps — too noisy, it would fire constantly.


8.  Where did the tool get it wrong or fall short?

The fallback logic. Claude wrote a try/except that caught the error, logged it, and returned a generic error string to the caller. Looked clean. Was wrong.

If Gemini fails and Groq also fails and I just return an error string — what actually happens to that ticket? Nothing. It's gone. Nobody knows. In a real support system, that's a dropped customer.

I rewrote it so failures raise a typed LLMError, the API returns a proper 503, and the failure is logged with enough detail to actually debug later. The ticket is always traceable. Claude was solving for "looks handled." I needed "actually handled."


9.  What is your mental model for vibe coding on a client project?

I treat it like a fast junior dev. It's really good at stuff I'd be Googling anyway — API payload formats, Pydantic syntax, boilerplate setup. Let it write that, review it, move on.

I take over for anything where being wrong has a real cost — error handling, anything touching payments or user data, logic that needs to fail loudly not quietly.

One question I ask before shipping AI-written code: if this breaks at 2am, will I know? If the answer is no — I rewrite it myself.



###  Part 4 (Reflection)


10.  What corners did you cut in the prototype that you would fix before going to production?

No auth on the API. Anyone can call /analyze-ticket right now. Fine for a prototype, definitely not fine for anything real.

Knowledge base is a JSON file with 10 tickets. Keyword matching works here but it won't scale. Needs proper vector search once the ticket history actually grows.

No feedback capture. When an agent fixes the category or rewrites the draft, that information just disappears. That's probably the most valuable signal I have for improving the system and I'm not collecting any of it.

Confidence score comes straight from the model. Models are genuinely bad at knowing when they're wrong. Real confidence should come from tracking how often agents actually override the AI's decisions over time.


11.  If this were a real client engagement, what is the first question you would ask before building
anything?

I'd ask to sit next to an agent and watch them handle tickets for 20 minutes. Not a walkthrough, not a demo — just watch.

Every time I've done this on a real project, what I actually see is different from what anyone described to me. Sometimes agents already have a shared doc full of copy-paste replies and the real problem is just finding the right one fast. Sometimes they spend more time in the CRM looking up account history than writing anything. You can't build the right solution until you see where the actual friction is.


12.  What would a v2 look like? What would you add next, and in what order?

In order of what actually matters:
Feedback buttons first. Category wrong, reply edited, escalation wrong — one click. Without this data the system never gets better. Everything else depends on having it.

Real RAG second. Swap keyword matching for embeddings and vector search over actual resolved tickets. Better examples in the prompt means better drafts. Highest ROI improvement once feedback is running.

Email webhook third. Right now someone has to manually POST to the API. In production the inbox should trigger analysis automatically. Until that's done it's a prototype, not a real product.

Simple agent UI fourth. Not a full product — just a screen with the ticket on one side and the AI output on the other, with approve/edit/escalate buttons. Makes feedback capture feel natural instead of like an extra step.

Analytics last. Escalation rate, override rate by category, cost per ticket. Mainly so I can show whether it's actually working and where to focus next.


