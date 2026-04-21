"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

type Point = { date: string; total_value: number };

function fmt(d: string) {
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function PortfolioChart({ data }: { data: Point[] }) {
  if (data.length === 0) {
    return (
      <div style={{ height: 220, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--subtext)" }}>
        No portfolio history yet.
      </div>
    );
  }

  const min = Math.min(...data.map(d => d.total_value));
  const max = Math.max(...data.map(d => d.total_value));
  const pad = (max - min) * 0.1 || 10;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis
          dataKey="date"
          tickFormatter={fmt}
          tick={{ fill: "var(--subtext)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[min - pad, max + pad]}
          tickFormatter={v => `$${v.toFixed(0)}`}
          tick={{ fill: "var(--subtext)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={56}
        />
        <Tooltip
          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
          labelFormatter={(d: unknown) => fmt(String(d))}
          formatter={(v: unknown) => [`$${Number(v).toFixed(2)}`, "Portfolio"]}
        />
        <ReferenceLine y={1700} stroke="var(--muted)" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="total_value"
          stroke="var(--purple)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "var(--purple)" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
