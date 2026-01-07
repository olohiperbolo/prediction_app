from __future__ import annotations
import os
from datetime import date
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from db import get_connection


ALLOWED_SORT = {
    "match_date_asc": "match_date ASC",
    "match_date_desc": "match_date DESC",
}

ALLOWED_RESULT = {"home_win", "away_win", "draw"}


TEAM_DISPLAY: dict[str, str] = {
    # ===== Bundesliga =====
    "Ein Frankfurt": "Eintracht Frankfurt",
    "M'gladbach": "Borussia Mönchengladbach",
    "Leverkusen": "Bayer Leverkusen",
    "Bayern Munich": "FC Bayern München",
    "RB Leipzig": "RB Leipzig",
    "St Pauli": "FC St. Pauli",
    "Union Berlin": "1. FC Union Berlin",
    "Werder Bremen": "SV Werder Bremen",
    "Wolfsburg": "VfL Wolfsburg",
    "Mainz": "1. FSV Mainz 05",
    "Augsburg": "FC Augsburg",
    "Bochum": "VfL Bochum",
    "Dortmund": "Borussia Dortmund",
    "Freiburg": "SC Freiburg",
    "Heidenheim": "1. FC Heidenheim",
    "Hoffenheim": "TSG Hoffenheim",
    "Holstein Kiel": "Holstein Kiel",
    "Stuttgart": "VfB Stuttgart",
    "FC Koln": "1. FC Köln",
    "Hamburg": "Hamburger SV",
    "Hertha": "Hertha BSC",
    "Schalke 04": "FC Schalke 04",


    # ===== Premier League / England =====
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Wolves": "Wolverhampton Wanderers",
    "Nott'm Forest": "Nottingham Forest",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Sheffield United": "Sheffield United",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Norwich": "Norwich City",
    "Ipswich": "Ipswich Town",
    "Bournemouth": "AFC Bournemouth",
    "Brighton": "Brighton & Hove Albion",
    "Crystal Palace": "Crystal Palace",
    "Aston Villa": "Aston Villa",
    "Nottm Forest": "Nottingham Forest",
    "Man Utd": "Manchester United",
    "Man United ": "Manchester United",
    "Arsenal": "Arsenal",
    "Brentford": "Brentford",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Liverpool": "Liverpool",
    "Luton": "Luton Town",
    "Southampton": "Southampton",
    "Sunderland": "Sunderland",

    # ===== La Liga / Spain =====
    "Ath Madrid": "Atlético Madrid",
    "Ath Bilbao": "Athletic Club",
    "Sociedad": "Real Sociedad",
    "Real Madrid": "Real Madrid",
    "Barcelona": "FC Barcelona",
    "Sevilla": "Sevilla FC",
    "Valencia": "Valencia CF",
    "Villarreal": "Villarreal CF",
    "Betis": "Real Betis",
    "Celta": "Celta Vigo",
    "Alaves": "Deportivo Alavés",
    "Vallecano": "Rayo Vallecano",
    "Espanol": "RCD Espanyol",
    "La Coruna": "Deportivo La Coruña",
    "Las Palmas": "UD Las Palmas",
    "Almeria": "UD Almería",
    "Cadiz": "Cádiz CF",
    "Elche": "Elche CF",
    "Getafe": "Getafe CF",
    "Girona": "Girona FC",
    "Granada": "Granada CF",
    "Leganes": "CD Leganés",
    "Levante": "Levante UD",
    "Mallorca": "RCD Mallorca",
    "Osasuna": "CA Osasuna",
    "Oviedo": "Real Oviedo",
    "Valladolid": "Real Valladolid",

    # ===== Serie A / Italy =====
    "Inter": "Inter Milan",
    "Milan": "AC Milan",
    "Roma": "AS Roma",
    "Lazio": "SS Lazio",
    "Juventus": "Juventus",
    "Napoli": "SSC Napoli",
    "Atalanta": "Atalanta",
    "Fiorentina": "Fiorentina",
    "Torino": "Torino",
    "Udinese": "Udinese",
    "Verona": "Hellas Verona",
    "Sassuolo": "Sassuolo",
    "Cagliari": "Cagliari",
    "Genoa": "Genoa",
    "Bologna": "Bologna",
    "Empoli": "Empoli",
    "Lecce": "Lecce",
    "Monza": "Monza",
    "Salernitana": "Salernitana",
    "Frosinone": "Frosinone",
    "Spezia": "Spezia",
    "Cremonese": "Cremonese",
    "Venezia": "Venezia",
    "Parma": "Parma",
    "Como": "Como",
    "Pisa": "Pisa",

    # ===== Ligue 1 / France =====
    "Paris SG": "Paris Saint-Germain",
    "PSG": "Paris Saint-Germain",
    "Marseille": "Olympique de Marseille",
    "Lyon": "Olympique Lyonnais",
    "Monaco": "AS Monaco",
    "Lille": "LOSC Lille",
    "Nice": "OGC Nice",
    "Rennes": "Stade Rennais",
    "Nantes": "FC Nantes",
    "Strasbourg": "RC Strasbourg",
    "Reims": "Stade de Reims",
    "Montpellier": "Montpellier HSC",
    "Toulouse": "Toulouse FC",
    "Lorient": "FC Lorient",
    "Brest": "Stade Brestois 29",
    "Lens": "RC Lens",
    "Metz": "FC Metz",
    "Le Havre": "Le Havre AC",
    "Clermont": "Clermont Foot",
    "Auxerre": "AJ Auxerre",
    "Angers": "Angers SCO",
    "St Etienne": "AS Saint-Étienne",
    "Saint Etienne": "AS Saint-Étienne",
    "Paris FC": "Paris FC",
}

def display_team(name: str) -> str:
    if name is None:
        return name
    n = str(name).strip()
    return TEAM_DISPLAY.get(n, n)

def check_team_alias_coverage() -> None:
    """
    Wypisuje w konsoli drużyny, które są w DB, a nie mają wpisu w TEAM_DISPLAY.
    Dzięki temu masz pewność, że aliasy obejmują wszystkie sezony/ligi jakie masz w bazie.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT team FROM (
                SELECT home_team AS team FROM football_matches
                UNION
                SELECT away_team AS team FROM football_matches
            )
            ORDER BY team ASC;
        """)
        teams = [r[0] for r in cur.fetchall()]
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

    missing = [t for t in teams if t not in TEAM_DISPLAY]
    if missing:
        print("\n[TEAM_DISPLAY] Brakuje aliasów dla:", missing, "\n")
    else:
        print("\n[TEAM_DISPLAY] OK: masz aliasy dla wszystkich drużyn w DB.\n")


def parse_int(name: str, raw: str | None, default: int, min_v: int | None = None, max_v: int | None = None) -> int:
    if raw is None or raw == "":
        x = default
    else:
        try:
            x = int(raw)
        except ValueError:
            raise ValueError(f"{name} must be an integer")

    if min_v is not None and x < min_v:
        raise ValueError(f"{name} must be >= {min_v}")
    if max_v is not None and x > max_v:
        raise ValueError(f"{name} must be <= {max_v}")
    return x


def parse_date(name: str, raw: str | None) -> str | None:
    if raw is None or raw == "":
        return None
    try:
        date.fromisoformat(raw)  # YYYY-MM-DD
        return raw
    except ValueError:
        raise ValueError(f"{name} must be YYYY-MM-DD")


def first_col(row, key: str | None = None):
    if row is None:
        return None
    if key is not None:
        try:
            return row[key]
        except Exception:
            pass
        try:
            return dict(row)[key]
        except Exception:
            pass
    try:
        return row[0]
    except Exception:
        return list(dict(row).values())[0]


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})


    # --- Error handling: ALWAYS JSON ---------------------------------------

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        # e.code: 400/404/405...
        return jsonify({"error": e.name, "message": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e: Exception):
        # Nie wyświetlamy stacktrace w odpowiedzi API
        # (stacktrace i tak masz w konsoli w trybie debug)
        return jsonify({"error": "Internal Server Error", "message": "Unexpected error"}), 500

    # --- Routes ------------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/debug/count")
    def debug_count():
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM football_matches;")
            cnt = cur.fetchone()[0]
            return jsonify({"count": cnt})
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/leagues")
    def get_leagues():
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT league FROM football_matches ORDER BY league ASC;")
            rows = cur.fetchall()
            leagues = [first_col(r, "league") for r in rows]
            return jsonify(leagues)
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/seasons")
    def get_seasons():
        league_name = request.args.get("league")
        if not league_name:
            return jsonify({"error": "Bad Request", "message": "league is required"}), 400

        conn = get_connection()
        cur = conn.cursor()
        try:
            # SQLite placeholder = ?
            cur.execute(
                "SELECT DISTINCT season FROM football_matches WHERE league = ? ORDER BY season ASC;",
                (league_name,),
            )
            rows = cur.fetchall()
            seasons = [first_col(r, "season") for r in rows]
            return jsonify(seasons)
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/teams")
    def get_teams():
        league = request.args.get("league")
        season = request.args.get("season")
        pretty = request.args.get("pretty", "0") in ("1", "true", "True", "yes")

        where = ["1=1"]
        params = []

        if league:
            where.append("league = ?")
            params.append(league)
        if season:
            where.append("season = ?")
            params.append(season)

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT DISTINCT team FROM (
                SELECT home_team AS team FROM football_matches WHERE {where_sql}
                UNION
                SELECT away_team AS team FROM football_matches WHERE {where_sql}
            )
            ORDER BY team ASC;
        """

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(params + params))  # where_sql jest 2x
            teams = [first_col(r, "team") for r in cur.fetchall()]
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

        if not pretty:
            return jsonify(teams)

        items = [{"value": t, "label": display_team(t)} for t in teams]
        # dla UI lepiej sortować po label
        items.sort(key=lambda x: x["label"])
        return jsonify(items)


    @app.get("/stats/team")
    def team_stats():
        league = request.args.get("league")
        season = request.args.get("season")
        team = request.args.get("team")

        if not league or not season or not team:
            return jsonify({
                "error": "Bad Request",
                "message": "league, season and team are required"
            }), 400

        try:
            last_n = parse_int("last", request.args.get("last"), default=5, min_v=1, max_v=20)
        except ValueError as e:
            return jsonify({"error": "Bad Request", "message": str(e)}), 400

        conn = get_connection()
        cur = conn.cursor()
        try:
            # 1) ALL matches for team in league+season
            cur.execute(
                """
                SELECT
                    id, match_date, home_team, away_team, home_goals, away_goals
                FROM football_matches
                WHERE league = ? AND season = ? AND (home_team = ? OR away_team = ?)
                ORDER BY match_date ASC;
                """,
                (league, season, team, team),
            )
            rows = [dict(r) for r in cur.fetchall()]

            if not rows:
                return jsonify({
                    "error": "Not Found",
                    "message": "No matches found for given league/season/team"
                }), 404

            # Helpers
            def outcome_for_team(r: dict) -> str:
                hg, ag = r["home_goals"], r["away_goals"]
                # jeśli braki w golach (None) - traktuj jako unknown
                if hg is None or ag is None:
                    return "U"
                if r["home_team"] == team:
                    if hg > ag: return "W"
                    if hg < ag: return "L"
                    return "D"
                else:
                    if ag > hg: return "W"
                    if ag < hg: return "L"
                    return "D"

            def goals_for_against(r: dict) -> tuple[int | None, int | None]:
                hg, ag = r["home_goals"], r["away_goals"]
                if hg is None or ag is None:
                    return None, None
                if r["home_team"] == team:
                    return hg, ag
                return ag, hg

            # 2) Aggregate stats
            played = 0
            wins = draws = losses = 0
            gf = ga = 0
            known_score_games = 0

            home_played = away_played = 0
            home_w = home_d = home_l = 0
            away_w = away_d = away_l = 0

            for r in rows:
                out = outcome_for_team(r)
                if out == "U":
                    continue  # pomijamy mecze bez wyniku

                played += 1
                gfor, gagainst = goals_for_against(r)
                gf += gfor
                ga += gagainst
                known_score_games += 1

                is_home = (r["home_team"] == team)
                if is_home:
                    home_played += 1
                else:
                    away_played += 1

                if out == "W":
                    wins += 1
                    if is_home: home_w += 1
                    else: away_w += 1
                elif out == "D":
                    draws += 1
                    if is_home: home_d += 1
                    else: away_d += 1
                elif out == "L":
                    losses += 1
                    if is_home: home_l += 1
                    else: away_l += 1

            # 3) Last N matches (with results)
            last_matches_src = [r for r in rows if r["home_goals"] is not None and r["away_goals"] is not None]
            last_matches = last_matches_src[-last_n:] if last_matches_src else []
            form = "".join(outcome_for_team(r) for r in last_matches)

            def fmt_match(r: dict) -> dict:
                return {
                    "id": r["id"],
                    "match_date": r["match_date"],
                    "home_team": r["home_team"],
                    "away_team": r["away_team"],
                    "home_goals": r["home_goals"],
                    "away_goals": r["away_goals"],
                    "team_result": outcome_for_team(r),
                    "is_home": (r["home_team"] == team),
                }

            return jsonify({
                "league": league,
                "season": season,
                "team": team,
                "played": played,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goals_for": gf,
                "goals_against": ga,
                "goals_for_per_game": round(gf / played, 3) if played else None,
                "goals_against_per_game": round(ga / played, 3) if played else None,
                "home": {"played": home_played, "wins": home_w, "draws": home_d, "losses": home_l},
                "away": {"played": away_played, "wins": away_w, "draws": away_d, "losses": away_l},
                "form_last_n": {"n": last_n, "sequence": form},
                "last_matches": [fmt_match(r) for r in last_matches],
                "note": "Stats ignore matches with missing scores (home_goals/away_goals is NULL).",
            })
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/stats/h2h")
    def h2h_stats():
        league = request.args.get("league")
        season = request.args.get("season")
        home_team = request.args.get("home_team")
        away_team = request.args.get("away_team")

        if not league or not home_team or not away_team:
            return jsonify({
                "error": "Bad Request",
                "message": "league, home_team and away_team are required"
            }), 400

        try:
            last_n = parse_int("last", request.args.get("last"), default=10, min_v=1, max_v=50)
        except ValueError as e:
            return jsonify({"error": "Bad Request", "message": str(e)}), 400

        where = ["league = ?"]
        params = [league]

        if season:
            where.append("season = ?")
            params.append(season)

        # mecze dokładnie tych dwóch drużyn (w obie strony)
        where.append("""
            (
                (home_team = ? AND away_team = ?)
                OR
                (home_team = ? AND away_team = ?)
            )
        """)
        params.extend([home_team, away_team, away_team, home_team])

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT id, season, match_date, home_team, away_team, home_goals, away_goals
            FROM football_matches
            WHERE {where_sql}
            ORDER BY match_date DESC
            LIMIT ?;
        """

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(params + [last_n]))
            rows = [dict(r) for r in cur.fetchall()]

            if not rows:
                return jsonify({
                    "error": "Not Found",
                    "message": "No head-to-head matches found for given filters"
                }), 404

            # bilans z perspektywy home_team (tego z query param)
            w = d = l = 0
            gf = ga = 0
            counted = 0

            def result_from_perspective(r: dict) -> str:
                hg, ag = r["home_goals"], r["away_goals"]
                if hg is None or ag is None:
                    return "U"
                # kto jest "nasz" w tym meczu?
                if r["home_team"] == home_team:
                    if hg > ag: return "W"
                    if hg < ag: return "L"
                    return "D"
                else:
                    # home_team grał jako away
                    if ag > hg: return "W"
                    if ag < hg: return "L"
                    return "D"

            def goals_from_perspective(r: dict) -> tuple[int | None, int | None]:
                hg, ag = r["home_goals"], r["away_goals"]
                if hg is None or ag is None:
                    return None, None
                if r["home_team"] == home_team:
                    return hg, ag
                return ag, hg

            formatted = []
            for r in rows:
                res = result_from_perspective(r)
                gfor, gagainst = goals_from_perspective(r)

                if res != "U":
                    counted += 1
                    gf += gfor
                    ga += gagainst
                    if res == "W": w += 1
                    elif res == "D": d += 1
                    elif res == "L": l += 1

                formatted.append({
                    "id": r["id"],
                    "league": league,
                    "season": r.get("season"),
                    "match_date": r["match_date"],
                    "home_team": r["home_team"],
                    "away_team": r["away_team"],
                    "home_goals": r["home_goals"],
                    "away_goals": r["away_goals"],
                    "result_for_home_team_param": res,  # W/D/L/U z perspektywy home_team paramu
                })

            return jsonify({
                "league": league,
                "season": season,
                "home_team": home_team,
                "away_team": away_team,
                "last": last_n,
                "counted_games_with_score": counted,
                "record_for_home_team": {"wins": w, "draws": d, "losses": l},
                "goals_for_home_team": gf,
                "goals_against_home_team": ga,
                "matches": formatted,
            })
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/stats/table")
    def league_table():
        league = request.args.get("league")
        season = request.args.get("season")

        if not league or not season:
            return jsonify({
                "error": "Bad Request",
                "message": "league and season are required"
            }), 400

        conn = get_connection()
        cur = conn.cursor()
        try:
            # Bierzemy wszystkie mecze w lidze+sezonie z kompletnym wynikiem
            cur.execute(
                """
                SELECT home_team, away_team, home_goals, away_goals
                FROM football_matches
                WHERE league = ? AND season = ?
                  AND home_goals IS NOT NULL AND away_goals IS NOT NULL;
                """,
                (league, season),
            )
            rows = cur.fetchall()

            # tabela w pythonie (łatwo i czytelnie na MVP)
            table = {}  # team -> stats

            def ensure_team(t: str):
                if t not in table:
                    table[t] = {
                        "team": t,
                        "played": 0,
                        "wins": 0,
                        "draws": 0,
                        "losses": 0,
                        "goals_for": 0,
                        "goals_against": 0,
                        "goal_diff": 0,
                        "points": 0,
                    }

            for r in rows:
                h = r["home_team"]
                a = r["away_team"]
                hg = r["home_goals"]
                ag = r["away_goals"]

                ensure_team(h)
                ensure_team(a)

                # played
                table[h]["played"] += 1
                table[a]["played"] += 1

                # goals
                table[h]["goals_for"] += hg
                table[h]["goals_against"] += ag
                table[a]["goals_for"] += ag
                table[a]["goals_against"] += hg

                # results + points
                if hg > ag:
                    table[h]["wins"] += 1
                    table[a]["losses"] += 1
                    table[h]["points"] += 3
                elif hg < ag:
                    table[a]["wins"] += 1
                    table[h]["losses"] += 1
                    table[a]["points"] += 3
                else:
                    table[h]["draws"] += 1
                    table[a]["draws"] += 1
                    table[h]["points"] += 1
                    table[a]["points"] += 1

            items = list(table.values())
            for it in items:
                it["goal_diff"] = it["goals_for"] - it["goals_against"]

            # sort: points desc, GD desc, GF desc, name asc
            items.sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team"]))

            # add rank
            for i, it in enumerate(items, start=1):
                it["rank"] = i

            return jsonify({
                "league": league,
                "season": season,
                "teams": items,
                "note": "Table computed from matches with non-null scores only. Tiebreakers: points, goal_diff, goals_for, team name.",
            })
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    # GET /matches?league=&season=&date_from=&date_to=&team=&result=&limit=&offset=&sort=
    @app.get("/matches")
    def get_matches():
        league = request.args.get("league")
        season = request.args.get("season")
        team = request.args.get("team")
        result = request.args.get("result")
        sort = request.args.get("sort", "match_date_asc")

        try:
            date_from = parse_date("date_from", request.args.get("date_from"))
            date_to = parse_date("date_to", request.args.get("date_to"))
            limit = parse_int("limit", request.args.get("limit"), default=20, min_v=1, max_v=200)
            offset = parse_int("offset", request.args.get("offset"), default=0, min_v=0)
        except ValueError as e:
            return jsonify({"error": "Bad Request", "message": str(e)}), 400

        if result and result not in ALLOWED_RESULT:
            return jsonify({"error": "Bad Request", "message": f"result must be one of {sorted(ALLOWED_RESULT)}"}), 400
        if sort not in ALLOWED_SORT:
            return jsonify({"error": "Bad Request", "message": f"sort must be one of {sorted(ALLOWED_SORT)}"}), 400

        where = ["1=1"]
        params: list[object] = []

        if league:
            where.append("league = ?")
            params.append(league)

        if season:
            where.append("season = ?")
            params.append(season)

        if date_from:
            where.append("match_date >= ?")
            params.append(date_from)

        if date_to:
            where.append("match_date <= ?")
            params.append(date_to)

        if team:
            where.append("(home_team = ? OR away_team = ?)")
            params.extend([team, team])

        if result == "home_win":
            where.append("home_goals > away_goals")
        elif result == "away_win":
            where.append("away_goals > home_goals")
        elif result == "draw":
            where.append("home_goals = away_goals")

        where_sql = " AND ".join(where)
        order_sql = ALLOWED_SORT[sort]

        data_sql = f"""
            SELECT
                id, league, season,
                home_team, away_team,
                match_date, home_goals, away_goals
            FROM football_matches
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?;
        """
        count_sql = f"SELECT COUNT(*) FROM football_matches WHERE {where_sql};"

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(count_sql, tuple(params))
            total = cur.fetchone()[0]

            cur.execute(data_sql, tuple(params + [limit, offset]))
            rows = cur.fetchall()
            items = [dict(r) for r in rows]

            return jsonify({
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": {
                    "league": league,
                    "season": season,
                    "date_from": date_from,
                    "date_to": date_to,
                    "team": team,
                    "result": result,
                    "sort": sort,
                },
            })
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()

    @app.get("/matches/<int:match_id>")
    def get_match_by_id(match_id: int):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM football_matches WHERE id = ?;", (match_id,))
            row = cur.fetchone()
            if row:
                return jsonify(dict(row))
            return jsonify({"error": "Not Found", "message": "Match not found"}), 404
        finally:
            try:
                cur.close()
            except Exception:
                pass
            conn.close()


    check_team_alias_coverage()

    return app


if __name__ == "__main__":
    app = create_app()

    # Sterowanie debug przez ENV
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))

    app.run(host=host, port=port, debug=debug)
