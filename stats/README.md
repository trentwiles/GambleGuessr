# Stats Aggregator

Fetches my account's stats at a given interval by scraping Geoguessr internal API.

## Components

- `app.py` — Geoguessr scrapers (account, rating, duels, singleplayer feed).
- `db.py` — SQLite schema, inserts, lookups, pagination counts, and chart aggregations.
- `cron.py` — entrypoint for the periodic scrape. Run via cron every 10–30 min.
- `api.py` — read-only FastAPI wrapper over the stats DB.

## Install

```sh
pip install -r requirements.txt
```

## Run the API

```sh
cd stats
uvicorn api:app --reload
```

Interactive docs: <http://127.0.0.1:8000/docs>.

## Endpoints

All list endpoints use `?limit=&offset=` and respond with
`{ items, limit, offset, total, has_more }`.

| Method | Path | Notes |
| ------ | ---- | ----- |
| GET | `/stats` | DB row counts + latest timestamps + winrate. |
| GET | `/account/snapshots` | Paginated. |
| GET | `/account/snapshots/{id}` | Single snapshot. |
| GET | `/ratings` | Paginated; `?type=overall\|standardDuel\|noMoveDuel`. |
| GET | `/ratings/{id}` | Single rating poll. |
| GET | `/ratings/timeseries` | Chart series with moving avg. |
| GET | `/singleplayer` | Paginated. |
| GET | `/singleplayer/{id}` | Single game. |
| GET | `/singleplayer/timeseries` | Chart series with moving avg. |
| GET | `/duels` | Paginated; `?i_won=true\|false`, `?include_rounds=`. |
| GET | `/duels/{id}` | Single duel + rounds. |
| GET | `/duels/timeseries` | Winrate moving avg. |

### Chart aggregation params

`/*/timeseries` endpoints accept:

- `bucket=raw|hour|day|week|month` — `raw` returns one point per row;
  the rest group rows by time bucket and average within the bucket.
- `window=N` — size of the trailing moving-average window in points/buckets.

Each point in the response is `{ bucket, value, n, moving_avg }`:

- `bucket` — timestamp string (or row sort key for `raw`).
- `value` — bucket aggregate (avg points / avg rating / winrate).
- `n` — rows in the bucket (always 1 for `raw`).
- `moving_avg` — trailing moving average of `value` over the last `window` points.

For `/duels/timeseries` `value` and `moving_avg` are winrates in `[0, 1]`.
