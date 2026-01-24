import axios from "axios";

export function errorHandler(err: Error, prefix = "") {
  const message = prefix ? `${prefix}: ${err.message}` : err.message;
  // Make a request to the logging-service
  axios
    .post("/ls/logs/log", {
      level: "error",
      message: message,
      stack: err.stack,
      timestamp: new Date().toISOString(),
    })
    .catch((loggingError) => {
      console.error(
        "Failed to log error to the logging service:",
        loggingError
      );
    });
}
