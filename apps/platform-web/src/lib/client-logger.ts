type LogLevel = "debug" | "info" | "warn" | "error";

type ClientLogEntry = {
  level?: LogLevel;
  event: string;
  message: string;
  context?: Record<string, unknown>;
};

export async function logClient(entry: ClientLogEntry) {
  const payload = {
    level: entry.level ?? "info",
    event: entry.event,
    message: entry.message,
    context: entry.context ?? {},
    page: typeof window === "undefined" ? undefined : window.location.pathname,
    query: typeof window === "undefined" ? undefined : window.location.search,
  };

  const logMethod =
    payload.level === "error"
      ? console.error
      : payload.level === "warn"
        ? console.warn
        : payload.level === "debug"
          ? console.debug
          : console.info;
  logMethod("[platform-web]", payload.event, payload.message, payload.context);

  if (typeof window === "undefined") {
    return;
  }

  try {
    await fetch("/api/client-logs", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch {
    // Ignore client log transport failures in local dev.
  }
}
