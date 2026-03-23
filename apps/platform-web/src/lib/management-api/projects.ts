import { requestManagementJson } from "./common";

export type ManagementProject = {
  id: string;
  name: string;
  description?: string | null;
  status?: string;
};

type ListProjectsPageResponse = {
  items: ManagementProject[];
  total: number;
};

export async function listProjects(params: {
  limit?: number;
  offset?: number;
  query?: string;
} = {}): Promise<ManagementProject[]> {
  const payload = await listProjectsPage(params);
  return payload.items;
}

export async function listProjectsPage(params: {
  limit?: number;
  offset?: number;
  query?: string;
} = {}): Promise<ListProjectsPageResponse> {
  const search = new URLSearchParams();
  if (typeof params.limit === "number") {
    search.set("limit", String(params.limit));
  }
  if (typeof params.offset === "number") {
    search.set("offset", String(params.offset));
  }
  if (params.query) {
    search.set("query", params.query);
  }

  const suffix = search.toString();
  return requestManagementJson<ListProjectsPageResponse>(
    `/projects${suffix ? `?${suffix}` : ""}`,
  );
}

export async function createProject(payload: {
  name: string;
  description?: string;
}): Promise<ManagementProject> {
  return requestManagementJson<ManagementProject>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteProject(projectId: string): Promise<{ ok: boolean }> {
  return requestManagementJson<{ ok: boolean }>(`/projects/${projectId}`, {
    method: "DELETE",
  });
}
