import type { AIMessage, Message, ToolMessage } from "@langchain/langgraph-sdk";

export const DO_NOT_RENDER_ID_PREFIX = "__synthetic_tool_result__";

function buildSyntheticToolMessage(
  toolCall: NonNullable<AIMessage["tool_calls"]>[number],
): ToolMessage {
  return {
    id: `${DO_NOT_RENDER_ID_PREFIX}${toolCall.id ?? toolCall.name ?? "tool"}`,
    type: "tool",
    name: toolCall.name ?? "",
    tool_call_id: toolCall.id ?? "",
    content: "Tool call pending.",
  };
}

export function ensureToolCallsHaveResponses(messages: Message[]): Message[] {
  const existingToolCallIds = new Set(
    messages
      .filter((message): message is ToolMessage => message.type === "tool")
      .map((message) => message.tool_call_id)
      .filter((value): value is string => typeof value === "string" && value.length > 0),
  );

  return messages.flatMap((message) => {
    if (message.type !== "ai" || !Array.isArray(message.tool_calls)) {
      return [message];
    }

    const syntheticMessages = message.tool_calls
      .filter((toolCall) => toolCall.id && !existingToolCallIds.has(toolCall.id))
      .map((toolCall) => buildSyntheticToolMessage(toolCall));

    return [message, ...syntheticMessages];
  });
}
