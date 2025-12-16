from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_connection

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/matches/football")
    def get_football_matches():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, league, home_team, away_team, match_date
            FROM football_matches
            ORDER BY match_date ASC
            LIMIT 20;
        """)
        rows = cur.fetchall()
        conn.close()

        matches = [dict(row) for row in rows]
        return jsonify(matches)

    @app.route("/debug/count")
    def debug_count():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM football_matches;")
        cnt = cur.fetchone()[0]
        conn.close()
        return jsonify({"count": cnt})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
