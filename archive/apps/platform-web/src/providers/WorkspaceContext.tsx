"use client";

import { listProjects, type ManagementProject } from "@/lib/management-api/projects";
import { logClient } from "@/lib/client-logger";
import {
  clearStoredWorkspaceProjectId,
  getStoredWorkspaceProjectId,
  setStoredWorkspaceProjectId,
} from "@/lib/workspace-project-preference";
import { useQueryState } from "nuqs";
import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";


type WorkspaceContextValue = {
  projectId: string;
  setProjectId: (value: string) => void;
  assistantId: string;
  setAssistantId: (value: string) => void;
  projects: ManagementProject[];
  currentProject: ManagementProject | null;
  loading: boolean;
};


const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);


export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectId] = useQueryState("projectId", { defaultValue: "" });
  const [assistantId, setAssistantId] = useQueryState("assistantId", { defaultValue: "" });
  const [, setThreadId] = useQueryState("threadId", { defaultValue: "" });
  const [projects, setProjects] = useState<ManagementProject[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      setLoading(true);
      try {
        const rows = await listProjects({ limit: 100, offset: 0 });
        if (cancelled) {
          return;
        }
        setProjects(rows);

        const normalizedProjectId = (projectId ?? "").trim();
        const projectStillValid = rows.some((item) => item.id === normalizedProjectId);
        if (projectStillValid) {
          setStoredWorkspaceProjectId(normalizedProjectId);
          return;
        }

        const preferredProjectId = getStoredWorkspaceProjectId();
        const preferredProjectStillValid = rows.some((item) => item.id === preferredProjectId);
        if (preferredProjectStillValid) {
          setProjectId(preferredProjectId);
          setStoredWorkspaceProjectId(preferredProjectId);
          return;
        }

        if (rows.length > 0) {
          setProjectId(rows[0].id);
          setStoredWorkspaceProjectId(rows[0].id);
          return;
        }
        if (rows.length === 0) {
          setProjectId("");
          clearStoredWorkspaceProjectId();
        }
      } catch (err) {
        if (!cancelled) {
          setProjects([]);
        }
        logClient({
          level: "error",
          event: "workspace_load_projects_error",
          message: "Failed to load projects",
          context: { error: String(err) },
        });
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProjects();

    return () => {
      cancelled = true;
    };
  }, [projectId, setProjectId]);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      projectId: projectId ?? "",
      setProjectId: (value: string) => {
        const normalizedValue = value.trim();
        setProjectId(normalizedValue);
        if (normalizedValue) {
          setStoredWorkspaceProjectId(normalizedValue);
        } else {
          clearStoredWorkspaceProjectId();
        }
        setThreadId(null);
        setAssistantId("");
      },
      assistantId: assistantId ?? "",
      setAssistantId,
      projects,
      currentProject: projects.find((item) => item.id === (projectId ?? "")) ?? null,
      loading,
    }),
    [assistantId, loading, projectId, projects, setAssistantId, setProjectId, setThreadId],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}


// eslint-disable-next-line react-refresh/only-export-components
export function useWorkspaceContext() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspaceContext must be used within WorkspaceProvider");
  }
  return context;
}
