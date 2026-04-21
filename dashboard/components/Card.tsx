export function Card({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "20px 24px",
    }}>
      {title && (
        <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", color: "var(--subtext)", textTransform: "uppercase", marginBottom: 14 }}>
          {title}
        </p>
      )}
      {children}
    </div>
  );
}
