export interface EvalSet {
  id: number;
  name: string;
  display_index?: number;
  count: number;
  created_at: string;
  updated_at: string;
  deleted: boolean;
}
export interface EvalData {
  id: number;
  eval_set_id: number;
  content: string;
  expected?: string | null;
  intent?: string | null;
  deleted: boolean;
}
export interface EvalResult {
  id: number;
  eval_set_id: number;
  eval_data_id: number;
  actual_result?: string | null;
  actual_intent?: string | null;
  score?: number | null;
  agent_version?: string | null;
  kdb: number;
  exec_time: string;
  deleted: boolean;
}
export interface ConfigInfo {
  url: string;
  api_key: string;
  hotline: string;
  userphone: string;
  updated?: boolean;
  path?: string;
}
export interface BatchExecResponse {
  total: number;
  succeeded: number;
  failed: number;
  result_ids: number[];
  errors: string[];
  durations_ms: number[];
}
export interface MultiSetExecSetResult {
  eval_set_id: number;
  total: number;
  succeeded: number;
  failed: number;
  result_ids: number[];
  errors: string[];
  durations_ms: number[];
}
export interface MultiSetExecResponse {
  sets: MultiSetExecSetResult[];
  overall_total: number;
  overall_succeeded: number;
  overall_failed: number;
}
