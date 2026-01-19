import { useEffect, useMemo, useState } from "react";

export default function HomePredict({ leagues, teamsByLeague, API }) {
  const [league, setLeague] = useState(leagues?.[0] ?? "");
  const [season, setSeason] = useState("");
  const [seasons, setSeasons] = useState([]);

  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [pred, setPred] = useState(null);

  // cutoff + okno historii
  const todayISO = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [matchDate, setMatchDate] = useState(todayISO);

  const [historyMode, setHistoryMode] = useState("last_n"); // "last_n" | "last_days"
  const [historyValue, setHistoryValue] = useState(10);

  // Gdy ligi dojdą async, ustaw domyślną ligę
  useEffect(() => {
    if (!league && leagues?.length) setLeague(leagues[0]);
  }, [leagues, league]);

  // Pobieranie sezonów dla wybranej ligi
  useEffect(() => {
    if (!league) return;

    const controller = new AbortController();

    (async () => {
      try {
        setSeasons([]);
        setSeason("");
        setHomeTeam("");
        setAwayTeam("");
        setPred(null);
        setErr("");

        const res = await fetch(`${API}/seasons?league=${encodeURIComponent(league)}`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (!res.ok) return;

        const data = await res.json();
        const arr = Array.isArray(data) ? data : [];
        setSeasons(arr);
        if (arr.length) setSeason(arr[arr.length - 1]);
      } catch (e) {
        if (e.name !== "AbortError") {
          // ignorujemy — sezony są dodatkiem
        }
      }
    })();

    return () => controller.abort();
  }, [league, API]);

  const teams = useMemo(() => {
    const list = teamsByLeague?.[league] || [];
    return list.slice().sort((a, b) => (a.label || "").localeCompare(b.label || ""));
  }, [teamsByLeague, league]);

  async function onPredict() {
    try {
      setLoading(true);
      setErr("");
      setPred(null);

      if (!league) throw new Error("Wybierz ligę");
      if (!homeTeam || !awayTeam) throw new Error("Wybierz oba zespoły");
      if (homeTeam === awayTeam) throw new Error("Zespoły muszą być różne");
      if (!matchDate) throw new Error("Wybierz datę meczu");

      const res = await fetch(`${API}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          league,
          season: season || undefined,
          home_team: homeTeam,
          away_team: awayTeam,

          match_date: matchDate, // "YYYY-MM-DD"
          history_mode: historyMode, // "last_n" | "last_days"
          history_value: Number(historyValue), // np. 10 albo 180
        }),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `HTTP ${res.status}`);
      }

      const json = await res.json();
      setPred(json);
    } catch (e) {
      setErr(e.message || "Błąd predykcji");
    } finally {
      setLoading(false);
    }
  }

  const pct = (x) => `${(x * 100).toFixed(1)}%`;

  return (
    <section className="card">
      <h2>Predict match</h2>

      <div className="formGrid">
        <label>
          Liga
          <select value={league} onChange={(e) => setLeague(e.target.value)}>
            {(leagues || []).map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>

        <label>
          Sezon (opcjonalnie)
          <select value={season} onChange={(e) => setSeason(e.target.value)}>
            <option value="">— wszystkie —</option>
            {seasons.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>

        <label>
          Home
          <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}>
            <option value="">— wybierz —</option>
            {teams.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label ?? t.value}
              </option>
            ))}
          </select>
        </label>

        <label>
          Away
          <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}>
            <option value="">— wybierz —</option>
            {teams.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label ?? t.value}
              </option>
            ))}
          </select>
        </label>

        <label>
          Data meczu (cutoff)
          <input type="date" value={matchDate} onChange={(e) => setMatchDate(e.target.value)} />
        </label>

        <label>
          Historia
          <select value={historyMode} onChange={(e) => setHistoryMode(e.target.value)}>
            <option value="last_n">Ostatnie N meczów</option>
            <option value="last_days">Ostatnie X dni</option>
          </select>
        </label>

        <label>
          Wartość
          <input
            type="number"
            min="1"
            value={historyValue}
            onChange={(e) => setHistoryValue(e.target.value)}
          />
        </label>

        <button className="btn" onClick={onPredict} disabled={loading}>
          {loading ? "Liczenie..." : "Predict"}
        </button>
      </div>

      {err && <p className="error">{err}</p>}

      {pred && (
        <div className="resultBox">
          <div className="resultRow">
            <div>
              <strong>Cutoff:</strong> {pred.cutoff_match_date ?? "—"}
            </div>
            <div>
              <strong>Historia:</strong> {pred.history?.mode ?? "—"} = {pred.history?.value ?? "—"}
            </div>
            <div>
              <strong>Mecze użyte:</strong> {pred.training_matches_used ?? "—"}
            </div>

            <div>
              <strong>λ Home:</strong> {pred.lambda_home?.toFixed?.(2) ?? pred.lambda_home}
            </div>
            <div>
              <strong>λ Away:</strong> {pred.lambda_away?.toFixed?.(2) ?? pred.lambda_away}
            </div>
            <div>
              <strong>Najbardziej prawdopodobny wynik:</strong>{" "}
              {pred.most_likely_score?.home_goals}:{pred.most_likely_score?.away_goals} (
              {pct(pred.most_likely_score?.p ?? 0)})
            </div>
          </div>

          <table className="simpleTable">
            <thead>
              <tr>
                <th>1</th>
                <th>X</th>
                <th>2</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{pct(pred.p_home ?? 0)}</td>
                <td>{pct(pred.p_draw ?? 0)}</td>
                <td>{pct(pred.p_away ?? 0)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
