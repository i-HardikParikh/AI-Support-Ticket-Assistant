"use client";
import type { DashboardStats } from "@/lib/api";

interface CardProps { label: string; value: string | number; sub?: string; valueClass?: string; }

function Cell({ label, value, sub, valueClass = "text-[#e8e9f0]" }: CardProps) {
  return (
    <div className="bg-surface px-5 py-4">
      <p className="text-[10px] uppercase tracking-widest text-muted font-body mb-2">{label}</p>
      <p className={`font-display text-[26px] font-bold leading-none ${valueClass}`}>{value}</p>
      {sub && <p className="text-[11px] text-muted font-body mt-1.5">{sub}</p>}
    </div>
  );
}

export default function StatsCards({ stats }: { stats: DashboardStats }) {
  return (
    <div className="grid grid-cols-5 divide-x divide-border">
      <Cell label="Total tickets"  value={stats.total_tickets}       sub="all time" />
      <Cell label="Pending"        value={stats.pending}             sub="awaiting agent"   valueClass="text-warning" />
      <Cell label="Resolved"       value={stats.resolved}            sub="agent acted"      valueClass="text-success" />
      <Cell label="Escalated"      value={stats.escalated}           sub="senior queue"     valueClass="text-danger"  />
      <Cell label="AI accuracy"    value={`${stats.accuracy_rate}%`} sub="approved as-is"   valueClass="text-accent"  />
    </div>
  );
}

