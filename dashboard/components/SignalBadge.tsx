const CONFIG: Record<number, { label: string; color: string; bg: string }> = {
  1:  { label: "LONG  ▲", color: "#22d87a", bg: "rgba(34,216,122,0.10)" },
  0:  { label: "FLAT  —", color: "#7b82a0", bg: "rgba(123,130,160,0.10)" },
  [-1]:{ label: "SHORT ▼", color: "#ff4d6a", bg: "rgba(255,77,106,0.10)" },
};

export function SignalBadge({ signal }: { signal: number }) {
  const cfg = CONFIG[signal] ?? CONFIG[0];
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 10px",
      borderRadius: 6,
      fontSize: 12,
      fontWeight: 700,
      letterSpacing: "0.04em",
      color: cfg.color,
      background: cfg.bg,
      border: `1px solid ${cfg.color}33`,
    }}>
      {cfg.label}
    </span>
  );
}
