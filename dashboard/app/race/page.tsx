import { getSnapshotHistory, getSignalHistory } from "@/lib/supabase";
import { Card } from "@/components/Card";
import { StrategyRaceChart } from "@/components/StrategyRaceChart";

export const revalidate = 300;

export default async function RacePage() {
  const [snapshots, signals] = await Promise.all([
    getSnapshotHistory(),
    getSignalHistory(),
  ]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <h1 style={{ fontSize: 20, fontWeight: 700 }}>Strategy Race</h1>
      <p style={{ color: "var(--subtext)", marginTop: -16 }}>
        Actual portfolio (Manual Strategy, real trades) vs ML Strategy (shadow mode, no real orders).
        Dashed line = $1,700 baseline.
      </p>

      <Card title="Cumulative Value — Manual vs ML vs Baseline">
        <StrategyRaceChart snapshots={snapshots as any} signals={signals} />
      </Card>

      <Card title="Legend">
        <div style={{ display: "flex", gap: 28 }}>
          {[
            { color: "var(--purple)", label: "Actual Portfolio (Manual Strategy, real trades)" },
            { color: "var(--green)",  label: "Manual Strategy (simulated)" },
            { color: "var(--blue)",   label: "ML Shadow (no real orders)" },
            { color: "var(--muted)",  label: "$1,700 baseline" },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 24, height: 2, background: color, borderRadius: 1 }} />
              <span style={{ fontSize: 12, color: "var(--subtext)" }}>{label}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
