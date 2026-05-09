"""
FastAPI wrapper around the GambleGuessr stats DB.

Run:
    uvicorn api:app --reload
"""

from typing import Literal

from fastapi import FastAPI, HTTPException, Query

import db


RatingType = Literal["overall", "standardDuel", "noMoveDuel"]
Bucket = Literal["raw", "hour", "day", "week", "month"]


app = FastAPI(
    title="GambleGuessr Stats API",
    description="Read API over scraped Geoguessr stats. Pagination + chart aggregations.",
    version="0.1.0",
)


db.init_db()


def _page(items: list, total: int, limit: int, offset: int) -> dict:
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": (offset + len(items)) < total,
    }


# ---------- meta ----------

@app.get("/")
def root():
    return {"service": "gambleguessr-stats", "ok": True}


@app.get("/stats")
def stats():
    return db.get_database_stats()


# ---------- account snapshots ----------

@app.get("/account/snapshots")
def list_account_snapshots(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items = db.get_account_snapshots(limit=limit, offset=offset)
    total = db.count_account_snapshots()
    return _page(items, total, limit, offset)


@app.get("/account/snapshots/{snapshot_id}")
def get_account_snapshot(snapshot_id: int):
    item = db.get_account_snapshot(snapshot_id)
    if not item:
        raise HTTPException(404, f"snapshot {snapshot_id} not found")
    return item


# ---------- ratings ----------

@app.get("/ratings")
def list_ratings(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    type: RatingType | None = Query(None, description="filter by rating type"),
):
    items = db.get_ratings(limit=limit, offset=offset, type=type)
    total = db.count_ratings(type=type)
    return _page(items, total, limit, offset)


@app.get("/ratings/timeseries")
def ratings_timeseries(
    type: RatingType = Query("overall"),
    bucket: Bucket = Query("raw", description="time-bucket granularity (raw = per record)"),
    window: int = Query(5, ge=1, le=500, description="moving-average window size"),
):
    return {
        "type": type,
        "bucket": bucket,
        "window": window,
        "points": db.get_ratings_timeseries(type=type, bucket=bucket, window=window),
    }


@app.get("/ratings/{rating_id}")
def get_rating(rating_id: int):
    item = db.get_rating(rating_id)
    if not item:
        raise HTTPException(404, f"rating {rating_id} not found")
    return item


# ---------- singleplayer games ----------

@app.get("/singleplayer")
def list_singleplayer(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    items = db.get_singleplayer_games(limit=limit, offset=offset)
    total = db.count_singleplayer_games()
    return _page(items, total, limit, offset)


@app.get("/singleplayer/timeseries")
def singleplayer_timeseries(
    bucket: Bucket = Query("raw"),
    window: int = Query(5, ge=1, le=500),
    mode: str | None = Query(None, description="optional game mode filter"),
):
    return {
        "metric": "points",
        "bucket": bucket,
        "window": window,
        "mode": mode,
        "points": db.get_singleplayer_timeseries(bucket=bucket, window=window, mode=mode),
    }


@app.get("/singleplayer/{game_id}")
def get_singleplayer(game_id: str):
    item = db.get_singleplayer_game(game_id)
    if not item:
        raise HTTPException(404, f"singleplayer game {game_id} not found")
    return item


# ---------- duels ----------

@app.get("/duels")
def list_duels(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    i_won: bool | None = Query(None, description="filter to wins (true) or losses (false)"),
    include_rounds: bool = Query(True, description="hydrate per-round detail"),
):
    items = db.get_duels(
        limit=limit, offset=offset, i_won=i_won, include_rounds=include_rounds
    )
    total = db.count_duels(i_won=i_won)
    return _page(items, total, limit, offset)


@app.get("/duels/timeseries")
def duels_timeseries(
    bucket: Bucket = Query("day", description="time-bucket granularity"),
    window: int = Query(5, ge=1, le=500, description="moving-average window size"),
):
    # value/moving_avg are winrates in [0, 1]; n is the duel count per bucket.
    return {
        "metric": "winrate",
        "bucket": bucket,
        "window": window,
        "points": db.get_duels_timeseries(bucket=bucket, window=window),
    }


@app.get("/duels/{duel_id}")
def get_duel(duel_id: str):
    item = db.get_duel(duel_id)
    if not item:
        raise HTTPException(404, f"duel {duel_id} not found")
    return item
