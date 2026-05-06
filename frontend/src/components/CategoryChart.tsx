"use client";

const COLORS: Record<string, string> = {
  "billing":         "#f59e0b",
  "bug report":      "#ef4444",
  "feature request": "#3b82f6",
  "account issue":   "#7c6af5",
  "other":           "#6b6f80",
};

export default function CategoryChart({ breakdown }: { breakdown: Record<string, number> }) {
  const total   = Object.values(breakdown).reduce((a, b) => a + b, 0);
  if (!total) return null;
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-3">
      <p className="text-[10px] uppercase tracking-widest text-muted font-body">Category breakdown</p>
      <div className="space-y-2.5">
        {entries.map(([cat, cnt]) => {
          const pct = Math.round((cnt / total) * 100);
          return (
            <div key={cat}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-mono capitalize text-[#e8e9f0]">{cat}</span>
                <span className="text-[11px] font-mono text-muted">{cnt} ({pct}%)</span>
              </div>
              <div className="h-[3px] w-full bg-border2 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, background: COLORS[cat] ?? "#6b6f80" }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

