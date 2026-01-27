// src/utils/logger.ts
type LogLevel = "debug" | "info" | "warn" | "error";
const LOGS_ENABLED = import.meta.env.VITE_ENABLE_LOGS;
const LOG_LEVEL = import.meta.env.VITE_LOG_LEVEL;

interface LogConfig {
  enabled: boolean;
  level: LogLevel;
  timestamp: boolean;
  context?: string;
}

class Logger {
  private config: LogConfig;
  private levels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor(config: Partial<LogConfig> = {}) {
    this.config = {
      enabled: LOGS_ENABLED,
      level: LOG_LEVEL || "debug",
      timestamp: true,
      ...config,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;
    return this.levels[level] >= this.levels[this.config.level];
  }

  private formatMessage(level: LogLevel, message: string): string {
    const parts: string[] = [];

    if (this.config.timestamp) {
      parts.push(`[${new Date().toISOString()}]`);
    }

    if (this.config.context) {
      parts.push(`[${this.config.context}]`);
    }

    parts.push(`[${level.toUpperCase()}]`);
    parts.push(message);

    return parts.join(" ");
  }

  private getEmoji(level: LogLevel): string {
    const emojis: Record<LogLevel, string> = {
      debug: "🔍",
      info: "ℹ️",
      warn: "⚠️",
      error: "❌",
    };
    return emojis[level];
  }

  debug(message: string, ...args: any[]): void {
    if (!this.shouldLog("debug")) return;
    console.debug(
      `${this.getEmoji("debug")} ${this.formatMessage("debug", message)}`,
      ...args
    );
  }

  info(message: string, ...args: any[]): void {
    if (!this.shouldLog("info")) return;
    console.info(
      `${this.getEmoji("info")} ${this.formatMessage("info", message)}`,
      ...args
    );
  }

  warn(message: string, ...args: any[]): void {
    if (!this.shouldLog("warn")) return;
    console.warn(
      `${this.getEmoji("warn")} ${this.formatMessage("warn", message)}`,
      ...args
    );
  }

  error(message: string, error?: Error, ...args: any[]): void {
    if (!this.shouldLog("error")) return;
    console.error(
      `${this.getEmoji("error")} ${this.formatMessage("error", message)}`,
      error,
      ...args
    );
  }

  // Create child logger with context
  child(context: string): Logger {
    return new Logger({
      ...this.config,
      context: this.config.context
        ? `${this.config.context}:${context}`
        : context,
    });
  }

  // Performance timing
  time(label: string): void {
    if (!this.config.enabled) return;
    console.time(`⏱️ ${label}`);
  }

  timeEnd(label: string): void {
    if (!this.config.enabled) return;
    console.timeEnd(`⏱️ ${label}`);
  }

  // Group logging
  group(label: string): void {
    if (!this.config.enabled) return;
    console.group(`📁 ${label}`);
  }

  groupEnd(): void {
    if (!this.config.enabled) return;
    console.groupEnd();
  }
}

// Export singleton instance
export const logger = new Logger();

// Export class for custom instances
export { Logger };
