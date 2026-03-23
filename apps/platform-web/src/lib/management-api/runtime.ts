import { requestManagementJson } from "./common";

export type RuntimeModelItem = {
  id: string;
  runtime_id: string;
  model_id: string;
  display_name: string;
  is_default: boolean;
  sync_status: string;
  last_seen_at?: string | null;
  last_synced_at?: string | null;
};

export type RuntimeToolItem = {
  id: string;
  runtime_id: string;
  tool_key: string;
  name: string;
  source: string;
  description: string;
  sync_status: string;
  last_seen_at?: string | null;
  last_synced_at?: string | null;
};

type RuntimeModelsResponse = {
  count: number;
  models: RuntimeModelItem[];
  last_synced_at?: string | null;
};

type RuntimeToolsResponse = {
  count: number;
  tools: RuntimeToolItem[];
  last_synced_at?: string | null;
};

export async function listRuntimeModels(): Promise<RuntimeModelsResponse> {
  return requestManagementJson<RuntimeModelsResponse>("/runtime/models");
}

export async function listRuntimeTools(): Promise<RuntimeToolsResponse> {
  return requestManagementJson<RuntimeToolsResponse>("/runtime/tools");
}

export async function refreshRuntimeModels(): Promise<{ ok: boolean }> {
  return requestManagementJson<{ ok: boolean }>("/catalog/models/refresh", {
    method: "POST",
  });
}

export async function refreshRuntimeTools(): Promise<{ ok: boolean }> {
  return requestManagementJson<{ ok: boolean }>("/catalog/tools/refresh", {
    method: "POST",
  });
}
