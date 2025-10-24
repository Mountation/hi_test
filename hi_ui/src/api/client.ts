// Vite env: set VITE_API_BASE to an absolute backend URL (e.g. http://127.0.0.1:8000) to bypass proxy.
// If empty, requests use relative paths and rely on the dev-server proxy (vite.config.ts).
const BASE = (import.meta.env && import.meta.env.VITE_API_BASE) ? String(import.meta.env.VITE_API_BASE) : '';

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const full = (BASE || '') + url;
  const res = await fetch(full, { ...options });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) {
    // No content
    return undefined as unknown as T;
  }
  return res.json() as Promise<T>;
}
export const api = {
  getEvalSets: () => request<import('../types').EvalSet[]>('/api/v1/evalsets/'),
  getEvalSet: (id: number) => request<import('../types').EvalSet>(`/api/v1/evalsets/${id}`),
  createEvalSet: (name: string) => request<import('../types').EvalSet>('/api/v1/evalsets/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }),
  deleteEvalSet: (id: number) => request<void>(`/api/v1/evalsets/${id}`, { method: 'DELETE' }),
  patchEvalSet: (id: number, payload: { name?: string }) => request<import('../types').EvalSet>(`/api/v1/evalsets/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  uploadExcel: async (file: File, name: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('name', name);
    return request('/api/v1/evalsets/upload', { method: 'POST', body: form });
  },
  // Query job status for async background tasks
  getJobStatus: (jobId: string) => request<{ job_id: string; status: string; processed?: number; total?: number; errors?: string[] }>(`/api/v1/jobs/${jobId}`),
  listEvalData: (setId: number, page: number = 1, pageSize: number = 10, q?: string, global_search?: boolean) => {
    const params = new URLSearchParams();
    params.set('page', String(page));
    params.set('page_size', String(pageSize));
    if (q) params.set('q', q);
    if (global_search) params.set('global_search', 'true');
    return request<{ items: import('../types').EvalData[]; total: number }>(`/api/v1/evalsets/${setId}/data?${params.toString()}`);
  },
  createEvalData: (setId: number, payload: { content: string; expected?: string; intent?: string }) => request(`/api/v1/evalsets/${setId}/data`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_set_id: setId, ...payload }) }),
  deleteEvalData: (setId: number, dataId: number) => request<void>(`/api/v1/evalsets/${setId}/data/${dataId}`, { method: 'DELETE' }),
  patchEvalData: (setId: number, dataId: number, payload: { content?: string; expected?: string; intent?: string }) => request<import('../types').EvalData>(`/api/v1/evalsets/${setId}/data/${dataId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  listResultsBySet: (setId: number) => request<import('../types').EvalResult[]>(`/api/v1/evalresults/byset/${setId}`),
  listResultsByData: (evalSetId: number, corpusId: number) => request<import('../types').EvalResult[]>(`/api/v1/evalresults/bydata/${evalSetId}/${corpusId}`),
  executeSingle: (eval_data_id: number) => request<import('../types').EvalResult>('/api/v1/evalresults/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_data_id }) }),
  executeBySet: (eval_set_id: number) => request<import('../types').BatchExecResponse>(`/api/v1/evalresults/execute/byset/${eval_set_id}`, { method: 'POST' }),
  executeBySetAsync: (eval_set_id: number) => request<{ job_id: string }>(`/api/v1/evalresults/execute/byset_async/${eval_set_id}`, { method: 'POST' }),
  executeBySets: (eval_set_ids: number[], global_concurrency?: number) => request<import('../types').MultiSetExecResponse>('/api/v1/evalresults/execute/bysets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_set_ids, global_concurrency }) }),
  getConfig: () => request<import('../types').ConfigInfo>('/api/v1/config/test'),
  updateConfig: (payload: Partial<{ url: string; api_key: string; hotline: string; userphone: string }>) => request('/api/v1/config/test', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
};
