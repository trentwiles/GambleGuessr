import requests
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timezone
from db import init_db
import time
import json

load_dotenv()
init_db()

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0"
API_BASE = "https://www.geoguessr.com/api"

def getAccount():
    r = requests.get(
        f"{API_BASE}/v3/profiles/",
        headers={"User-Agent": USER_AGENT},
        cookies={"_ncfa": os.getenv("GEO_NCFA")}
    )
    
    if r.status_code != 200 or "application/json" not in r.headers["Content-type"]:
        raise ValueError(f"Invalid token... http status {str(r.status_code)} content type " + str(r.headers["Content-type"]))
    
    # strip out PPI and only get relevant account info

    api = r.json()["user"]

    # account age calculation; will break if account age doesn't follow ISO 8601
    ts = datetime.fromisoformat(api["created"].replace("Z", "+00:00"))
    age_ms = int((datetime.now(timezone.utc) - ts).total_seconds() * 1000)

    return {
        "nickname": api["nick"],
        "age": age_ms,
        "profile_url": api["url"],
        "country_code": api["countryCode"],
        "level_progress": api["progress"],
        "competitive": api["competitive"]
    }

def getRating():
    r = requests.get(
        f"{API_BASE}/v4/ranked-system/me",
        headers={"User-Agent": USER_AGENT},
        cookies={"_ncfa": os.getenv("GEO_NCFA")}
    )

    if r.status_code != 200 or "application/json" not in r.headers["Content-type"]:
        raise ValueError(f"Invalid token... http status {str(r.status_code)} content type " + str(r.headers["Content-type"]))

    api = r.json()
    # aggregated stats, meant to be inserted to DB in another file; probably called from cron
    return {
        "overall": api["rating"],
        "standardDuel": api["gameModeRatings"]["standardDuels"]["rating"],
        "noMoveDuel": api["gameModeRatings"]["noMoveDuels"]["rating"],
        "timestamp": int(time.time())
    }

# grabs the moving average of the last 5, 10, and 20 games
def getMovingAverages(pagination=None, activity=None):
    if activity is None:
        activity = []

    hit_url = f"{API_BASE}/v4/feed/private"
    if pagination is not None:
        hit_url = f"{hit_url}?paginationToken={pagination}"

    r = requests.get(
        hit_url,
        headers={"User-Agent": USER_AGENT},
        cookies={"_ncfa": os.getenv("GEO_NCFA")}
    )

    if r.status_code != 200 or "application/json" not in r.headers["Content-type"]:
        raise ValueError(f"Invalid token... http status {str(r.status_code)} content type " + str(r.headers["Content-type"]))

    api = r.json()["entries"]
    for entry in api:
        # determine type
        # type 7 = duals
        # type 2 = daily challenge
        # type 1 = standard singleplayer game (any map, custom or built into to Geoguessr)
        # only looking for type 1 for this application
        # this data is also sorted by time
        if entry["type"] != 1:
            continue
        game_data = json.loads(entry["payload"])

        # note: gameToken is the primary key, it's unique
        activity.append(
            {
                "id": game_data['gameToken'],
                "map_url": f"https://www.geoguessr.com/maps/{str(game_data['mapSlug'])}",
                "map_name": game_data["mapName"],
                "points": game_data["points"],
                "result_url": f"https://www.geoguessr.com/results/{str(game_data['gameToken'])}",
                "mode": game_data["gameMode"],
                "timestamp": entry["time"]
            }
        )

    
    # if at the end we don't have enough for a 20 game average, recursive make another API request to the next page
    # ie. return getMovingAverages() + getMovingAverages(paginationToken)
    if len(activity) < 20:
        time.sleep(1)
        return getMovingAverages(r.json()['paginationToken'], activity)

    def avg(n):
        return sum(g["points"] for g in activity[:n]) / n

    return {
        "activities": activity,
        "averages": {
            "last_game": round(activity[0]["points"]),
            "three_game": round(avg(3)),
            "five_game": round(avg(5)),
            "ten_game": round(avg(10)),
            "twenty_game": round(avg(20))
        }
    }

def getDuelMetadata(game_id: str):
    # the duels summary page is server-rendered; the full game state is embedded
    # in the __NEXT_DATA__ JSON blob (no public JSON endpoint exposes the same shape)
    r = requests.get(
        f"https://www.geoguessr.com/duels/{game_id}/summary",
        headers={"User-Agent": USER_AGENT},
        cookies={"_ncfa": os.getenv("GEO_NCFA")}
    )

    if r.status_code != 200:
        raise ValueError(f"Invalid token... http status {str(r.status_code)}")

    # unlike the other JSON APIs, the duels metadata is baked into the server side rendering of nextjs, which comes out as html/client js
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        r.text,
        re.DOTALL
    )
    if not m:
        raise ValueError(f"Could not locate __NEXT_DATA__ for duel {game_id}")

    page_props = json.loads(m.group(1))["props"]["pageProps"]
    game = page_props["game"]
    user_id = page_props.get("userId")

    my_team = next(
        t for t in game["teams"]
        if any(p["playerId"] == user_id for p in t["players"])
    )
    other_team = next(t for t in game["teams"] if t["id"] != my_team["id"])

    # duels end when one team hits 0 HP — whoever's still standing wins
    final_hp = lambda t: t["roundResults"][-1]["healthAfter"] if t["roundResults"] else 0
    winner_team_id = my_team["id"] if final_hp(my_team) > final_hp(other_team) else other_team["id"]

    # per-round winner = team with higher score that round (the loser deals 0 damage)
    other_scores = {rr["roundNumber"]: rr["score"] for rr in other_team["roundResults"]}
    rounds = [
        {
            "round": rr["roundNumber"],
            "my_health": rr["healthAfter"],
            "round_winner_team_id": (
                my_team["id"] if rr["score"] > other_scores.get(rr["roundNumber"], 0)
                else other_team["id"] if rr["score"] < other_scores.get(rr["roundNumber"], 0)
                else None  # tie
            ),
        }
        for rr in my_team["roundResults"]
    ]
    for r in rounds:
        r["i_won_round"] = r["round_winner_team_id"] == my_team["id"]

    return {
        "id": game["gameId"],
        "results_url": f"https://www.geoguessr.com/duels/{game['gameId']}/summary",
        "rounds_played": len(rounds),
        "winner_team_id": winner_team_id,
        "i_won": winner_team_id == my_team["id"],
        "rounds": rounds,
    }

def getDuelsHistory(pagination=None, activity=None):
    if activity is None:
        activity = []

    hit_url = f"{API_BASE}/v4/feed/private"
    if pagination is not None:
        hit_url = f"{hit_url}?paginationToken={pagination}"

    r = requests.get(
        hit_url,
        headers={"User-Agent": USER_AGENT},
        cookies={"_ncfa": os.getenv("GEO_NCFA")}
    )

    if r.status_code != 200 or "application/json" not in r.headers["Content-type"]:
        raise ValueError(f"Invalid token... http status {str(r.status_code)} content type " + str(r.headers["Content-type"]))

    
    api = r.json()["entries"]
    for entry in api:
        # see notes on types in getMovingAverages
        if entry['type'] == 7:
            game_data = json.loads(entry["payload"])
            for game in game_data:
                if game['type'] == 6:
                    game_id = game['payload']['gameId']
                    activity.append({
                        "time": game['time'],
                        "id": game_id,
                        "game_data": getDuelMetadata(game_id)
                    })
                    time.sleep(1)

    if len(activity) < 20:
        print("refetch @ " + str(len(activity)))
        time.sleep(1)
        return getDuelsHistory(r.json()['paginationToken'], activity)


    return activity

print(getDuelsHistory())