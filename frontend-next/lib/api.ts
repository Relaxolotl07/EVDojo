// Default to Next.js rewrite proxy at /api; can be overridden with NEXT_PUBLIC_API_BASE
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

async function j<T>(resPromise: Promise<Response>): Promise<T> {
  const res = await resPromise;
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  get: <T>(p: string) => j<T>(fetch(`${API_BASE}${p}`, { cache: 'no-store' })),
  post: <T>(p: string, body: any, headers: Record<string,string> = {}) => j<T>(fetch(`${API_BASE}${p}`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) })),
  postForm: <T>(p: string, form: FormData) => j<T>(fetch(`${API_BASE}${p}`, { method: 'POST', body: form })),
};

export type Topic = "internal-request"|"customer-support"|"networking"|"ask-out"|string;
export type Pair = { pair_id: string; item_id: string; a: { variant_id: string; subject: string; body: string }; b: { variant_id: string; subject: string; body: string }; context: { goal: Topic } };
