import { supabase, STRATEGY_META, STRATEGY_ORDER, type StrategyName, type StrategySnapshot } from "@/lib/supabase";
import { Card } from "@/components/Card";

export const revalidate = 300;

export default async function SignalsPage() {
  const { data } = await supabase
    .from("strategy_snapshots")
    .select("date, strategy, signals, positions")
    .order("date", { ascending: false });
  const rows = (data ?? []) as StrategySnapshot[];

  // Group by date descending
  const byDate: Record<string, Record<string, StrategySnapshot>> = {};
  for (const r of rows) {
    byDate[r.date] ??= {};
    byDate[r.date][r.strategy] = r;
  }
  const dates = Object.keys(byDate).sort().reverse();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>Signal History</h1>
        <p style={{ color: "var(--subtext)", marginTop: 6 }}>
          What each strategy said every day, and why.
        </p>
      </div>

      {dates.length === 0 ? (
        <Card><p style={{ color: "var(--subtext)" }}>No signals logged yet.</p></Card>
      ) : dates.map(date => (
        <Card key={date} title={new Date(date).toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {STRATEGY_ORDER.map(key => {
              const row = byDate[date][key];
              if (!row) return null;
              const meta = STRATEGY_META[key];
              const signals = (row.signals ?? {}) as Record<string, unknown>;
              return (
                <div key={key} style={{ borderTop: "1px solid var(--border)", paddingTop: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, background: meta.color, borderRadius: 2, marginRight: 8 }} />
                    {meta.label}
                  </div>
                  <pre style={{
                    fontSize: 11, fontFamily: "monospace", color: "var(--subtext)",
                    background: "var(--bg)", padding: "10px 14px", borderRadius: 6,
                    overflow: "auto", margin: 0,
                  }}>
                    {JSON.stringify(signals, null, 2)}
                  </pre>
                </div>
              );
            })}
          </div>
        </Card>
      ))}
    </div>
  );
}
