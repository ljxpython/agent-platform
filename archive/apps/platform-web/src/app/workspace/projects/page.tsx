"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ColumnResizeHandle, useResizableColumns } from "@/components/platform/column-resize";
import { ConfirmDialog } from "@/components/platform/confirm-dialog";
import { ListSearch } from "@/components/platform/list-search";
import {
  PageStateEmpty,
  PageStateError,
  PageStateLoading,
  PageStateNotice,
} from "@/components/platform/page-state";
import { DEFAULT_PAGE_SIZE_OPTIONS, PaginationControls } from "@/components/platform/pagination-controls";
import { deleteProject, listProjectsPage, type ManagementProject } from "@/lib/management-api/projects";
import { useWorkspaceContext } from "@/providers/WorkspaceContext";


export default function ProjectsPage() {
  const projectColumnKeys = ["index", "name", "description", "status", "actions"] as const;
  const { projectId, setProjectId, projects, currentProject, loading: projectsLoading } = useWorkspaceContext();
  const [items, setItems] = useState<ManagementProject[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [customPage, setCustomPage] = useState("1");
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [projectPickerQuery, setProjectPickerQuery] = useState("");
  const [pendingProjectId, setPendingProjectId] = useState("");
  const [loading, setLoading] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [pendingDeleteProject, setPendingDeleteProject] = useState<ManagementProject | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const { columnWidths, startResize, resetColumnWidth, resizingColumnIndex } = useResizableColumns([80, 220, 280, 140, 220], {
    storageKey: "table-columns-projects",
  });
  const tableWidth = Math.max(760, columnWidths.reduce((sum, width) => sum + width, 0));

  const refreshList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listProjectsPage({ limit: pageSize, offset, query });
      const rows = payload.items;
      setItems(rows);
      setTotal(payload.total);
      if (payload.total > 0 && offset >= payload.total) {
        const fallbackOffset = Math.max(0, (Math.ceil(payload.total / pageSize) - 1) * pageSize);
        if (fallbackOffset !== offset) {
          setOffset(fallbackOffset);
          return;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [offset, pageSize, query]);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  useEffect(() => {
    setPendingProjectId(projectId);
  }, [projectId]);

  const filteredProjects = useMemo(() => {
    const normalized = projectPickerQuery.trim().toLowerCase();
    if (!normalized) {
      return projects;
    }
    return projects.filter((item) =>
      [item.name, item.description, item.id]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalized)),
    );
  }, [projectPickerQuery, projects]);

  const pendingProject = useMemo(
    () => projects.find((item) => item.id === pendingProjectId) ?? null,
    [pendingProjectId, projects],
  );

  const projectPickerOptions = useMemo(() => {
    if (!pendingProject) {
      return filteredProjects;
    }
    if (filteredProjects.some((item) => item.id === pendingProject.id)) {
      return filteredProjects;
    }
    return [pendingProject, ...filteredProjects];
  }, [filteredProjects, pendingProject]);

  async function onDeleteProject(project: ManagementProject) {
    setRemovingId(project.id);
    setError(null);
    setNotice(null);
    try {
      await deleteProject(project.id);
      if (projectId === project.id) {
        setProjectId("");
      }
      setNotice(`Deleted project: ${project.name}`);
      if (offset > 0 && items.length === 1) {
        setOffset((prev) => Math.max(0, prev - pageSize));
      }
      await refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project");
    } finally {
      setPendingDeleteProject((current) => (current?.id === project.id ? null : current));
      setRemovingId(null);
    }
  }

  function applyCustomPage() {
    const parsed = Number(customPage);
    if (!Number.isFinite(parsed)) {
      return;
    }
    const normalizedPage = Math.max(1, Math.floor(parsed));
    setOffset((normalizedPage - 1) * pageSize);
    setCustomPage(String(normalizedPage));
  }

  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(maxPage, Math.floor(offset / pageSize) + 1);
  const switchDisabled = projectsLoading || !pendingProjectId || pendingProjectId === projectId;

  return (
    <section className="p-4 sm:p-6">
      <h2 className="text-xl font-semibold tracking-tight">Projects</h2>
      <p className="text-muted-foreground mt-2 text-sm">Project list view. Create operations are on a dedicated page.</p>

      <div className="mt-4 rounded-lg border border-border/80 bg-card/70 p-4">
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold tracking-tight">Global Project Context</h3>
          <p className="text-muted-foreground text-sm">
            All workspace pages read the global `projectId` from here. Switch it once, then Testcase, Chat, SQL Agent and other pages follow the same context.
          </p>
        </div>

        <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,220px)_minmax(0,1fr)_auto]">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Search project</span>
            <input
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              placeholder="Search by name, description or ID"
              value={projectPickerQuery}
              onChange={(event) => setProjectPickerQuery(event.target.value)}
            />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Project selector</span>
            <select
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={pendingProjectId}
              onChange={(event) => setPendingProjectId(event.target.value)}
              disabled={projectsLoading || projectPickerOptions.length === 0}
            >
              {projectPickerOptions.length === 0 ? (
                <option value="">No matching projects</option>
              ) : null}
              {projectPickerOptions.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name} ({project.status})
                </option>
              ))}
            </select>
          </label>

          <div className="flex items-end gap-2">
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => {
                if (!pendingProjectId || pendingProjectId === projectId) {
                  return;
                }
                setProjectId(pendingProjectId);
                setNotice(`Switched current project to ${pendingProject?.name || pendingProjectId}`);
              }}
              disabled={switchDisabled}
            >
              Switch Project
            </button>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
              onClick={() => setProjectPickerQuery("")}
              disabled={projectsLoading || projectPickerQuery.length === 0}
            >
              Clear
            </button>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full border border-border/80 px-2 py-1">
            Current: {currentProject?.name || "No project selected"}
          </span>
          <span className="rounded-full border border-border/80 px-2 py-1" title={projectId || undefined}>
            ID: {projectId || "-"}
          </span>
          <span className="rounded-full border border-border/80 px-2 py-1">
            Status: {currentProject?.status || "-"}
          </span>
          <span className="rounded-full border border-border/80 px-2 py-1">
            Matches: {filteredProjects.length}
          </span>
        </div>
      </div>

      <div className="mt-4">
        <Link
          href="/workspace/projects/new"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-foreground px-3 text-sm font-medium text-background"
        >
          Go to Create Project
        </Link>
      </div>

      <ListSearch
        value={searchInput}
        placeholder="Search by project name or description"
        onValueChange={setSearchInput}
        onSearch={(keyword) => {
          setOffset(0);
          setCustomPage("1");
          setQuery(keyword);
        }}
        onClear={() => {
          setQuery("");
          setOffset(0);
          setCustomPage("1");
        }}
      />

      {loading ? <PageStateLoading /> : null}
      {error ? <PageStateError message={error} /> : null}
      {notice ? <PageStateNotice message={notice} /> : null}

      {!loading && !error && items.length === 0 ? <PageStateEmpty message="No projects found." /> : null}

      {!loading && !error && items.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border/80 bg-card/70">
          <table className="min-w-[760px] table-fixed text-sm" style={{ width: `max(100%, ${tableWidth}px)` }}>
            <colgroup>
              {columnWidths.map((width, index) => (
                <col key={projectColumnKeys[index]} style={{ width }} />
              ))}
            </colgroup>
            <thead className="bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="relative px-4 py-2">#<ColumnResizeHandle active={resizingColumnIndex === 0} onMouseDown={(event) => startResize(0, event)} onDoubleClick={() => resetColumnWidth(0)} /></th>
                <th className="relative px-4 py-2">Name<ColumnResizeHandle active={resizingColumnIndex === 1} onMouseDown={(event) => startResize(1, event)} onDoubleClick={() => resetColumnWidth(1)} /></th>
                <th className="relative px-4 py-2">Description<ColumnResizeHandle active={resizingColumnIndex === 2} onMouseDown={(event) => startResize(2, event)} onDoubleClick={() => resetColumnWidth(2)} /></th>
                <th className="relative px-4 py-2">Status<ColumnResizeHandle active={resizingColumnIndex === 3} onMouseDown={(event) => startResize(3, event)} onDoubleClick={() => resetColumnWidth(3)} /></th>
                <th className="relative px-4 py-2">Actions<ColumnResizeHandle active={resizingColumnIndex === 4} onMouseDown={(event) => startResize(4, event)} onDoubleClick={() => resetColumnWidth(4)} /></th>
              </tr>
            </thead>
            <tbody>
              {items.map((project, index) => (
                <tr key={project.id} className="border-t transition-colors hover:bg-muted/30">
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{offset + index + 1}</td>
                  <td className="px-4 py-2 font-medium">
                    <Link
                      href={`/workspace/projects/${project.id}`}
                      className="text-primary underline-offset-2 hover:underline"
                      onClick={() => setProjectId(project.id)}
                    >
                      {project.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{project.description || "-"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{project.status}</td>
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-background px-2 text-xs"
                        onClick={() => {
                          setProjectId(project.id);
                          if (typeof window !== "undefined") {
                            window.location.href = `/workspace/projects/${project.id}`;
                          }
                        }}
                        disabled={removingId === project.id}
                      >
                        Manage
                      </button>
                      <button
                        type="button"
                        className="inline-flex h-8 items-center justify-center rounded-md border border-destructive/40 bg-destructive/5 px-2 text-xs text-destructive"
                        onClick={() => setPendingDeleteProject(project)}
                        disabled={removingId === project.id}
                      >
                        {removingId === project.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <ConfirmDialog
        open={pendingDeleteProject !== null}
        title="Delete project"
        description={pendingDeleteProject ? `Are you sure you want to delete project "${pendingDeleteProject.name}"?` : undefined}
        confirmLabel="Delete"
        confirmLabelLoading="Deleting..."
        loading={pendingDeleteProject ? removingId === pendingDeleteProject.id : false}
        onCancel={() => setPendingDeleteProject(null)}
        onConfirm={() => {
          if (!pendingDeleteProject) {
            return;
          }
          void onDeleteProject(pendingDeleteProject);
        }}
      />

      {!loading && !error ? (
        <PaginationControls
          total={total}
          offset={offset}
          pageSize={pageSize}
          customPage={customPage}
          currentPage={currentPage}
          maxPage={maxPage}
          loading={loading}
          pageSizeOptions={DEFAULT_PAGE_SIZE_OPTIONS}
          onPageSizeChange={(next) => {
            setOffset(0);
            setPageSize(next);
            setCustomPage("1");
          }}
          onCustomPageChange={setCustomPage}
          onApplyCustomPage={applyCustomPage}
          onPrevious={() => setOffset((prev) => Math.max(0, prev - pageSize))}
          onNext={() => setOffset((prev) => prev + pageSize)}
          previousDisabled={loading || offset === 0}
          nextDisabled={loading || offset + pageSize >= total}
        />
      ) : null}
    </section>
  );
}
