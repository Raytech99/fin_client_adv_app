// Server-only Supabase client and data queries.
// Do NOT import from "use client" components — use lib/strategies.ts
// for constants and types that need to cross the client boundary.

import { createClient } from "@supabase/supabase-js";
import type { StrategyName, StrategySnapshot, Trade } from "./strategies";

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_ANON_KEY!;

export const supabase = createClient(url, key);

export type { StrategyName, StrategySnapshot, Trade, Position } from "./strategies";
export { STRATEGY_META, STRATEGY_ORDER, STARTING_CAPITAL } from "./strategies";

// ── Queries ───────────────────────────────────────────────────────────────────

export async function getLatestSnapshots(): Promise<Record<StrategyName, StrategySnapshot | null>> {
  const latest = await supabase
    .from("strategy_snapshots")
    .select("date")
    .order("date", { ascending: false })
    .limit(1)
    .single();

  const out: Record<string, StrategySnapshot | null> = {
    vgt_real: null, manual: null, ml: null, momentum: null, pairs: null,
  };
  if (!latest.data) return out as Record<StrategyName, StrategySnapshot | null>;

  const { data } = await supabase
    .from("strategy_snapshots")
    .select("*")
    .eq("date", latest.data.date);

  for (const row of data ?? []) out[row.strategy] = row as StrategySnapshot;
  return out as Record<StrategyName, StrategySnapshot | null>;
}

export async function getAllSnapshotHistory(): Promise<StrategySnapshot[]> {
  const { data } = await supabase
    .from("strategy_snapshots")
    .select("date, strategy, total_value")
    .order("date", { ascending: true });
  return (data ?? []) as StrategySnapshot[];
}

export async function getRecentTrades(limit = 100): Promise<Trade[]> {
  const { data } = await supabase
    .from("trades")
    .select("*")
    .order("date", { ascending: false })
    .limit(limit);
  return data ?? [];
}
