"""Daily email report — shows all 5 strategies' performance."""
import os
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from bot import db

load_dotenv()

STARTING_VALUE = 1700.0

STRATEGY_META = {
    "vgt_real":  {"label": "VGT (Real Money)",     "color": "#a78bfa"},
    "manual":    {"label": "Manual Mean Reversion", "color": "#22d87a"},
    "ml":        {"label": "ML Shadow",            "color": "#4d9fff"},
    "momentum":  {"label": "Momentum",             "color": "#ffa94d"},
    "pairs":     {"label": "Pairs Trading",        "color": "#ff6aa1"},
}
DISPLAY_ORDER = ["vgt_real", "manual", "ml", "momentum", "pairs"]

SIGNAL_LABELS = {1: "LONG ▲", 0: "FLAT —", -1: "SHORT ▼"}


def _fetch_today_snapshots(snap_date: date) -> dict:
    res = (
        db._db()
        .table("strategy_snapshots")
        .select("*")
        .eq("date", str(snap_date))
        .execute()
    )
    return {row["strategy"]: row for row in res.data}


def send_daily_report(snap_date: date) -> None:
    snapshots = _fetch_today_snapshots(snap_date)

    subject_bits = []
    for key in DISPLAY_ORDER:
        snap = snapshots.get(key)
        if snap is None:
            continue
        pct = ((snap["total_value"] - STARTING_VALUE) / STARTING_VALUE) * 100
        subject_bits.append(f"{STRATEGY_META[key]['label'].split()[0]} {pct:+.2f}%")

    subject = f"trade_b0t_mk1 | {snap_date.strftime('%b %d')} | {' · '.join(subject_bits)}"

    # ── Build HTML body ──────────────────────────────────────────────────────
    lines = [
        f"<h2>trade_b0t_mk1 — {snap_date.strftime('%A, %B %d %Y')}</h2>",
        "<p>Real-money trade: VGT buy-and-hold. The other 4 are simulated, "
        "each with its own virtual $1,700. Apples-to-apples comparison.</p>",
        "<h3>Strategy Scoreboard</h3>",
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;font-family:system-ui;'>",
        "<tr style='background:#0f1120;color:#e2e4f0'>"
        "<th align='left'>Strategy</th>"
        "<th align='right'>Virtual Value</th>"
        "<th align='right'>Total Return</th>"
        "<th align='right'>Cash</th></tr>",
    ]

    for key in DISPLAY_ORDER:
        snap = snapshots.get(key)
        if snap is None:
            lines.append(
                f"<tr><td>{STRATEGY_META[key]['label']}</td>"
                f"<td colspan='3' align='center'><i>no data</i></td></tr>"
            )
            continue
        val = float(snap["total_value"])
        pct = ((val - STARTING_VALUE) / STARTING_VALUE) * 100
        color = "#22d87a" if pct >= 0 else "#ff4d6a"
        cash = float(snap.get("cash") or 0)
        lines.append(
            f"<tr>"
            f"<td><span style='display:inline-block;width:10px;height:10px;"
            f"background:{STRATEGY_META[key]['color']};"
            f"border-radius:2px;margin-right:6px;'></span>"
            f"{STRATEGY_META[key]['label']}</td>"
            f"<td align='right'>${val:,.2f}</td>"
            f"<td align='right' style='color:{color};font-weight:700'>"
            f"{pct:+.2f}%</td>"
            f"<td align='right'>${cash:,.2f}</td>"
            f"</tr>"
        )

    lines += ["</table>"]

    # ── Per-strategy details ─────────────────────────────────────────────────
    for key in DISPLAY_ORDER:
        snap = snapshots.get(key)
        if snap is None:
            continue
        lines.append(f"<h4>{STRATEGY_META[key]['label']}</h4>")
        positions = snap.get("positions") or {}
        if not positions:
            lines.append("<p><i>No open positions.</i></p>")
        else:
            lines.append(
                "<table border='1' cellpadding='6' cellspacing='0' "
                "style='border-collapse:collapse;font-size:13px'>"
                "<tr><th>Symbol</th><th>Side</th><th>Shares</th>"
                "<th>Entry</th><th>Current</th><th>P&L</th></tr>"
            )
            for sym, p in positions.items():
                side = p.get("side", "").upper()
                shares = p.get("shares") or p.get("qty") or 0
                entry = p.get("entry_price") or p.get("cost_basis") or 0
                cur = p.get("current_price", 0)
                pnl = p.get("unrealized_pnl") or p.get("unrealized_pl") or 0
                pnl_color = "#22d87a" if pnl >= 0 else "#ff4d6a"
                lines.append(
                    f"<tr><td><b>{sym}</b></td><td>{side}</td>"
                    f"<td>{float(shares):.4f}</td>"
                    f"<td>${float(entry):.2f}</td>"
                    f"<td>${float(cur):.2f}</td>"
                    f"<td style='color:{pnl_color}'>${float(pnl):+.2f}</td></tr>"
                )
            lines.append("</table>")

    dashboard_url = os.getenv("DASHBOARD_URL", "https://dashboard-nine-virid-85.vercel.app")
    lines.append(f"<p><a href='{dashboard_url}'>Open Dashboard</a></p>")

    body = "\n".join(lines)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.environ["EMAIL_SENDER"]
    msg["To"] = os.environ["EMAIL_RECIPIENT"]
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_SENDER"], os.environ["EMAIL_APP_PASSWORD"])
        server.sendmail(
            os.environ["EMAIL_SENDER"],
            os.environ["EMAIL_RECIPIENT"],
            msg.as_string(),
        )
    print(f"[reporter] Daily email sent for {snap_date}")
