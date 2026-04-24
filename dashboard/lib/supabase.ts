import { createClient } from "@supabase/supabase-js";

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_ANON_KEY!;

export const supabase = createClient(url, key);

// ── Types ────────────────────────────────────────────────────────────────────

export type StrategyName = "vgt_real" | "manual" | "ml" | "momentum" | "pairs";

export type Position = {
  side: string;
  shares?: number;
  qty?: number;
  entry_price?: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  unrealized_pl?: number;
};

export type StrategySnapshot = {
  id: number;
  date: string;
  strategy: StrategyName;
  total_value: number;
  cash: number | null;
  positions: Record<string, Position> | null;
  signals: Record<string, unknown> | null;
};

export type Trade = {
  id: number;
  date: string;
  symbol: string;
  action: string;
  shares: number;
  dollar_amount: number;
  price: number;
  strategy: string;
};

export const STRATEGY_META: Record<StrategyName, { label: string; color: string; short: string }> = {
  vgt_real: { label: "VGT (Real Money)",      color: "#a78bfa", short: "VGT" },
  manual:   { label: "Manual Mean Reversion", color: "#22d87a", short: "Manual" },
  ml:       { label: "ML Shadow",             color: "#4d9fff", short: "ML" },
  momentum: { label: "Momentum",              color: "#ffa94d", short: "Momentum" },
  pairs:    { label: "Pairs Trading",         color: "#ff6aa1", short: "Pairs" },
};

export const STRATEGY_ORDER: StrategyName[] = ["vgt_real", "manual", "ml", "momentum", "pairs"];
export const STARTING_CAPITAL = 1700;

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
