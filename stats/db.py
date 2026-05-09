import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS duels_ranking_poll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL,
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS account_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                account_age_ms INTEGER NOT NULL,
                profile_url TEXT,
                country_code TEXT,
                level_progress TEXT,
                competitive TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS singleplayer_games (
                id TEXT PRIMARY KEY,
                map_url TEXT,
                map_name TEXT,
                points INTEGER,
                result_url TEXT,
                mode TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS duels (
                id TEXT PRIMARY KEY,
                time TEXT,
                results_url TEXT,
                rounds_played INTEGER,
                winner_team_id TEXT,
                i_won INTEGER
            );

            CREATE TABLE IF NOT EXISTS duel_rounds (
                duel_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                my_health INTEGER,
                round_winner_team_id TEXT,
                i_won_round INTEGER,
                PRIMARY KEY (duel_id, round),
                FOREIGN KEY (duel_id) REFERENCES duels(id) ON DELETE CASCADE
            );
            """
        )


# ---------- account snapshots ----------

def insert_account_snapshot(account: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO account_snapshots
                (nickname, account_age_ms, profile_url, country_code, level_progress, competitive)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                account["nickname"],
                account["age"],
                account.get("profile_url"),
                account.get("country_code"),
                json.dumps(account.get("level_progress")),
                json.dumps(account.get("competitive")),
            ),
        )
        return cur.lastrowid


def get_account_snapshot(snapshot_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM account_snapshots WHERE id = ?;", (snapshot_id,)
        ).fetchone()
        return _hydrate_account(row) if row else None


def get_account_snapshots(limit: int = 50, offset: int = 0) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM account_snapshots ORDER BY id DESC LIMIT ? OFFSET ?;",
            (limit, offset),
        ).fetchall()
        return [_hydrate_account(r) for r in rows]


def _hydrate_account(row: sqlite3.Row) -> dict:
    d = dict(row)
    for k in ("level_progress", "competitive"):
        if d.get(k) is not None:
            d[k] = json.loads(d[k])
    return d


# ---------- ratings ----------

def insert_duels_rating(rating: int, type: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO duels_ranking_poll (rating, type) VALUES (?, ?);",
            (rating, type),
        )
        return cur.lastrowid


def insert_rating_snapshot(rating: dict) -> list[int]:
    pairs = [
        (rating["overall"], "overall"),
        (rating["standardDuel"], "standardDuel"),
        (rating["noMoveDuel"], "noMoveDuel"),
    ]
    ids = []
    with get_connection() as conn:
        for r, t in pairs:
            cur = conn.execute(
                "INSERT INTO duels_ranking_poll (rating, type) VALUES (?, ?);",
                (r, t),
            )
            ids.append(cur.lastrowid)
    return ids


def get_rating(rating_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM duels_ranking_poll WHERE id = ?;", (rating_id,)
        ).fetchone()
        return dict(row) if row else None


def get_ratings(limit: int = 50, offset: int = 0, type: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if type is None:
            rows = conn.execute(
                "SELECT * FROM duels_ranking_poll ORDER BY id DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM duels_ranking_poll WHERE type = ? ORDER BY id DESC LIMIT ? OFFSET ?;",
                (type, limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]


# ---------- singleplayer games ----------

_SP_COLS = ("id", "map_url", "map_name", "points", "result_url", "mode", "timestamp")


def _sp_row(g: dict) -> tuple:
    return (
        g["id"],
        g.get("map_url"),
        g.get("map_name"),
        g.get("points"),
        g.get("result_url"),
        g.get("mode"),
        g.get("timestamp"),
    )


def insert_singleplayer_game(game: dict) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT OR IGNORE INTO singleplayer_games ({','.join(_SP_COLS)}) VALUES (?,?,?,?,?,?,?);",
            _sp_row(game),
        )
        return cur.rowcount == 1


def insert_singleplayer_games(games: list[dict]) -> int:
    if not games:
        return 0
    with get_connection() as conn:
        cur = conn.executemany(
            f"INSERT OR IGNORE INTO singleplayer_games ({','.join(_SP_COLS)}) VALUES (?,?,?,?,?,?,?);",
            [_sp_row(g) for g in games],
        )
        return cur.rowcount


def get_singleplayer_game(game_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM singleplayer_games WHERE id = ?;", (game_id,)
        ).fetchone()
        return dict(row) if row else None


def get_singleplayer_games(limit: int = 50, offset: int = 0) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM singleplayer_games ORDER BY timestamp DESC LIMIT ? OFFSET ?;",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- duels ----------

def _insert_duel_one(conn: sqlite3.Connection, duel: dict) -> bool:
    # accept both getDuelsHistory entries ({time,id,game_data}) and raw getDuelMetadata returns
    game_data = duel.get("game_data", duel)
    duel_id = duel.get("id") or game_data["id"]

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO duels
            (id, time, results_url, rounds_played, winner_team_id, i_won)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            duel_id,
            duel.get("time"),
            game_data.get("results_url"),
            game_data.get("rounds_played"),
            game_data.get("winner_team_id"),
            int(bool(game_data.get("i_won"))),
        ),
    )
    if cur.rowcount == 0:
        return False

    rounds = game_data.get("rounds", [])
    if rounds:
        conn.executemany(
            """
            INSERT OR IGNORE INTO duel_rounds
                (duel_id, round, my_health, round_winner_team_id, i_won_round)
            VALUES (?, ?, ?, ?, ?);
            """,
            [
                (
                    duel_id,
                    r["round"],
                    r.get("my_health"),
                    r.get("round_winner_team_id"),
                    int(bool(r.get("i_won_round"))),
                )
                for r in rounds
            ],
        )
    return True


def insert_duel(duel: dict) -> bool:
    with get_connection() as conn:
        return _insert_duel_one(conn, duel)


def insert_duels(duels: list[dict]) -> int:
    if not duels:
        return 0
    with get_connection() as conn:
        return sum(1 for d in duels if _insert_duel_one(conn, d))


def _attach_rounds(conn: sqlite3.Connection, duel_row: sqlite3.Row) -> dict:
    d = dict(duel_row)
    rounds = conn.execute(
        """
        SELECT round, my_health, round_winner_team_id, i_won_round
        FROM duel_rounds WHERE duel_id = ? ORDER BY round;
        """,
        (d["id"],),
    ).fetchall()
    d["rounds"] = [dict(r) for r in rounds]
    return d


def get_duel(duel_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM duels WHERE id = ?;", (duel_id,)).fetchone()
        return _attach_rounds(conn, row) if row else None


def get_duels(
    limit: int = 50,
    offset: int = 0,
    i_won: bool | None = None,
    include_rounds: bool = True,
) -> list[dict]:
    sql = "SELECT * FROM duels"
    params: list = []
    if i_won is not None:
        sql += " WHERE i_won = ?"
        params.append(int(bool(i_won)))
    sql += " ORDER BY time DESC LIMIT ? OFFSET ?;"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        if include_rounds:
            return [_attach_rounds(conn, r) for r in rows]
        return [dict(r) for r in rows]


# ---------- counts (for paginated list metadata) ----------

def count_account_snapshots() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM account_snapshots;").fetchone()[0]


def count_ratings(type: str | None = None) -> int:
    with get_connection() as conn:
        if type is None:
            return conn.execute("SELECT COUNT(*) FROM duels_ranking_poll;").fetchone()[0]
        return conn.execute(
            "SELECT COUNT(*) FROM duels_ranking_poll WHERE type = ?;", (type,)
        ).fetchone()[0]


def count_singleplayer_games() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM singleplayer_games;").fetchone()[0]


def count_duels(i_won: bool | None = None) -> int:
    with get_connection() as conn:
        if i_won is None:
            return conn.execute("SELECT COUNT(*) FROM duels;").fetchone()[0]
        return conn.execute(
            "SELECT COUNT(*) FROM duels WHERE i_won = ?;", (int(bool(i_won)),)
        ).fetchone()[0]


# ---------- chart aggregations ----------
#
# bucket=raw  → one point per row with a rolling moving avg over the last
#               `window` rows (window functions on the natural sort column).
# bucket=hour|day|week|month → group by time bucket, then a rolling avg
#               over the last `window` buckets.
#
# Window-frame bounds (`ROWS BETWEEN N PRECEDING…`) cannot be parameterized
# in SQLite, so `window` is coerced to an int and inlined.

_BUCKET_FORMATS = {
    "hour":  "%Y-%m-%dT%H:00:00",
    "day":   "%Y-%m-%d",
    "week":  "%Y-W%W",
    "month": "%Y-%m",
}


def _validate_bucket(bucket: str) -> str:
    if bucket != "raw" and bucket not in _BUCKET_FORMATS:
        raise ValueError(f"invalid bucket: {bucket}")
    return bucket


def _validate_window(window: int) -> int:
    w = int(window)
    if w < 1:
        raise ValueError("window must be >= 1")
    return w


def _timeseries(
    *,
    table: str,
    value_expr: str,
    time_col: str,
    sort_col: str,
    where_sql: str = "",
    where_params: tuple = (),
    bucket: str,
    window: int,
    bucket_agg: str = "AVG",
) -> list[dict]:
    bucket = _validate_bucket(bucket)
    w = _validate_window(window) - 1  # frame is N-1 PRECEDING + current row

    where_clause = f"WHERE {where_sql}" if where_sql else ""

    if bucket == "raw":
        sql = f"""
            SELECT {time_col} AS bucket,
                   {value_expr} AS value,
                   1 AS n,
                   AVG({value_expr}) OVER (
                       ORDER BY {sort_col}
                       ROWS BETWEEN {w} PRECEDING AND CURRENT ROW
                   ) AS moving_avg
            FROM {table}
            {where_clause}
            ORDER BY {sort_col};
        """
        params = where_params
    else:
        fmt = _BUCKET_FORMATS[bucket]
        sql = f"""
            WITH bucketed AS (
                SELECT strftime(?, {time_col}) AS bucket,
                       {bucket_agg}({value_expr}) AS value,
                       COUNT(*) AS n
                FROM {table}
                {where_clause}
                GROUP BY bucket
            )
            SELECT bucket, value, n,
                   AVG(value) OVER (
                       ORDER BY bucket
                       ROWS BETWEEN {w} PRECEDING AND CURRENT ROW
                   ) AS moving_avg
            FROM bucketed
            ORDER BY bucket;
        """
        params = (fmt, *where_params)

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_ratings_timeseries(
    type: str = "overall",
    bucket: str = "raw",
    window: int = 5,
) -> list[dict]:
    return _timeseries(
        table="duels_ranking_poll",
        value_expr="rating",
        time_col="timestamp",
        sort_col="id",
        where_sql="type = ?",
        where_params=(type,),
        bucket=bucket,
        window=window,
    )


def get_singleplayer_timeseries(
    bucket: str = "raw",
    window: int = 5,
    mode: str | None = None,
) -> list[dict]:
    where_sql = ""
    where_params: tuple = ()
    if mode is not None:
        where_sql = "mode = ?"
        where_params = (mode,)
    return _timeseries(
        table="singleplayer_games",
        value_expr="points",
        time_col="timestamp",
        sort_col="timestamp",
        where_sql=where_sql,
        where_params=where_params,
        bucket=bucket,
        window=window,
    )


def get_duels_timeseries(
    bucket: str = "day",
    window: int = 5,
) -> list[dict]:
    # value = winrate (0..1); for bucket=raw each row is 0 or 1 and the
    # rolling avg is the trailing winrate over the last `window` duels.
    return _timeseries(
        table="duels",
        value_expr="i_won",
        time_col="time",
        sort_col="time",
        bucket=bucket,
        window=window,
    )


# ---------- stats ----------

def get_database_stats() -> dict:
    with get_connection() as conn:
        def count(table: str) -> int:
            return conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]

        def scalar(sql: str):
            row = conn.execute(sql).fetchone()
            return row[0] if row else None

        wins = scalar("SELECT COUNT(*) FROM duels WHERE i_won = 1;") or 0
        total_duels = count("duels")

        return {
            "counts": {
                "account_snapshots": count("account_snapshots"),
                "duels_ranking_poll": count("duels_ranking_poll"),
                "singleplayer_games": count("singleplayer_games"),
                "duels": total_duels,
                "duel_rounds": count("duel_rounds"),
            },
            "latest": {
                "rating": scalar("SELECT timestamp FROM duels_ranking_poll ORDER BY id DESC LIMIT 1;"),
                "account_snapshot": scalar("SELECT timestamp FROM account_snapshots ORDER BY id DESC LIMIT 1;"),
                "singleplayer_game": scalar("SELECT timestamp FROM singleplayer_games ORDER BY timestamp DESC LIMIT 1;"),
                "duel": scalar("SELECT time FROM duels ORDER BY time DESC LIMIT 1;"),
            },
            "duels_winrate": (wins / total_duels) if total_duels else None,
            "db_path": str(DB_PATH),
            "db_size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
        }


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
