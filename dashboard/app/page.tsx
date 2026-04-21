import { getLatestSnapshot, getSnapshotHistory, getLatestSignals } from "@/lib/supabase";
import { StatTile } from "@/components/StatTile";
import { Card } from "@/components/Card";
import { SignalBadge } from "@/components/SignalBadge";
import { PortfolioChart } from "@/components/PortfolioChart";

const STARTING = 1700;
const SYMBOLS = ["NVDA", "MSFT", "SPY"];

export const revalidate = 300; // refresh every 5 min

export default async function OverviewPage() {
  const [snapshot, history, signals] = await Promise.all([
    getLatestSnapshot(),
    getSnapshotHistory(),
    getLatestSignals(),
  ]);

  const equity = snapshot?.total_value ?? STARTING;
  const totalReturnPct = ((equity - STARTING) / STARTING) * 100;
  const returnColor = totalReturnPct >= 0 ? "var(--green)" : "var(--red)";
  const sigMap = Object.fromEntries(signals.map(s => [s.symbol, s]));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

      {/* Top stat tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
        <StatTile
          label="Portfolio Value"
          value={`$${equity.toFixed(2)}`}
          sub={`Started at $${STARTING.toLocaleString()}`}
        />
        <StatTile
          label="Total Return"
          value={`${totalReturnPct >= 0 ? "+" : ""}${totalReturnPct.toFixed(2)}%`}
          accent={returnColor}
        />
        <StatTile
          label="P&L"
          value={`${equity - STARTING >= 0 ? "+" : ""}$${(equity - STARTING).toFixed(2)}`}
          accent={returnColor}
        />
        <StatTile
          label="Last Updated"
          value={snapshot?.date ?? "—"}
          sub="Market close signal"
        />
      </div>

      {/* Portfolio chart */}
      <Card title="Portfolio Value (vs $1,700 baseline)">
        <PortfolioChart data={history as any} />
      </Card>

      {/* Current positions */}
      <Card title="Current Positions">
        {!snapshot?.positions || Object.keys(snapshot.positions).length === 0 ? (
          <p style={{ color: "var(--subtext)" }}>No open positions yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "var(--subtext)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {["Symbol", "Side", "Qty", "Market Value", "Unrealized P&L"].map(h => (
                  <th key={h} style={{ textAlign: "left", paddingBottom: 10, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SYMBOLS.filter(s => snapshot?.positions?.[s]?.qty).map(s => {
                const p = snapshot!.positions![s];
                const pl = p.unrealized_pl ?? 0;
                return (
                  <tr key={s} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 0", fontWeight: 700 }}>{s}</td>
                    <td style={{ color: p.side === "long" ? "var(--green)" : "var(--red)" }}>{p.side?.toUpperCase()}</td>
                    <td>{Number(p.qty).toFixed(4)}</td>
                    <td>${Number(p.market_value).toFixed(2)}</td>
                    <td style={{ color: pl >= 0 ? "var(--green)" : "var(--red)" }}>
                      {pl >= 0 ? "+" : ""}${pl.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      {/* Today's signals quick view */}
      <Card title="Today's Signals">
        {signals.length === 0 ? (
          <p style={{ color: "var(--subtext)" }}>No signals logged yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "var(--subtext)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {["Symbol", "Manual Strategy", "ML (shadow)", "BB%B", "Momentum", "RSI"].map(h => (
                  <th key={h} style={{ textAlign: "left", paddingBottom: 10, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SYMBOLS.map(s => {
                const sig = sigMap[s];
                if (!sig) return null;
                return (
                  <tr key={s} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 0", fontWeight: 700 }}>{s}</td>
                    <td><SignalBadge signal={sig.manual_signal} /></td>
                    <td><SignalBadge signal={sig.ml_signal} /></td>
                    <td style={{ color: "var(--subtext)" }}>{sig.bb_pct_b?.toFixed(4)}</td>
                    <td style={{ color: "var(--subtext)" }}>{sig.momentum?.toFixed(4)}</td>
                    <td style={{ color: "var(--subtext)" }}>{sig.rsi?.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
