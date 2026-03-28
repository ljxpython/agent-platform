import { useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Circle,
  Clock3,
  Copy,
  Download,
  FileText,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "../ui/button";

type TodoStatus = "pending" | "in_progress" | "completed";

type NormalizedTodo = {
  id: string;
  content: string;
  status: TodoStatus;
};

type NormalizedFile = {
  path: string;
  content: string;
};

function normalizeTodoStatus(value: unknown): TodoStatus {
  if (value === "in_progress") return "in_progress";
  if (value === "completed") return "completed";
  return "pending";
}

function normalizeTodos(values: Record<string, unknown> | undefined): NormalizedTodo[] {
  const rawTodos = values?.todos;
  if (!Array.isArray(rawTodos)) {
    return [];
  }

  return rawTodos
    .map((item, index) => {
      if (!item || typeof item !== "object") {
        return null;
      }
      const todo = item as Record<string, unknown>;
      const content =
        typeof todo.content === "string"
          ? todo.content
          : typeof todo.text === "string"
            ? todo.text
            : "";
      if (!content.trim()) {
        return null;
      }
      const id =
        typeof todo.id === "string" && todo.id.trim()
          ? todo.id
          : `todo-${index + 1}`;
      return {
        id,
        content: content.trim(),
        status: normalizeTodoStatus(todo.status),
      } satisfies NormalizedTodo;
    })
    .filter((item): item is NormalizedTodo => item !== null);
}

function normalizeFileContent(rawContent: unknown): string {
  if (typeof rawContent === "string") {
    return rawContent;
  }

  if (rawContent && typeof rawContent === "object") {
    const fileRecord = rawContent as Record<string, unknown>;
    if ("content" in fileRecord) {
      const content = fileRecord.content;
      if (typeof content === "string") {
        return content;
      }
      if (Array.isArray(content)) {
        return content.map((part) => String(part)).join("\n");
      }
      if (content != null) {
        return JSON.stringify(content, null, 2);
      }
      return "";
    }

    return JSON.stringify(fileRecord, null, 2);
  }

  if (rawContent == null) {
    return "";
  }

  return String(rawContent);
}

function normalizeFiles(values: Record<string, unknown> | undefined): NormalizedFile[] {
  const rawFiles = values?.files;
  if (!rawFiles || typeof rawFiles !== "object" || Array.isArray(rawFiles)) {
    return [];
  }

  return Object.entries(rawFiles as Record<string, unknown>)
    .map(([path, rawContent]) => ({
      path,
      content: normalizeFileContent(rawContent),
    }))
    .sort((a, b) => a.path.localeCompare(b.path));
}

function TodoStatusIcon({ status }: { status: TodoStatus }) {
  if (status === "completed") {
    return <CheckCircle2 className="size-3.5 text-emerald-600" />;
  }
  if (status === "in_progress") {
    return <Clock3 className="size-3.5 text-amber-600" />;
  }
  return <Circle className="size-3.5 text-muted-foreground" />;
}

function downloadTextFile(fileName: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function TasksFilesPanel({
  values,
}: {
  values: Record<string, unknown> | undefined;
}) {
  const todos = useMemo(() => normalizeTodos(values), [values]);
  const files = useMemo(() => normalizeFiles(values), [values]);
  const [metaOpen, setMetaOpen] = useState<"tasks" | "files" | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const prevTodosCount = useRef(0);
  const prevFilesCount = useRef(0);

  useEffect(() => {
    if (prevTodosCount.current === 0 && todos.length > 0) {
      setMetaOpen((prev) => prev ?? "tasks");
    }
    prevTodosCount.current = todos.length;
  }, [todos.length]);

  useEffect(() => {
    if (prevFilesCount.current === 0 && files.length > 0) {
      setMetaOpen((prev) => prev ?? "files");
    }
    prevFilesCount.current = files.length;
  }, [files.length]);

  useEffect(() => {
    if (files.length === 0) {
      setSelectedFilePath(null);
      return;
    }
    if (!selectedFilePath || !files.some((file) => file.path === selectedFilePath)) {
      setSelectedFilePath(files[0].path);
    }
  }, [files, selectedFilePath]);

  const selectedFile = useMemo(
    () => files.find((file) => file.path === selectedFilePath) ?? null,
    [files, selectedFilePath],
  );

  const groupedTodos = useMemo(
    () => ({
      in_progress: todos.filter((todo) => todo.status === "in_progress"),
      pending: todos.filter((todo) => todo.status === "pending"),
      completed: todos.filter((todo) => todo.status === "completed"),
    }),
    [todos],
  );

  const totalTasks = todos.length;
  const completedTasks = groupedTodos.completed.length;
  const activeTask = groupedTodos.in_progress[0] ?? groupedTodos.pending[0] ?? null;
  const hasTasks = totalTasks > 0;
  const hasFiles = files.length > 0;

  if (!hasTasks && !hasFiles) {
    return null;
  }

  const handleCopyFile = async () => {
    if (!selectedFile) return;
    try {
      await navigator.clipboard.writeText(selectedFile.content);
      toast.success("File content copied");
    } catch {
      toast.error("Failed to copy file content");
    }
  };

  const handleDownloadFile = () => {
    if (!selectedFile) return;
    try {
      downloadTextFile(selectedFile.path, selectedFile.content);
      toast.success("File downloaded");
    } catch {
      toast.error("Failed to download file");
    }
  };

  return (
    <div className="border-b border-border bg-muted/30">
      {metaOpen === null ? (
        <div className="grid grid-cols-[1fr_auto_auto] items-center">
          {hasTasks ? (
            <button
              type="button"
              onClick={() => setMetaOpen("tasks")}
              className="grid grid-cols-[auto_1fr] items-center gap-2 px-4 py-3 text-left text-sm hover:bg-accent/60"
            >
              {activeTask ? <TodoStatusIcon status={activeTask.status} /> : <Circle className="size-3.5 text-muted-foreground" />}
              <span className="truncate text-foreground">
                {activeTask
                  ? `${completedTasks}/${totalTasks} ${activeTask.content}`
                  : `${completedTasks}/${totalTasks} tasks completed`}
              </span>
            </button>
          ) : (
            <span />
          )}
          {hasFiles ? (
            <button
              type="button"
              onClick={() => setMetaOpen("files")}
              className="inline-flex items-center gap-2 px-4 py-3 text-sm text-foreground hover:bg-accent/60"
            >
              <FileText className="size-4" />
              <span>Files</span>
              <span className="rounded-full bg-emerald-700 px-1.5 py-0.5 text-[10px] text-white">
                {files.length}
              </span>
            </button>
          ) : null}
          <button
            type="button"
            className="px-3 py-3 text-sm text-muted-foreground hover:bg-accent/60"
            onClick={() => setMetaOpen(hasTasks ? "tasks" : "files")}
            aria-label="Open meta panel"
          >
            <span className="sr-only">Open</span>
          </button>
        </div>
      ) : (
        <div className="px-4 pb-3 pt-2">
          <div className="mb-2 flex items-center justify-between border-b border-border/80 pb-2">
            <div className="flex items-center gap-3 text-sm">
              {hasTasks ? (
                <button
                  type="button"
                  onClick={() => setMetaOpen(metaOpen === "tasks" ? null : "tasks")}
                  className={cn(
                    "rounded px-2 py-1",
                    metaOpen === "tasks" ? "bg-accent font-medium text-foreground" : "text-muted-foreground",
                  )}
                >
                  Tasks
                </button>
              ) : null}
              {hasFiles ? (
                <button
                  type="button"
                  onClick={() => setMetaOpen(metaOpen === "files" ? null : "files")}
                  className={cn(
                    "rounded px-2 py-1",
                    metaOpen === "files" ? "bg-accent font-medium text-foreground" : "text-muted-foreground",
                  )}
                >
                  Files ({files.length})
                </button>
              ) : null}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setMetaOpen(null)}
            >
              <X className="size-4" />
            </Button>
          </div>

          {metaOpen === "tasks" ? (
            <div className="max-h-52 overflow-y-auto pr-1">
              {totalTasks === 0 ? (
                <p className="px-2 py-3 text-xs text-muted-foreground">No tasks yet.</p>
              ) : (
                <div className="space-y-3">
                  {(["in_progress", "pending", "completed"] as const).map((statusKey) => {
                    const items = groupedTodos[statusKey];
                    if (items.length === 0) return null;
                    const label =
                      statusKey === "in_progress"
                        ? "In Progress"
                        : statusKey === "pending"
                          ? "Pending"
                          : "Completed";
                    return (
                      <div key={statusKey}>
                        <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                          {label}
                        </p>
                        <div className="space-y-1">
                          {items.map((todo) => (
                            <div key={todo.id} className="grid grid-cols-[auto_1fr] items-start gap-2 rounded-md px-2 py-1.5 hover:bg-accent/40">
                              <TodoStatusIcon status={todo.status} />
                              <span className="text-sm text-foreground">{todo.content}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="grid gap-3 lg:grid-cols-[220px_1fr]">
              <div className="max-h-52 overflow-y-auto rounded-md border border-border/80 bg-background">
                {files.map((file) => (
                  <button
                    key={file.path}
                    type="button"
                    className={cn(
                      "block w-full truncate border-b border-border/60 px-3 py-2 text-left text-sm last:border-b-0",
                      selectedFilePath === file.path ? "bg-accent text-foreground" : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
                    )}
                    onClick={() => setSelectedFilePath(file.path)}
                    title={file.path}
                  >
                    {file.path}
                  </button>
                ))}
              </div>
              <div className="min-h-0 rounded-md border border-border/80 bg-background">
                {selectedFile ? (
                  <div className="flex h-full min-h-[210px] flex-col">
                    <div className="flex items-center justify-between border-b border-border/80 px-3 py-2">
                      <p className="truncate text-xs text-foreground" title={selectedFile.path}>
                        {selectedFile.path}
                      </p>
                      <div className="flex items-center gap-1">
                        <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={handleCopyFile}>
                          <Copy className="mr-1 size-3.5" />
                          Copy
                        </Button>
                        <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={handleDownloadFile}>
                          <Download className="mr-1 size-3.5" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <pre className="h-full max-h-52 overflow-auto px-3 py-2 text-xs leading-5 text-foreground">
                      {selectedFile.content || "<empty file>"}
                    </pre>
                  </div>
                ) : (
                  <p className="px-3 py-4 text-xs text-muted-foreground">No files available.</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

