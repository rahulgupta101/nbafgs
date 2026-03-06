#!/usr/bin/env python3
"""
Weekly Sports Schedule Fetcher
Uses ESPN's free public API — no key required.
Fetches this week's games for: NBA, NHL, MLB, NFL, NCAAB

Usage:
    python fetch_weekly_schedule.py
    python fetch_weekly_schedule.py --leagues nba nhl mlb
    python fetch_weekly_schedule.py --output schedule.csv
    python fetch_weekly_schedule.py --days 7
"""

import urllib.request
import json
import argparse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ──────────────────────────────────────────────
# ESPN API CONFIG
# ──────────────────────────────────────────────

LEAGUES = {
    "nba":   ("basketball", "nba"),
    "nhl":   ("hockey",     "nhl"),
    "mlb":   ("baseball",   "mlb"),
    "nfl":   ("football",   "nfl"),
    "ncaab": ("basketball", "mens-college-basketball"),
    "wnba":  ("basketball", "wnba"),
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"

ET = ZoneInfo("America/New_York")


# ──────────────────────────────────────────────
# FETCH
# ──────────────────────────────────────────────

def fetch_schedule(sport: str, league: str, date_str: str) -> list[dict]:
    """Fetch games for a single league on a single date (YYYYMMDD)."""
    url = ESPN_BASE.format(sport=sport, league=league) + f"?dates={date_str}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {league} for {date_str}: {e}")
        return []

    games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])

        home = away = home_score = away_score = None
        for c in competitors:
            team_abbr = c.get("team", {}).get("abbreviation", "?")
            score = c.get("score", "")
            if c.get("homeAway") == "home":
                home = team_abbr
                home_score = score
            else:
                away = team_abbr
                away_score = score

        # Parse start time to ET
        start_raw = event.get("date", "")
        try:
            dt_utc = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
            dt_et = dt_utc.astimezone(ET)
            time_str = dt_et.strftime("%-I:%M %p ET")
        except Exception:
            time_str = start_raw

        status = comp.get("status", {}).get("type", {}).get("name", "")
        state = comp.get("status", {}).get("type", {}).get("state", "pre")  # pre / in / post

        game = {
            "league":     league.upper().replace("MENS-COLLEGE-BASKETBALL", "NCAAB"),
            "date":       date_str,
            "time":       time_str,
            "away":       away or "?",
            "home":       home or "?",
            "status":     status,
            "state":      state,
            "away_score": away_score,
            "home_score": home_score,
        }
        games.append(game)

    return games


def fetch_week(league_keys: list[str], days: int = 7) -> list[dict]:
    """Fetch games for all requested leagues over the next N days."""
    today = datetime.now(tz=ET).date()
    dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]

    all_games = []
    for key in league_keys:
        if key not in LEAGUES:
            print(f"Unknown league: {key}")
            continue
        sport, league = LEAGUES[key]
        print(f"Fetching {key.upper()}...")
        for d in dates:
            games = fetch_schedule(sport, league, d)
            all_games.extend(games)

    # Sort by date then time
    all_games.sort(key=lambda g: (g["date"], g["time"]))
    return all_games


# ──────────────────────────────────────────────
# OUTPUT
# ──────────────────────────────────────────────

def format_score(game: dict) -> str:
    if game["state"] == "post":
        return f"{game['away']} {game['away_score']} @ {game['home']} {game['home_score']}  ✅"
    elif game["state"] == "in":
        return f"{game['away']} {game['away_score']} @ {game['home']} {game['home_score']}  🔴 LIVE"
    else:
        return f"{game['away']} @ {game['home']}"


def print_schedule(games: list[dict]):
    if not games:
        print("No games found.")
        return

    current_date = None
    for g in games:
        # Format date header
        date_label = datetime.strptime(g["date"], "%Y%m%d").strftime("%A, %B %-d")
        if date_label != current_date:
            current_date = date_label
            print(f"\n{'═'*55}")
            print(f"  {date_label}")
            print(f"{'═'*55}")

        matchup = format_score(g)
        print(f"  [{g['league']:5s}]  {g['time']:12s}  {matchup}")


def save_csv(games: list[dict], path: str):
    import csv
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "league", "date", "time", "away", "home",
            "state", "away_score", "home_score"
        ])
        writer.writeheader()
        for g in games:
            writer.writerow({k: g[k] for k in writer.fieldnames})
    print(f"\n✅ Saved to {path}")


def save_json(games: list[dict], path: str):
    with open(path, "w") as f:
        json.dump(games, f, indent=2)
    print(f"\n✅ Saved to {path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch this week's sports schedule from ESPN.")
    parser.add_argument(
        "--leagues", nargs="+",
        default=["nba", "nhl", "mlb", "nfl", "ncaab"],
        choices=list(LEAGUES.keys()),
        help="Leagues to fetch (default: nba nhl mlb nfl ncaab)"
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days ahead to fetch (default: 7)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Save results to file. Use .csv or .json extension."
    )
    args = parser.parse_args()

    print(f"\n🏟️  Fetching schedule for: {', '.join(l.upper() for l in args.leagues)}")
    print(f"📅  Next {args.days} days starting today\n")

    games = fetch_week(args.leagues, args.days)

    print_schedule(games)
    print(f"\n📊  Total games found: {len(games)}")

    if args.output:
        if args.output.endswith(".json"):
            save_json(games, args.output)
        else:
            save_csv(games, args.output)


if __name__ == "__main__":
    main()