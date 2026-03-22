import { validate } from "uuid";

export type ThreadTargetType = "assistant" | "graph";

function isThreadTargetType(value: string | null): value is ThreadTargetType {
  return value === "assistant" || value === "graph";
}

export function resolveThreadTarget({
  assistantId,
  graphId,
  targetType,
  envAssistantId,
}: {
  assistantId: string;
  graphId: string;
  targetType: string;
  envAssistantId?: string;
}): {
  targetType: ThreadTargetType;
  targetId: string;
} {
  const resolvedAssistantId = assistantId || envAssistantId || "";
  const resolvedGraphId = graphId || resolvedAssistantId;
  const resolvedTargetType = isThreadTargetType(targetType)
    ? targetType
    : validate(resolvedAssistantId)
      ? "assistant"
      : "graph";

  return {
    targetType: resolvedTargetType,
    targetId:
      resolvedTargetType === "graph"
        ? resolvedGraphId
        : resolvedAssistantId || resolvedGraphId,
  };
}

export function buildThreadTargetMetadata(
  targetType: ThreadTargetType,
  targetId: string,
): { graph_id: string } | { assistant_id: string } {
  if (targetType === "graph") {
    return { graph_id: targetId };
  }

  return { assistant_id: targetId };
}
