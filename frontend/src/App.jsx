import { useEffect, useState } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL ?? "/api";

export default function App() {
  const [tab, setTab] = useState("home");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // zamiast jednej listy:
  const [leagues, setLeagues] = useState([]); // ["Bundesliga", ...]
  const [teamsByLeague, setTeamsByLeague] = useState({}); // { league: [{value,label}, ...] }

  useEffect(() => {
    if (tab !== "teams") return;

    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setError("");
        setLeagues([]);
        setTeamsByLeague({});

        // 1) pobierz ligi
        const leaguesUrl = `${API}/leagues`;
        console.log("Pobieram ligi z:", leaguesUrl);

        const resLeagues = await fetch(leaguesUrl, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!resLeagues.ok) {
          const text = await resLeagues.text();
          console.error("HTTP", resLeagues.status, "Body:", text.slice(0, 300));
          throw new Error(`HTTP ${resLeagues.status} (leagues)`);
        }

        const leaguesData = await resLeagues.json();
        const leaguesArr = Array.isArray(leaguesData) ? leaguesData : [];
        setLeagues(leaguesArr);

        // 2) pobierz drużyny dla każdej ligi (równolegle)
        const pairs = await Promise.all(
          leaguesArr.map(async (lg) => {
            const url = `${API}/teams?league=${encodeURIComponent(lg)}&pretty=1`;
            console.log("Pobieram teams z:", url);

            const resTeams = await fetch(url, {
              signal: controller.signal,
              cache: "no-store",
            });

            if (!resTeams.ok) {
              const text = await resTeams.text();
              console.error("HTTP", resTeams.status, "Body:", text.slice(0, 300));
              throw new Error(`HTTP ${resTeams.status} (teams for ${lg})`);
            }

            const teams = await resTeams.json();
            return [lg, Array.isArray(teams) ? teams : []];
          })
        );

        setTeamsByLeague(Object.fromEntries(pairs));
      } catch (e) {
        if (e.name !== "AbortError") {
          setError(e.message || "Błąd pobierania danych");
        }
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [tab]);

  const leaguesSorted = (leagues || []).slice().sort((a, b) => a.localeCompare(b));

  return (
    <div className="app">
      <header className="app-header">
        <nav className="topnav">
          <div className="brand">Prediction Application</div>

          <div className="topnav-center">
            <button onClick={() => setTab("home")} className={tab === "home" ? "active" : ""}>
              Home
            </button>
            <button onClick={() => setTab("teams")} className={tab === "teams" ? "active" : ""}>
              Teams
            </button>
            <button onClick={() => setTab("about")} className={tab === "about" ? "active" : ""}>
              About
            </button>
          </div>

          <div className="topnav-right" />
        </nav>
      </header>

      <main className="app-main">
        {tab === "home" && (
          <section>
            <h2>Start</h2>
            <p>
              Jeśli widzisz tę stronę, to znaczy że <b>App.jsx</b> działa i nie renderujesz już template Vite.
            </p>
            <p>
              Backend API ustawiasz przez <code>VITE_API_URL</code> (np. w pliku <code>.env</code>).
            </p>
          </section>
        )}

        {tab === "teams" && (
          <section>
            <h2>Teams</h2>

            <p style={{ opacity: 0.8 }}>
              Pobieram ligi z: <code>{API}/leagues</code>
              <br />
              A drużyny z: <code>{API}/teams?league=...&pretty=1</code>
            </p>

            {loading && <p>Ładowanie…</p>}
            {error && <p style={{ color: "crimson" }}>Błąd: {error}</p>}

            {!loading && !error && (
              <>
                {leaguesSorted.length === 0 ? (
                  <p>(brak lig)</p>
                ) : (
                  <div className="teams-by-league">
                    {leaguesSorted.map((lg) => {
                      const teams = teamsByLeague[lg] || [];
                      const teamsSorted = teams
                        .slice()
                        .sort((a, b) => (a.label || "").localeCompare(b.label || ""));

                      return (
                        <section key={lg} className="league-section">
                          <h3 className="league-title">{lg}</h3>

                          {teamsSorted.length === 0 ? (
                            <p style={{ opacity: 0.7 }}>(brak drużyn)</p>
                          ) : (
                            <div className="teams-grid" role="table" aria-label={`Teams ${lg}`}>
                              {teamsSorted.map((t, i) => (
                                <div className="team-cell" role="row" key={t.value ?? `${lg}-${i}`}>
                                  {t.label ?? t.value}
                                </div>
                              ))}
                            </div>

                          )}
                        </section>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {tab === "about" && (
          <section>
            <h2>O aplikacji</h2>
            <p>Tu możesz wrzucić opis projektu, linki, itd.</p>
          </section>
        )}
      </main>
    </div>
  );
}
