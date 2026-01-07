import { useEffect, useState } from "react";
import "./App.css";


const API = import.meta.env.VITE_API_URL ?? "/api";


export default function App() {
  const [tab, setTab] = useState("home");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    if (tab !== "teams") return;

    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setError("");

        const url = `${API}/teams?pretty=1`;
        console.log("Pobieram z:", url);

        const res = await fetch(url, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!res.ok) {
          const text = await res.text();
          console.error("HTTP", res.status, "Body:", text.slice(0, 300));
          throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        setTeams(Array.isArray(data) ? data : []);
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

  return (
  <div className="app">
    <header className="app-header">
      <nav className="topnav">
        <div className="brand">Moja aplikacja</div>

      <div className="topnav-center">
        <button
          onClick={() => setTab("home")}
          className={tab === "home" ? "active" : ""}
        >
          Home
        </button>

        <button onClick={() => setTab("teams")} disabled={tab === "teams"}>
          Teams
        </button>
        <button onClick={() => setTab("about")} disabled={tab === "about"}>
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
            Pobieram z: <code>{API}/teams</code>
          </p>

          {loading && <p>Ładowanie…</p>}
          {error && <p style={{ color: "crimson" }}>Błąd: {error}</p>}

          {!loading && !error && (
            <ul>
              {teams.length === 0 ? (
                <li>(brak danych)</li>
              ) : (
                teams.map((t, i) => <li key={t.value ?? i}>{t.label ?? t.value}</li>)
              )}
            </ul>
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
