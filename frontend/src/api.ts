const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/+$/, "") || "";

export function normalizeImageUrl(raw: string): string {
  if (!raw) return "";
  let url = raw.trim();

  // Если бэк вернул полный localhost-URL — удаляем корень
  if (
    url.startsWith("http://localhost:8000") ||
    url.startsWith("http://127.0.0.1:8000")
  ) {
    url = url
      .replace("http://localhost:8000", "")
      .replace("http://127.0.0.1:8000", "");
  }

  // Если это уже полный http/https-URL — оставляем как есть
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }

  // Относительный путь вида "static/..." или "/static/..."
  if (!url.startsWith("/")) {
    url = "/" + url;
  }

  return `${API_URL}${url}`;
}

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