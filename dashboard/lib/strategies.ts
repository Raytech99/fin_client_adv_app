// Client-safe constants and types. No Supabase client here — this file
// is imported by both server components and "use client" components, so it
// must not touch server-only env vars at module load time.

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
