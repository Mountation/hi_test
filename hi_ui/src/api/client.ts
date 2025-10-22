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
  createEvalSet: (name: string) => request<import('../types').EvalSet>('/api/v1/evalsets/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }),
  deleteEvalSet: (id: number) => request<void>(`/api/v1/evalsets/${id}`, { method: 'DELETE' }),
  uploadExcel: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request('/api/v1/evalsets/upload', { method: 'POST', body: form });
  },
  // Query job status for async background tasks
  getJobStatus: (jobId: string) => request<{ job_id: string; status: string; processed?: number; total?: number; errors?: string[] }>(`/api/v1/jobs/${jobId}`),
  listEvalData: (setId: number) => request<import('../types').EvalData[]>(`/api/v1/evalsets/${setId}/data`),
  createEvalData: (setId: number, payload: { content: string; expected?: string; intent?: string }) => request(`/api/v1/evalsets/${setId}/data`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_set_id: setId, ...payload }) }),
  deleteEvalData: (setId: number, dataId: number) => request<void>(`/api/v1/evalsets/${setId}/data/${dataId}`, { method: 'DELETE' }),
  listResultsBySet: (setId: number) => request<import('../types').EvalResult[]>(`/api/v1/evalresults/byset/${setId}`),
  listResultsByData: (evalSetId: number, corpusId: number) => request<import('../types').EvalResult[]>(`/api/v1/evalresults/bydata/${evalSetId}/${corpusId}`),
  executeSingle: (eval_data_id: number) => request<import('../types').EvalResult>('/api/v1/evalresults/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_data_id }) }),
  executeBySet: (eval_set_id: number) => request<import('../types').BatchExecResponse>(`/api/v1/evalresults/execute/byset/${eval_set_id}`, { method: 'POST' }),
  executeBySets: (eval_set_ids: number[], global_concurrency?: number) => request<import('../types').MultiSetExecResponse>('/api/v1/evalresults/execute/bysets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eval_set_ids, global_concurrency }) }),
  getConfig: () => request<import('../types').ConfigInfo>('/api/v1/config/test'),
  updateConfig: (payload: Partial<{ url: string; api_key: string; hotline: string; userphone: string }>) => request('/api/v1/config/test', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
};
