import { createClient } from "@supabase/supabase-js";

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_ANON_KEY!;

export const supabase = createClient(url, key);

// ── Types ────────────────────────────────────────────────────────────────────

export type Signal = {
  date: string;
  symbol: string;
  bb_pct_b: number;
  momentum: number;
  rsi: number;
  manual_signal: number;
  ml_signal: number;
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

export type Snapshot = {
  date: string;
  total_value: number;
  cash?: number;
  positions?: Record<string, {
    side: string;
    qty: number;
    market_value: number;
    current_price: number;
    unrealized_pl: number;
  }>;
};

// ── Queries ───────────────────────────────────────────────────────────────────

export async function getLatestSnapshot(): Promise<Snapshot | null> {
  const { data } = await supabase
    .from("portfolio_snapshots")
    .select("*")
    .order("date", { ascending: false })
    .limit(1)
    .single();
  return data;
}

export async function getSnapshotHistory(): Promise<Snapshot[]> {
  const { data } = await supabase
    .from("portfolio_snapshots")
    .select("date, total_value")
    .order("date", { ascending: true });
  return data ?? [];
}

export async function getLatestSignals(): Promise<Signal[]> {
  const latest = await supabase
    .from("signals")
    .select("date")
    .order("date", { ascending: false })
    .limit(1)
    .single();

  if (!latest.data) return [];

  const { data } = await supabase
    .from("signals")
    .select("*")
    .eq("date", latest.data.date);
  return data ?? [];
}

export async function getSignalHistory(): Promise<Signal[]> {
  const { data } = await supabase
    .from("signals")
    .select("*")
    .order("date", { ascending: true });
  return data ?? [];
}

export async function getRecentTrades(limit = 50): Promise<Trade[]> {
  const { data } = await supabase
    .from("trades")
    .select("*")
    .order("date", { ascending: false })
    .limit(limit);
  return data ?? [];
}
