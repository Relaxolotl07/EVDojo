// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

// assumes j: (r: Response) => Promise<T>
const j = async <T>(r: Response): Promise<T> => {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
};

export const api = {
  get: async <T>(p: string) =>
    j<T>(await fetch(`${API_BASE}${p}`, { cache: 'no-store' })),

  post: async <T>(p: string, body: any, headers: Record<string, string> = {}) =>
    j<T>(await fetch(`${API_BASE}${p}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(body),
    })),

  postForm: async <T>(p: string, form: FormData) =>
    j<T>(await fetch(`${API_BASE}${p}`, {
      method: 'POST',
      body: form,
    })),
};
