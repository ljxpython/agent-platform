type InterruptCandidate = {
  value?: {
    action_requests?: unknown;
    review_configs?: unknown;
  };
};

export function isAgentInboxInterruptSchema(
  value: unknown,
): value is InterruptCandidate {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as InterruptCandidate;
  return (
    Array.isArray(candidate.value?.action_requests) &&
    Array.isArray(candidate.value?.review_configs)
  );
}
