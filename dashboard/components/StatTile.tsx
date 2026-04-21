export function StatTile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "18px 22px",
    }}>
      <p style={{ fontSize: 11, fontWeight: 600, color: "var(--subtext)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
        {label}
      </p>
      <p style={{ fontSize: 28, fontWeight: 700, color: accent ?? "var(--text)", lineHeight: 1.1 }}>
        {value}
      </p>
      {sub && (
        <p style={{ fontSize: 12, color: "var(--subtext)", marginTop: 4 }}>{sub}</p>
      )}
    </div>
  );
}
