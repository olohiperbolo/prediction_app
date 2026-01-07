const API = import.meta.env.VITE_API_URL;

function normalizeTeams(payload) {
  // Obsłuż różne możliwe formaty odpowiedzi
  if (Array.isArray(payload)) return payload;

  if (payload && Array.isArray(payload.teams)) return payload.teams;

  // np. obiekt { "Arsenal": {...}, "Chelsea": {...} } albo { "teams": {..} }
  const maybeObj = payload?.teams && typeof payload.teams === "object" ? payload.teams : payload;
  if (maybeObj && typeof maybeObj === "object") return Object.values(maybeObj);

  return [];
}

export async function getTeams() {
  const res = await fetch(`${API}/teams`);
  if (!res.ok) throw new Error(`GET /teams -> HTTP ${res.status}`);
  const data = await res.json();
  return normalizeTeams(data);
}
