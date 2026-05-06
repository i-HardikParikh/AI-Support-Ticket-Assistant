const STYLES: Record<string, string> = {
  "billing":         "bg-[rgba(245,158,11,0.1)]  text-[#f59e0b] border border-[rgba(245,158,11,0.25)]",
  "bug report":      "bg-[rgba(239,68,68,0.1)]   text-[#ef4444] border border-[rgba(239,68,68,0.25)]",
  "feature request": "bg-[rgba(59,130,246,0.1)]  text-[#3b82f6] border border-[rgba(59,130,246,0.25)]",
  "account issue":   "bg-[rgba(124,106,245,0.12)] text-[#7c6af5] border border-[rgba(124,106,245,0.3)]",
  "other":           "bg-surface2 text-muted border border-border2",
};

export default function CategoryBadge({ category }: { category: string }) {
  const style = STYLES[category] ?? STYLES["other"];
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-mono font-medium tracking-wide ${style}`}>
      {category}
    </span>
  );
}

