"use client";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import type { StrategySnapshot } from "@/lib/strategies";
import { STRATEGY_META, STRATEGY_ORDER, STARTING_CAPITAL } from "@/lib/strategies";

type ChartRow = {
  date: string;
  vgt_real?: number | null;
  manual?: number | null;
  ml?: number | null;
  momentum?: number | null;
  pairs?: number | null;
};

function buildChartData(snapshots: StrategySnapshot[]): ChartRow[] {
  const dates = [...new Set(snapshots.map(s => s.date))].sort();
  const byDateStrategy: Record<string, Record<string, number>> = {};
  for (const s of snapshots) {
    byDateStrategy[s.date] ??= {};
    byDateStrategy[s.date][s.strategy] = Number(s.total_value);
  }
  return dates.map(d => ({
    date: d,
    vgt_real: byDateStrategy[d]?.vgt_real ?? null,
    manual: byDateStrategy[d]?.manual ?? null,
    ml: byDateStrategy[d]?.ml ?? null,
    momentum: byDateStrategy[d]?.momentum ?? null,
    pairs: byDateStrategy[d]?.pairs ?? null,
  }));
}

function fmt(d: string) {
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function StrategyRaceChart({ snapshots }: { snapshots: StrategySnapshot[] }) {
  const data = buildChartData(snapshots);

  if (data.length === 0) {
    return (
      <div style={{
        height: 320, display: "flex", alignItems: "center",
        justifyContent: "center", color: "var(--subtext)",
      }}>
        No data yet — check back after the first trading day.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <XAxis
          dataKey="date"
          tickFormatter={fmt}
          tick={{ fill: "var(--subtext)", fontSize: 11 }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          tickFormatter={(v: number) => `$${v.toFixed(0)}`}
          tick={{ fill: "var(--subtext)", fontSize: 11 }}
          axisLine={false} tickLine={false} width={60}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, fontSize: 12,
          }}
          labelFormatter={(d: unknown) => fmt(String(d))}
          formatter={(v: unknown, name: unknown) => [
            `$${Number(v).toFixed(2)}`,
            STRATEGY_META[name as keyof typeof STRATEGY_META]?.short ?? String(name),
          ]}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, color: "var(--subtext)", paddingTop: 12 }}
          formatter={(value) => STRATEGY_META[value as keyof typeof STRATEGY_META]?.short ?? String(value)}
        />
        <ReferenceLine y={STARTING_CAPITAL} stroke="var(--muted)" strokeDasharray="4 4" />
        {STRATEGY_ORDER.map(key => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={STRATEGY_META[key].color}
            strokeWidth={key === "vgt_real" ? 2.5 : 1.8}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
