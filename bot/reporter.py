"""Send a daily performance email via Gmail SMTP."""
import os
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

SIGNAL_LABELS = {1: "LONG ▲", 0: "FLAT —", -1: "SHORT ▼"}


STARTING_VALUE = 1700.0


def send_daily_report(
    snap_date: date,
    virtual_equity: float,
    positions: dict,
    signals: dict[str, dict],  # {symbol: {manual, ml, bb, momentum, rsi}}
    trades_placed: list[dict],
) -> None:
    total = virtual_equity
    total_return_pct = ((total - STARTING_VALUE) / STARTING_VALUE) * 100

    subject = (
        f"trade_b0t_mk1 | {snap_date.strftime('%b %d')} | "
        f"${total:,.2f} ({total_return_pct:+.2f}% total)"
    )

    lines = [
        f"<h2>trade_b0t_mk1 — {snap_date.strftime('%A, %B %d %Y')}</h2>",
        f"<p><b>Virtual Portfolio:</b> ${total:,.2f} "
        f"(started at ${STARTING_VALUE:,.2f}) &nbsp;|&nbsp; "
        f"<b>Total Return:</b> {total_return_pct:+.2f}%</p>",
        "<h3>Open Positions</h3>",
        "<table border='1' cellpadding='6' cellspacing='0'>",
        "<tr><th>Symbol</th><th>Side</th><th>Qty</th>"
        "<th>Market Value</th><th>Unrealized P&L</th></tr>",
    ]

    for symbol, pos in positions.items():
        lines.append(
            f"<tr><td>{symbol}</td><td>{pos['side'].upper()}</td>"
            f"<td>{pos['qty']:.4f}</td><td>${pos['market_value']:,.2f}</td>"
            f"<td>${pos['unrealized_pl']:+,.2f}</td></tr>"
        )

    lines += [
        "</table>",
        "<h3>Today's Signals</h3>",
        "<table border='1' cellpadding='6' cellspacing='0'>",
        "<tr><th>Symbol</th><th>Manual</th><th>ML (shadow)</th>"
        "<th>BB%B</th><th>Momentum</th><th>RSI</th></tr>",
    ]

    for symbol, s in signals.items():
        lines.append(
            f"<tr><td>{symbol}</td>"
            f"<td>{SIGNAL_LABELS[s['manual']]}</td>"
            f"<td>{SIGNAL_LABELS[s['ml']]}</td>"
            f"<td>{s['bb']:.4f}</td>"
            f"<td>{s['momentum']:.4f}</td>"
            f"<td>{s['rsi']:.2f}</td></tr>"
        )

    lines += ["</table>"]

    if trades_placed:
        lines += [
            "<h3>Trades Placed Today</h3>",
            "<table border='1' cellpadding='6' cellspacing='0'>",
            "<tr><th>Symbol</th><th>Action</th><th>Shares</th>"
            "<th>Dollar Amount</th></tr>",
        ]
        for t in trades_placed:
            lines.append(
                f"<tr><td>{t['symbol']}</td><td>{t['action'].upper()}</td>"
                f"<td>{t['shares']:.4f}</td><td>${t['dollar']:,.2f}</td></tr>"
            )
        lines.append("</table>")
    else:
        lines.append("<p><i>No trades placed today (no signal changes).</i></p>")

    dashboard_url = os.getenv("DASHBOARD_URL", "https://your-app.vercel.app")
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
