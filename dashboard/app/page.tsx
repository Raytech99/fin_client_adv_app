import {
  getLatestSnapshots, getAllSnapshotHistory,
  STRATEGY_META, STRATEGY_ORDER, STARTING_CAPITAL,
  type Position,
} from "@/lib/supabase";
import { StatTile } from "@/components/StatTile";
import { Card } from "@/components/Card";
import { StrategyRaceChart } from "@/components/StrategyRaceChart";

export const revalidate = 300;

export default async function OverviewPage() {
  const [latest, history] = await Promise.all([
    getLatestSnapshots(),
    getAllSnapshotHistory(),
  ]);

  const vgt = latest.vgt_real;
  const vgtValue = vgt?.total_value ?? STARTING_CAPITAL;
  const vgtPct = ((vgtValue - STARTING_CAPITAL) / STARTING_CAPITAL) * 100;
  const returnColor = vgtPct >= 0 ? "var(--green)" : "var(--red)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

      {/* Top stat tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
        <StatTile
          label="Real Portfolio (VGT)"
          value={`$${vgtValue.toFixed(2)}`}
          sub={`Started at $${STARTING_CAPITAL.toLocaleString()}`}
        />
        <StatTile
          label="Total Return"
          value={`${vgtPct >= 0 ? "+" : ""}${vgtPct.toFixed(2)}%`}
          accent={returnColor}
        />
        <StatTile
          label="P&L"
          value={`${vgtValue - STARTING_CAPITAL >= 0 ? "+" : ""}$${(vgtValue - STARTING_CAPITAL).toFixed(2)}`}
          accent={returnColor}
        />
        <StatTile
          label="Last Updated"
          value={vgt?.date ?? "—"}
          sub="Daily 3:50 PM ET"
        />
      </div>

      {/* Strategy Race chart front and center */}
      <Card title="Strategy Race — Virtual Portfolio Value (all start at $1,700)">
        <StrategyRaceChart snapshots={history} />
      </Card>

      {/* Strategy Scoreboard */}
      <Card title="Today's Scoreboard">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "var(--subtext)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {["Strategy", "Value", "Return", "Cash", "Open Positions"].map(h => (
                <th key={h} style={{ textAlign: "left", paddingBottom: 12, fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {STRATEGY_ORDER.map(key => {
              const snap = latest[key];
              if (!snap) {
                return (
                  <tr key={key} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "14px 0" }}>
                      <span style={{ display: "inline-block", width: 10, height: 10, background: STRATEGY_META[key].color, borderRadius: 2, marginRight: 8 }} />
                      {STRATEGY_META[key].label}
                    </td>
                    <td colSpan={4} style={{ color: "var(--subtext)" }}>no data yet</td>
                  </tr>
                );
              }
              const val = Number(snap.total_value);
              const pct = ((val - STARTING_CAPITAL) / STARTING_CAPITAL) * 100;
              const color = pct >= 0 ? "var(--green)" : "var(--red)";
              const positions = snap.positions ?? {};
              const posStrs = Object.entries(positions)
                .filter(([_, p]: [string, Position]) => p.shares || p.qty)
                .map(([sym, p]: [string, Position]) => {
                  const shares = Number(p.shares ?? p.qty ?? 0);
                  return `${p.side?.toUpperCase()} ${sym} (${shares.toFixed(2)})`;
                })
                .join(" · ");

              return (
                <tr key={key} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "14px 0" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, background: STRATEGY_META[key].color, borderRadius: 2, marginRight: 8 }} />
                    {STRATEGY_META[key].label}
                  </td>
                  <td style={{ fontFamily: "monospace" }}>${val.toFixed(2)}</td>
                  <td style={{ color, fontWeight: 700 }}>{pct >= 0 ? "+" : ""}{pct.toFixed(2)}%</td>
                  <td style={{ fontFamily: "monospace", color: "var(--subtext)" }}>${Number(snap.cash ?? 0).toFixed(2)}</td>
                  <td style={{ fontSize: 12, color: "var(--subtext)" }}>{posStrs || "flat"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
