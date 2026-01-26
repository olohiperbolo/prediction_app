import { useEffect, useMemo, useState } from "react";
import "./App.css";

import HomePredict from "./HomePredict"; // <- upewnij się, że masz ten plik/eksport

const API = import.meta.env.VITE_API_URL ?? "/api";

export default function App() {
  const [tab, setTab] = useState("home");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [leagues, setLeagues] = useState([]);            // ["Bundesliga", ...]
  const [teamsByLeague, setTeamsByLeague] = useState({}); // { league: [{value,label}, ...] }

  // Ładujemy dane globalnie (dla Home i Teams)
  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setError("");

        // 1) ligi
        const resLeagues = await fetch(`${API}/leagues`, {
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

        // 2) teams per liga
        const pairs = await Promise.all(
          leaguesArr.map(async (lg) => {
            const url = `${API}/teams?league=${encodeURIComponent(lg)}&pretty=1`;
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
  }, []);

  const leaguesSorted = useMemo(
    () => (leagues || []).slice().sort((a, b) => a.localeCompare(b)),
    [leagues]
  );

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
        {/* statusy wspólne */}
        {loading && <p>Ładowanie…</p>}
        {error && <p style={{ color: "crimson" }}>Błąd: {error}</p>}

        {tab === "home" && !loading && !error && (
          <>
            <HomePredict leagues={leaguesSorted} teamsByLeague={teamsByLeague} API={API} />
          </>
        )}

        {tab === "teams" && !loading && !error && (
          <section>
            <h2>Teams</h2>

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
          </section>
        )}

        {tab === "about" && (
          <section>
            <h2>O aplikacji</h2>
            <p>Ta aplikacja służy do przewidywania wyniku meczu piłkarskiego na podstawie danych historycznych. Wybierz ligę, sezon oraz drużyny gospodarzy i gości, a następnie ustaw datę „cutoff”, aby model brał pod uwagę tylko mecze rozegrane przed tym dniem. Predykcja opiera się na analizie formy z ostatnich 5 spotkań i zwraca najbardziej prawdopodobny rezultat..</p>
          </section>
        )}
      </main>
    </div>
  );
}
