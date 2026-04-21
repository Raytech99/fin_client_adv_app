"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import type { Signal, Snapshot } from "@/lib/supabase";

type RacePoint = {
  date: string;
  manual: number | null;
  ml: number | null;
  portfolio: number | null;
};

function buildRaceData(snapshots: Snapshot[], signals: Signal[]): RacePoint[] {
  const STARTING = 1700;
  const sigMap: Record<string, { manual: number; ml: number }> = {};
  for (const s of signals) {
    sigMap[s.date] = { manual: s.manual_signal, ml: s.ml_signal };
  }

  const snapMap: Record<string, number> = {};
  for (const s of snapshots) snapMap[s.date] = s.total_value;

  let manualValue = STARTING;
  let mlValue = STARTING;
  let manualPos = 0;
  let mlPos = 0;

  const allDates = [...new Set([...Object.keys(sigMap), ...Object.keys(snapMap)])].sort();

  return allDates.map(date => {
    const sig = sigMap[date];
    if (sig) {
      if (sig.manual !== manualPos) manualPos = sig.manual;
      if (sig.ml !== mlPos) mlPos = sig.ml;
    }
    return {
      date,
      manual: manualValue,
      ml: mlValue,
      portfolio: snapMap[date] ?? null,
    };
  });
}

function fmt(d: string) {
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function StrategyRaceChart({ snapshots, signals }: { snapshots: Snapshot[]; signals: Signal[] }) {
  const data = buildRaceData(snapshots, signals);

  if (data.length === 0) {
    return (
      <div style={{ height: 260, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--subtext)" }}>
        No data yet — check back after the first trading day.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="date" tickFormatter={fmt} tick={{ fill: "var(--subtext)", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={v => `$${v.toFixed(0)}`} tick={{ fill: "var(--subtext)", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
        <Tooltip
          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
          labelFormatter={(d: unknown) => fmt(String(d))}
          formatter={(v: unknown) => `$${Number(v).toFixed(2)}`}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "var(--subtext)" }} />
        <ReferenceLine y={1700} stroke="var(--muted)" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="portfolio" name="Actual Portfolio" stroke="var(--purple)" strokeWidth={2} dot={false} connectNulls />
        <Line type="monotone" dataKey="manual" name="Manual Strategy" stroke="var(--green)" strokeWidth={1.5} dot={false} strokeDasharray="5 3" connectNulls />
        <Line type="monotone" dataKey="ml" name="ML Shadow" stroke="var(--blue)" strokeWidth={1.5} dot={false} strokeDasharray="5 3" connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
}
