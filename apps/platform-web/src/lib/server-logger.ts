import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

type LogLevel = "debug" | "info" | "warn" | "error";

type ServerLogEntry = {
  level?: LogLevel;
  event: string;
  message: string;
  context?: Record<string, unknown>;
};

async function writeLog(fileName: string | undefined, entry: ServerLogEntry) {
  if (!fileName) {
    return;
  }

  const logsDir = process.env.FRONTEND_LOGS_DIR?.trim();
  if (!logsDir) {
    return;
  }

  const targetPath = path.join(logsDir, fileName);
  await mkdir(path.dirname(targetPath), { recursive: true });
  await appendFile(targetPath, `${JSON.stringify(entry)}\n`, "utf8");
}

async function emitLog(prefix: string, fileName: string | undefined, entry: ServerLogEntry) {
  const level = entry.level ?? "info";
  const logMethod =
    level === "error"
      ? console.error
      : level === "warn"
        ? console.warn
        : level === "debug"
          ? console.debug
          : console.info;

  logMethod(prefix, entry.event, entry.message, entry.context ?? {});

  try {
    await writeLog(fileName, {
      ...entry,
      level,
    });
  } catch (error) {
    console.warn(`${prefix} file_log_failed`, String(error));
  }
}

export async function logFrontendServer(entry: ServerLogEntry) {
  await emitLog(
    "[platform-web][server]",
    process.env.FRONTEND_SERVER_LOG_FILE,
    entry,
  );
}

export async function logFrontendClient(entry: ServerLogEntry) {
  await emitLog(
    "[platform-web][client]",
    process.env.FRONTEND_CLIENT_LOG_FILE,
    entry,
  );
}
