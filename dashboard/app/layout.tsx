import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "trade_b0t_mk1",
  description: "ML4T strategy bot — Alpaca paper trading dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <nav style={{
          background: "var(--surface)",
          borderBottom: "1px solid var(--border)",
          padding: "0 24px",
          height: 52,
          display: "flex",
          alignItems: "center",
          gap: 32,
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: "var(--purple)", letterSpacing: "0.02em" }}>
            trade_b0t_mk1
          </span>
          <a href="/" style={{ color: "var(--subtext)", fontSize: 13 }}>Overview</a>
          <a href="/signals" style={{ color: "var(--subtext)", fontSize: 13 }}>Signals</a>
          <a href="/race" style={{ color: "var(--subtext)", fontSize: 13 }}>Strategy Race</a>
          <a href="/trades" style={{ color: "var(--subtext)", fontSize: 13 }}>Trade Log</a>
        </nav>
        <main style={{ flex: 1, padding: "28px 24px", maxWidth: 1100, margin: "0 auto", width: "100%" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
