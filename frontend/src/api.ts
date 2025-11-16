const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function postJSON(path: string, body: any) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = "Ошибка запроса";
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json();
}

export async function getJSON(path: string) {
  const res = await fetch(`${API_URL}${path}`);

  if (!res.ok) {
    let detail = "Ошибка запроса";
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json();
}