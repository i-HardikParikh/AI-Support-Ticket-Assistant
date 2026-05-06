"use client";

import { useState } from "react";
import { analyzeTicket, submitFeedback, type TicketResult } from "@/lib/api";
import CategoryBadge from "./CategoryBadge";
import ConfidenceBar from "./ConfidenceBar";

const SAMPLES = [
  { label: "billing",   text: "I was charged twice this month — same amount, same date. Please refund one immediately." },
  { label: "bug",       text: "Dashboard is broken since 9am. None of our reports load. Entire team is blocked." },
  { label: "feature",   text: "Can you add CSV export to analytics page? Using the API every time is painful." },
  { label: "account",   text: "I can't log in — reset my password 4 times and still get invalid credentials." },
  { label: "escalate",  text: "We go live in 1 hour and your API is down. Will cancel enterprise contract if not fixed NOW." },
];

export default function TicketAnalyzer({ onAnalyzed }: { onAnalyzed?: () => void }) {
  const [ticketText,    setTicketText]    = useState("");
  const [senderEmail,   setSenderEmail]   = useState("");
  const [loading,       setLoading]       = useState(false);
  const [result,        setResult]        = useState<TicketResult | null>(null);
  const [error,         setError]         = useState<string | null>(null);
  const [editedReply,   setEditedReply]   = useState("");
  const [isEditing,     setIsEditing]     = useState(false);
  const [feedbackSent,  setFeedbackSent]  = useState(false);
  const [feedbackLoad,  setFeedbackLoad]  = useState(false);
  const [showReason,    setShowReason]    = useState(false);

  async function handleAnalyze() {
    if (!ticketText.trim()) return;
    setLoading(true); setError(null); setResult(null); setFeedbackSent(false); setIsEditing(false);
    try {
      const data = await analyzeTicket(ticketText.trim(), senderEmail || undefined);
      setResult(data); setEditedReply(data.draft_reply); onAnalyzed?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally { setLoading(false); }
  }

  async function handleFeedback(action: "approved"|"edited"|"escalated"|"dismissed") {
    if (!result?.id) {
      setError("Cannot submit feedback: Ticket was not saved to the database. Please check your Supabase configuration in the .env file.");
      return;
    }
    if (feedbackSent) return;
    setFeedbackLoad(true);
    const wasEdited = editedReply !== result.draft_reply;
    await submitFeedback({
      ticket_id: result.id,
      action: wasEdited && action === "approved" ? "edited" : action,
      edited_reply: wasEdited ? editedReply : undefined,
    });
    setFeedbackSent(true); setFeedbackLoad(false); onAnalyzed?.();
  }

  function reset() {
    setTicketText(""); setSenderEmail(""); setResult(null);
    setError(null); setFeedbackSent(false); setIsEditing(false);
  }

  return (
    <div className="space-y-4">

      {/* email */}
      <div>
        <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-1.5">Customer email <span className="normal-case tracking-normal">(optional)</span></p>
        <input
          type="email" value={senderEmail} onChange={e => setSenderEmail(e.target.value)}
          placeholder="customer@company.com"
          className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-[13px] text-gray-900 placeholder-gray-400 focus:border-accent transition-colors font-body"
        />
      </div>

      {/* textarea */}
      <div>
        <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-1.5">Ticket message</p>
        <textarea
          value={ticketText} onChange={e => setTicketText(e.target.value)}
          onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") handleAnalyze(); }}
          placeholder="Paste the support ticket here…"
          rows={7}
          className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-[12px] text-gray-900 placeholder-gray-400 focus:border-accent transition-colors resize-none font-mono leading-relaxed"
        />
        <p className="text-[10px] text-muted font-body mt-1">Ctrl+Enter to analyze</p>
      </div>

      {/* samples */}
      <div>
        <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-1.5">Quick samples</p>
        <div className="flex flex-wrap gap-1.5">
          {SAMPLES.map(s => (
            <button key={s.label} onClick={() => { setTicketText(s.text); setResult(null); setError(null); setFeedbackSent(false); }}
              className="text-[11px] px-2.5 py-1 bg-surface2 border border-border2 rounded-full text-muted hover:border-accent hover:text-accent transition-all font-mono">
              {s.label}
            </button>
          ))}
          <button onClick={reset} className="text-[11px] px-2.5 py-1 bg-surface2 border border-border2 rounded-full text-muted hover:text-[#e8e9f0] transition-all font-mono ml-auto">
            clear
          </button>
        </div>
      </div>

      {/* analyze button */}
      <button onClick={handleAnalyze} disabled={loading || !ticketText.trim()}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-[13px] font-medium text-white transition-colors font-display">
        {loading ? (
          <>
            <svg className="w-4 h-4 animate-spin-slow" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 14 14">
              <path d="M7 1v2M7 11v2M1 7h2M11 7h2M3.22 3.22l1.41 1.41M9.17 9.17l1.41 1.41M3.22 10.78l1.41-1.41M9.17 4.83l1.41-1.41"/>
            </svg>
            Analyzing…
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 14 14">
              <path d="M7 1v5M10 4H4M2 7v5a1 1 0 001 1h8a1 1 0 001-1V7"/>
            </svg>
            Analyze ticket
          </>
        )}
      </button>

      {/* error */}
      {error && (
        <div className="bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.25)] rounded-lg p-3 flex items-start gap-2 animate-fade-in">
          <svg className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 14 14">
            <path d="M7 1L1 13h12L7 1zM7 6v3M7 11v.5"/>
          </svg>
          <p className="text-[12px] text-danger font-body">{error}</p>
        </div>
      )}

      {/* result */}
      {result && (
        <div className="bg-surface2 border border-border2 rounded-xl p-4 space-y-4 animate-slide-up">

          {/* header */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CategoryBadge category={result.category} />
            {result.escalation ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium text-danger bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.25)]">
                ⚑ escalation required
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium text-success bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.25)]">
                ✓ no escalation
              </span>
            )}
          </div>

          {/* confidence */}
          <ConfidenceBar confidence={result.confidence} />

          {/* draft reply */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] uppercase tracking-widest text-muted font-body">Draft reply</p>
              {!feedbackSent && (
                <button onClick={() => setIsEditing(!isEditing)}
                  className="text-[11px] text-accent hover:text-accent-hover transition-colors font-mono">
                  {isEditing ? "done" : "edit"}
                </button>
              )}
            </div>
            {isEditing && !feedbackSent ? (
              <textarea value={editedReply} onChange={e => setEditedReply(e.target.value)} rows={5}
                className="w-full bg-white border border-accent/50 rounded-lg px-3 py-2.5 text-[12px] text-gray-900 resize-none font-mono focus:border-accent transition-colors leading-relaxed"/>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-[12px] text-gray-900 font-mono leading-relaxed whitespace-pre-wrap">
                {editedReply}
              </div>
            )}
          </div>

          {/* reasoning */}
          <div>
            <button onClick={() => setShowReason(!showReason)}
              className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-muted hover:text-[#e8e9f0] transition-colors font-body w-full text-left">
              <svg className={`w-3 h-3 transition-transform ${showReason ? "rotate-90" : ""}`} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 8 8">
                <path d="M2 1l4 3-4 3"/>
              </svg>
              AI reasoning
            </button>
            {showReason && (
              <p className="mt-2 text-[12px] text-muted font-body leading-relaxed italic border-l-2 border-border2 pl-3 animate-fade-in">
                {result.reason}
              </p>
            )}
          </div>

          {/* actions */}
          {!feedbackSent ? (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-widest text-muted font-body">Agent action</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { action:"approved" as const, label: editedReply !== result.draft_reply ? "Send edited" : "Approve & send", cls:"bg-[rgba(34,197,94,0.1)] text-success border-[rgba(34,197,94,0.25)] hover:bg-[rgba(34,197,94,0.2)]" },
                  { action:"escalated" as const, label:"Escalate",       cls:"bg-[rgba(239,68,68,0.1)] text-danger border-[rgba(239,68,68,0.25)] hover:bg-[rgba(239,68,68,0.2)]" },
                  { action:"dismissed" as const, label:"Dismiss",        cls:"bg-surface2 text-muted border-border2 hover:text-[#e8e9f0]" },
                ].map(btn => (
                  <button key={btn.action} onClick={() => handleFeedback(btn.action)} disabled={feedbackLoad}
                    className={`flex items-center justify-center px-3 py-2 rounded-lg text-[12px] font-medium border transition-all disabled:opacity-40 font-body ${btn.cls}`}>
                    {btn.label}
                  </button>
                ))}
                <button onClick={reset}
                  className="flex items-center justify-center px-3 py-2 rounded-lg text-[12px] font-medium border border-border2 bg-surface2 text-muted hover:text-[#e8e9f0] transition-all font-body">
                  New ticket
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-success text-[12px] bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.25)] rounded-lg px-3 py-2.5 animate-fade-in font-body">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 14 14">
                <path d="M2 7l3.5 3.5L12 3"/>
              </svg>
              Feedback saved — improving AI accuracy
            </div>
          )}
        </div>
      )}
    </div>
  );
}

