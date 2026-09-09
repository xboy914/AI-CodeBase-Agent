export type Citation = {
  path: string;
  start_line: number;
  end_line: number;
};

export type AskResult = {
  answer: string;
  citations: Citation[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function checkHealth() {
  return request<{ status: string }>("/health");
}

export function indexRepository(path: string) {
  return request<{ files: number; chunks: number }>("/index", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}

export function askQuestion(question: string, limit = 8) {
  return request<AskResult>("/ask", {
    method: "POST",
    body: JSON.stringify({ question, limit }),
  });
}
