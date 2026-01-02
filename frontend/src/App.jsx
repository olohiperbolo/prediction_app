import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:3000";

export default function App() {
  const [tab, setTab] = useState("home");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    // ładujemy dane tylko gdy jesteśmy w zakładce "teams"
    if (tab !== "teams") return;

    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setError("");

        const res = await fetch(`${API}/teams`, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

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
    <div style={{ fontFamily: "system-ui", padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h1 style={{ margin: 0 }}>Moja aplikacja</h1>

        <nav style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setTab("home")} disabled={tab === "home"}>
            Home
          </button>
          <button onClick={() => setTab("teams")} disabled={tab === "teams"}>
            Teams
          </button>
          <button onClick={() => setTab("about")} disabled={tab === "about"}>
            About
          </button>
        </nav>
      </header>

      <hr style={{ margin: "16px 0" }} />

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
                teams.map((t, i) => <li key={t.id ?? i}>{t.name ?? JSON.stringify(t)}</li>)
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
    </div>
  );
}
