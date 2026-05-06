function color(c: number) {
  if (c >= 0.8) return { bar: "#22c55e", text: "text-success" };
  if (c >= 0.5) return { bar: "#f59e0b", text: "text-warning" };
  return        { bar: "#ef4444", text: "text-danger" };
}

export default function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const { bar, text } = color(confidence);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest text-muted font-body">AI confidence</span>
        <span className={`text-[11px] font-mono font-medium ${text}`}>{pct}%</span>
      </div>
      <div className="h-[3px] w-full bg-border2 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: bar }}
        />
      </div>
    </div>
  );
}

