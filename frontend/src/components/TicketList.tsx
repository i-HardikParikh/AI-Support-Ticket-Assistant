"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchTickets, type TicketRecord } from "@/lib/api";
import CategoryBadge from "./CategoryBadge";

const TABS = ["all","pending","escalated","resolved"] as const;

const STATUS_STYLE: Record<string, string> = {
  pending:   "bg-[rgba(245,158,11,0.1)] text-warning",
  resolved:  "bg-[rgba(34,197,94,0.1)]  text-success",
  escalated: "bg-[rgba(239,68,68,0.1)]  text-danger",
  ai_failed: "bg-surface2 text-muted",
};

function timeAgo(d: string) {
  const s = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
  if (s < 60)    return "just now";
  if (s < 3600)  return Math.floor(s/60)+"m ago";
  if (s < 86400) return Math.floor(s/3600)+"h ago";
  return Math.floor(s/86400)+"d ago";
}

export default function TicketList({ refreshKey }: { refreshKey: number }) {
  const [tickets,   setTickets]   = useState<TicketRecord[]>([]);
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>("all");
  const [loading,   setLoading]   = useState(true);
  const [expandId,  setExpandId]  = useState<string|null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await fetchTickets(activeTab === "all" ? undefined : activeTab, 50);
    setTickets(data);
    setLoading(false);
  }, [activeTab]);

  useEffect(() => { load(); }, [load, refreshKey]);

  return (
    <div className="flex flex-col flex-1 min-h-0">

      {/* tabs + refresh */}
      <div className="bg-surface border-b border-border flex items-center justify-between px-5 py-2.5">
        <div className="flex gap-1">
          {TABS.map(tab => (
            <button key={tab} onClick={() => { setActiveTab(tab); setExpandId(null); }}
              className={`px-3 py-1.5 rounded-md text-[11px] font-mono border transition-all ${
                activeTab === tab
                  ? "bg-surface2 text-[#e8e9f0] border-border2"
                  : "text-muted border-transparent hover:text-[#e8e9f0]"
              }`}>
              {tab}
            </button>
          ))}
        </div>
        <button onClick={load}
          className="w-7 h-7 rounded-md bg-surface2 border border-border2 flex items-center justify-center text-muted hover:text-[#e8e9f0] transition-colors">
          <svg className={`w-3.5 h-3.5 ${loading ? "animate-spin-slow" : ""}`} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 13 13">
            <path d="M1 6.5A5.5 5.5 0 1 0 6.5 1"/><path d="M1 1v5h5"/>
          </svg>
        </button>
      </div>

      {/* list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-10 gap-2 text-muted text-[13px] font-body">
            <svg className="w-4 h-4 animate-spin-slow" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 14 14">
              <path d="M7 1v2M7 11v2M1 7h2M11 7h2"/>
            </svg>
            Loading tickets…
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted">
            <svg className="w-10 h-10 opacity-20" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" viewBox="0 0 24 24">
              <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6M9 13h4"/>
            </svg>
            <p className="text-[13px] font-body">No tickets yet — analyze one to get started</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {tickets.map(t => (
              <li key={t.id}>
                <button onClick={() => setExpandId(expandId === t.id ? null : t.id)}
                  className={`w-full text-left px-5 py-3.5 hover:bg-surface transition-colors space-y-2 ${expandId === t.id ? "bg-surface" : ""}`}>
                  <div className="flex items-center justify-between gap-2">
                    <CategoryBadge category={t.category} />
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${STATUS_STYLE[t.status] ?? STATUS_STYLE.ai_failed}`}>
                        {t.status}
                      </span>
                      <span className="text-[11px] text-muted font-mono">{timeAgo(t.created_at)}</span>
                    </div>
                  </div>
                  <p className="text-[12px] text-[#e8e9f0] font-body line-clamp-2 leading-relaxed text-left">{t.raw_text}</p>
                  <div className="flex items-center gap-3 text-[11px] text-muted font-mono">
                    <span>{t.sender_email || t.source}</span>
                    {t.escalation && <span className="text-danger">⚑ escalation</span>}
                    <span>conf {Math.round(t.confidence*100)}%</span>
                  </div>
                </button>

                {/* expanded detail */}
                {expandId === t.id && (
                  <div className="mx-0 bg-surface2 border-t border-border px-5 py-4 space-y-3 animate-fade-in">
                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-1.5">Draft reply</p>
                      <div className="bg-bg border border-border2 rounded-lg px-3 py-2.5 text-[12px] text-[#e8e9f0] font-mono leading-relaxed whitespace-pre-wrap">
                        {t.edited_reply || t.draft_reply}
                      </div>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-1.5">AI reasoning</p>
                      <p className="text-[12px] text-muted font-body leading-relaxed italic border-l-2 border-border2 pl-3">{t.reason}</p>
                    </div>
                    <div className="flex flex-wrap gap-4 text-[11px] font-mono text-muted">
                      <span>confidence <span className="text-[#e8e9f0]">{Math.round(t.confidence*100)}%</span></span>
                      <span>source <span className="text-[#e8e9f0]">{t.source}</span></span>
                      {t.agent_action    && <span>action <span className="text-[#e8e9f0]">{t.agent_action}</span></span>}
                      {t.corrected_category && <span>corrected → <span className="text-warning">{t.corrected_category}</span></span>}
                      {t.sender_email    && <span>from <span className="text-[#e8e9f0]">{t.sender_email}</span></span>}
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}