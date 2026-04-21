"""
Entry point. Run this once and leave it running:
  conda activate trade_b0t && python -m bot.scheduler

Jobs:
  - 3:50 PM ET Mon–Fri  → run_daily()
  - 1st of every 2nd month at 7:00 AM ET → retrain_all()
"""
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from bot.executor import run_daily
from bot.trainer import retrain_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

ET = pytz.timezone("America/New_York")


def main():
    scheduler = BlockingScheduler(timezone=ET)

    # Daily trade cycle: 3:50 PM ET, Mon–Fri
    scheduler.add_job(
        run_daily,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=15,
            minute=50,
            timezone=ET,
        ),
        id="daily_trade",
        name="Daily trade cycle",
        misfire_grace_time=300,
    )

    # Bimonthly retraining: 1st of Jan, Mar, May, Jul, Sep, Nov at 7 AM ET
    scheduler.add_job(
        retrain_all,
        trigger=CronTrigger(
            month="1,3,5,7,9,11",
            day=1,
            hour=7,
            minute=0,
            timezone=ET,
        ),
        id="bimonthly_retrain",
        name="Bimonthly model retraining",
        misfire_grace_time=3600,
    )

    logging.info("Scheduler started. Waiting for jobs...")
    logging.info("  Trade cycle:  Mon–Fri 3:50 PM ET")
    logging.info("  Retraining:   1st of odd months 7:00 AM ET")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logging.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
