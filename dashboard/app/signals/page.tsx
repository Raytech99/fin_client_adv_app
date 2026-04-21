import { getSignalHistory } from "@/lib/supabase";
import { Card } from "@/components/Card";
import { SignalBadge } from "@/components/SignalBadge";

export const revalidate = 300;

const SYMBOLS = ["NVDA", "MSFT", "SPY"];

export default async function SignalsPage() {
  const all = await getSignalHistory();

  // Group by date descending
  const byDate: Record<string, typeof all> = {};
  for (const s of all) {
    if (!byDate[s.date]) byDate[s.date] = [];
    byDate[s.date].push(s);
  }
  const dates = Object.keys(byDate).sort().reverse();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <h1 style={{ fontSize: 20, fontWeight: 700 }}>Signal History</h1>
      <p style={{ color: "var(--subtext)", marginTop: -16 }}>
        BB%B, Momentum, and RSI indicator values and resulting signals for every trading day.
      </p>

      {dates.length === 0 ? (
        <Card><p style={{ color: "var(--subtext)" }}>No signals logged yet.</p></Card>
      ) : dates.map(date => {
        const sigMap = Object.fromEntries(byDate[date].map(s => [s.symbol, s]));
        return (
          <Card key={date} title={new Date(date).toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ color: "var(--subtext)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  {["Symbol", "Manual", "ML (shadow)", "BB%B", "Momentum", "RSI"].map(h => (
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
                      <td style={{ color: "var(--subtext)", fontFamily: "monospace" }}>{sig.bb_pct_b?.toFixed(4)}</td>
                      <td style={{ color: "var(--subtext)", fontFamily: "monospace" }}>{sig.momentum?.toFixed(4)}</td>
                      <td style={{ color: "var(--subtext)", fontFamily: "monospace" }}>{sig.rsi?.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        );
      })}
    </div>
  );
}
