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
    CORS(app)

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

    return app


if __name__ == "__main__":
    app = create_app()

    # Sterowanie debug przez ENV (nie hardcode)
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))

    app.run(host=host, port=port, debug=debug)
