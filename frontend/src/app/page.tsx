"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchStats, checkHealth, type DashboardStats } from "@/lib/api";
import TicketAnalyzer from "@/components/TicketAnalyzer";
import TicketList from "@/components/TicketList";
import StatsCards from "@/components/StatsCards";
import CategoryChart from "@/components/CategoryChart";

export default function Dashboard() {
  const [stats, setStats]         = useState<DashboardStats | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [apiStatus, setApiStatus]  = useState<"connecting"|"ok"|"error">("connecting");

  const loadStats = useCallback(async () => {
    const ok = await checkHealth();
    setApiStatus(ok ? "ok" : "error");
    if (ok) {
      const data = await fetchStats();
      if (data) setStats(data);
    }
  }, []);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, [loadStats]);

  function handleAnalyzed() {
    setRefreshKey(k => k + 1);
    setTimeout(loadStats, 600);
  }

  const statusColor =
    apiStatus === "ok"         ? "bg-success shadow-[0_0_6px_rgba(34,197,94,0.5)] animate-pulse2"
    : apiStatus === "error"    ? "bg-danger"
    : "bg-warning animate-pulse2";

  const statusLabel =
    apiStatus === "ok"    ? "API connected"
    : apiStatus === "error" ? "API offline"
    : "Connecting…";

  return (
    <div className="min-h-screen bg-bg text-[#e8e9f0] flex flex-col">

      {/* ── HEADER ── */}
      <header className="sticky top-0 z-50 bg-surface border-b border-border flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 16 16">
              <rect x="2" y="2" width="12" height="12" rx="2"/><path d="M8 5v4M6 7h4"/>
            </svg>
          </div>
          <div>
            <h1 className="font-display text-[15px] font-semibold tracking-tight leading-none text-[#e8e9f0]">Support AI</h1>
            <p className="text-[11px] text-muted mt-0.5 leading-none font-body">Agent Dashboard</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-[7px] h-[7px] rounded-full flex-shrink-0 ${statusColor}`} />
            <span className="text-[12px] text-muted font-body">{statusLabel}</span>
          </div>
          <div className="font-mono text-[11px] text-muted bg-surface2 px-2.5 py-1 rounded-md border border-border2">
            localhost:8000
          </div>
        </div>
      </header>

      {/* ── STATS ROW ── */}
      <div className="border-b border-border">
        {stats
          ? <StatsCards stats={stats} />
          : <div className="grid grid-cols-5 divide-x divide-border">
              {[...Array(5)].map((_,i) => (
                <div key={i} className="bg-surface px-5 py-4">
                  <div className="h-3 w-20 bg-surface2 rounded animate-pulse mb-3" />
                  <div className="h-7 w-12 bg-surface2 rounded animate-pulse" />
                </div>
              ))}
            </div>
        }
      </div>

      {/* ── MAIN GRID ── */}
      <div className="flex-1 grid grid-cols-[420px_1fr] min-h-0">

        {/* LEFT — Analyze */}
        <div className="border-r border-border bg-surface flex flex-col overflow-y-auto">
          <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
            <h2 className="font-display text-[13px] font-semibold tracking-tight text-[#e8e9f0]">Analyze ticket</h2>
          </div>
          <div className="p-5 flex-1">
            <TicketAnalyzer onAnalyzed={handleAnalyzed} />
          </div>
        </div>

        {/* RIGHT — History + Chart */}
        <div className="flex flex-col min-h-0 bg-bg">
          <TicketList refreshKey={refreshKey} />
          {stats && Object.keys(stats.category_breakdown).length > 0 && (
            <div className="border-t border-border bg-surface px-5 py-4">
              <CategoryChart breakdown={stats.category_breakdown} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

