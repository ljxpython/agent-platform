import { getApiKey } from "@/lib/api-key";
import type { Thread } from "@langchain/langgraph-sdk";
import { useQueryState } from "nuqs";
import {
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  createContext,
  useContext,
  useCallback,
  useState,
} from "react";
import { createClient } from "./client";
import { buildThreadTargetMetadata, resolveThreadTarget } from "./thread-target";

interface ThreadContextType {
  getThreads: () => Promise<Thread[]>;
  threads: Thread[];
  setThreads: Dispatch<SetStateAction<Thread[]>>;
  threadsLoading: boolean;
  setThreadsLoading: Dispatch<SetStateAction<boolean>>;
}

const ThreadContext = createContext<ThreadContextType | undefined>(undefined);

export function ThreadProvider({ children }: { children: ReactNode }) {
  const envApiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL;
  const envAssistantId: string | undefined = process.env.NEXT_PUBLIC_ASSISTANT_ID;
  const [apiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || "",
  });
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const [graphId] = useQueryState("graphId", {
    defaultValue: "",
  });
  const [targetType] = useQueryState("targetType", {
    defaultValue: "",
  });
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(false);

  const getThreads = useCallback(async (): Promise<Thread[]> => {
    const finalApiUrl = apiUrl || envApiUrl || "";
    const resolvedTarget = resolveThreadTarget({
      assistantId,
      graphId,
      targetType,
      envAssistantId,
    });
    if (!finalApiUrl || !resolvedTarget.targetId) return [];

    const client = createClient(finalApiUrl, getApiKey() ?? undefined);

    const threads = await client.threads.search({
      metadata: {
        ...buildThreadTargetMetadata(
          resolvedTarget.targetType,
          resolvedTarget.targetId,
        ),
      },
      limit: 100,
    });

    return threads;
  }, [apiUrl, assistantId, envApiUrl, envAssistantId, graphId, targetType]);

  const value = {
    getThreads,
    threads,
    setThreads,
    threadsLoading,
    setThreadsLoading,
  };

  return (
    <ThreadContext.Provider value={value}>{children}</ThreadContext.Provider>
  );
}

export function useThreads() {
  const context = useContext(ThreadContext);
  if (context === undefined) {
    throw new Error("useThreads must be used within a ThreadProvider");
  }
  return context;
}
