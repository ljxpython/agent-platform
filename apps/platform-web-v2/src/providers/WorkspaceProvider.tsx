"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { hasOidcSession } from "@/lib/oidc-storage";
import { listProjects, type ManagementProject } from "@/lib/management-api/projects";
import {
  clearStoredWorkspaceProjectId,
  getStoredWorkspaceProjectId,
  setStoredWorkspaceProjectId,
} from "@/lib/workspace-project-preference";

type WorkspaceContextValue = {
  projectId: string;
  setProjectId: (value: string) => void;
  projects: ManagementProject[];
  currentProject: ManagementProject | null;
  loading: boolean;
  refreshProjects: () => Promise<void>;
};

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectIdState] = useState("");
  const [projects, setProjects] = useState<ManagementProject[]>([]);
  const [loading, setLoading] = useState(true);

  const loadProjects = useCallback(async () => {
    const currentProjectId = projectId;
    if (!hasOidcSession()) {
      setProjects([]);
      setProjectIdState("");
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const rows = await listProjects({ limit: 100, offset: 0 });
      setProjects(rows);

      const storedProjectId = getStoredWorkspaceProjectId();
      const nextProjectId =
        rows.find((item) => item.id === currentProjectId)?.id ||
        rows.find((item) => item.id === storedProjectId)?.id ||
        rows[0]?.id ||
        "";

      setProjectIdState(nextProjectId);
      if (nextProjectId) {
        setStoredWorkspaceProjectId(nextProjectId);
      } else {
        clearStoredWorkspaceProjectId();
      }
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      projectId,
      setProjectId: (value: string) => {
        const normalizedValue = value.trim();
        setProjectIdState(normalizedValue);
        if (normalizedValue) {
          setStoredWorkspaceProjectId(normalizedValue);
        } else {
          clearStoredWorkspaceProjectId();
        }
      },
      projects,
      currentProject: projects.find((item) => item.id === projectId) ?? null,
      loading,
      refreshProjects: loadProjects,
    }),
    [loadProjects, loading, projectId, projects],
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
