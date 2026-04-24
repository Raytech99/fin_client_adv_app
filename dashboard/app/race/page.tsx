import { getAllSnapshotHistory, STRATEGY_META, STRATEGY_ORDER } from "@/lib/supabase";
import { Card } from "@/components/Card";
import { StrategyRaceChart } from "@/components/StrategyRaceChart";

export const revalidate = 300;

export default async function RacePage() {
  const snapshots = await getAllSnapshotHistory();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>Strategy Race</h1>
        <p style={{ color: "var(--subtext)", marginTop: 6 }}>
          Each strategy runs with its own virtual $1,700. Only VGT executes real Alpaca trades
          — the rest are simulated so every line is directly comparable. Dashed line = $1,700 baseline.
        </p>
      </div>

      <Card title="Cumulative Value — 5 Strategies Compared">
        <StrategyRaceChart snapshots={snapshots} />
      </Card>

      <Card title="Legend">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
          {STRATEGY_ORDER.map(key => {
            const meta = STRATEGY_META[key];
            return (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 28, height: 3, background: meta.color, borderRadius: 2 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{meta.label}</div>
                  <div style={{ fontSize: 11, color: "var(--subtext)" }}>
                    {key === "vgt_real" && "Real Alpaca trade — buy & hold VGT"}
                    {key === "manual" && "Sim: 2/3 voting on JPM, KO, XOM"}
                    {key === "ml" && "Sim: BagLearner on JPM, KO, XOM"}
                    {key === "momentum" && "Sim: 10/30 SMA crossover on MSFT, AAPL, NVDA"}
                    {key === "pairs" && "Sim: z-score pair trade on AMD/NVDA"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
