import { getRecentTrades } from "@/lib/supabase";
import { Card } from "@/components/Card";

export const revalidate = 300;

const ACTION_COLORS: Record<string, string> = {
  buy:   "var(--green)",
  short: "var(--red)",
  close: "var(--yellow)",
};

export default async function TradesPage() {
  const trades = await getRecentTrades(100);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <h1 style={{ fontSize: 20, fontWeight: 700 }}>Trade Log</h1>
      <p style={{ color: "var(--subtext)", marginTop: -16 }}>
        All orders placed by the Manual Strategy. ML shadow signals are logged in the Signals tab only.
      </p>

      <Card>
        {trades.length === 0 ? (
          <p style={{ color: "var(--subtext)" }}>No trades placed yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "var(--subtext)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {["Date", "Symbol", "Action", "Shares", "Price", "Dollar Amount"].map(h => (
                  <th key={h} style={{ textAlign: "left", paddingBottom: 12, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map(t => (
                <tr key={t.id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "10px 0", color: "var(--subtext)", fontFamily: "monospace", fontSize: 12 }}>{t.date}</td>
                  <td style={{ fontWeight: 700 }}>{t.symbol}</td>
                  <td>
                    <span style={{
                      color: ACTION_COLORS[t.action] ?? "var(--text)",
                      fontWeight: 700,
                      fontSize: 12,
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}>
                      {t.action}
                    </span>
                  </td>
                  <td style={{ fontFamily: "monospace" }}>{Number(t.shares).toFixed(4)}</td>
                  <td style={{ fontFamily: "monospace" }}>${Number(t.price).toFixed(2)}</td>
                  <td style={{ fontFamily: "monospace" }}>${Number(t.dollar_amount).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
