#!/usr/bin/env python3

# designed to be executed as a cron, stats will be aggregated and
# inserted into database every 10, 15, or 30 minutes

import logging
import sys
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "cron.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("gambleguessr.cron")

from app import getAccount, getRating, getMovingAverages, getDuelsHistory
import db


def collect_account():
    account = getAccount()
    rowid = db.insert_account_snapshot(account)
    log.info(
        "account snapshot id=%s nickname=%s country=%s age_ms=%s",
        rowid,
        account["nickname"],
        account.get("country_code"),
        account.get("age"),
    )


def collect_rating():
    rating = getRating()
    ids = db.insert_rating_snapshot(rating)
    log.info(
        "rating snapshot ids=%s overall=%s standardDuel=%s noMoveDuel=%s",
        ids,
        rating["overall"],
        rating["standardDuel"],
        rating["noMoveDuel"],
    )


def collect_singleplayer():
    result = getMovingAverages()
    activities = result["activities"]
    new = db.insert_singleplayer_games(activities)
    avgs = result["averages"]
    log.info(
        "singleplayer scraped=%d new=%d last=%d 3g=%d 5g=%d 10g=%d 20g=%d",
        len(activities),
        new,
        avgs["last_game"],
        avgs["three_game"],
        avgs["five_game"],
        avgs["ten_game"],
        avgs["twenty_game"],
    )


def collect_duels():
    duels = getDuelsHistory()
    new = db.insert_duels(duels)
    wins = sum(1 for d in duels if d["game_data"]["i_won"])
    losses = len(duels) - wins
    log.info(
        "duels scraped=%d new=%d wins_in_window=%d losses_in_window=%d",
        len(duels),
        new,
        wins,
        losses,
    )


def main():
    log.info("cron run start")
    steps = (
        ("account", collect_account),
        ("rating", collect_rating),
        ("singleplayer", collect_singleplayer),
        ("duels", collect_duels),
    )
    failures = 0
    for name, fn in steps:
        try:
            fn()
        except Exception:
            failures += 1
            log.exception("step=%s failed", name)

    stats = db.get_database_stats()
    log.info(
        "db totals account=%d ratings=%d singleplayer=%d duels=%d duel_rounds=%d winrate=%s",
        stats["counts"]["account_snapshots"],
        stats["counts"]["duels_ranking_poll"],
        stats["counts"]["singleplayer_games"],
        stats["counts"]["duels"],
        stats["counts"]["duel_rounds"],
        stats["duels_winrate"],
    )
    log.info("cron run end failures=%d/%d", failures, len(steps))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
