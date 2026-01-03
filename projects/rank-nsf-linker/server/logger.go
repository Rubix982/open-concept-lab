package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sync"

	"github.com/sirupsen/logrus"
)

var (
	logger    *logrus.Logger
	once      sync.Once
	LogsRoute string
)

func init() {
	LogsRoute = fmt.Sprintf("%s/logs/log", LOGGING_SERVICE_ROUTE)
}

// LoggingServiceHook sends log entries to an HTTP logging service
type LoggingServiceHook struct{}

func (h *LoggingServiceHook) Levels() []logrus.Level {
	return logrus.AllLevels[:logrus.InfoLevel+1]
}

func (h *LoggingServiceHook) Fire(entry *logrus.Entry) error {
	payload := map[string]interface{}{
		"level":     entry.Level.String(),
		"message":   entry.Message,
		"data":      entry.Data,
		"caller":    fmt.Sprintf("%s:%d", entry.Caller.File, entry.Caller.Line),
		"timestamp": entry.Time.Format("2006-01-02T15:04:05.000Z07:00"),
	}

	logPrefix := "[LoggingServiceHookFire]"

	body, err := json.Marshal(payload)
	if err != nil {
		// fallback to console if JSON marshaling fails
		logger.Errorf("%s - Failed to marshal log entry: %v", logPrefix, err)
		return err
	}

	go func() {
		req, err := http.NewRequest("POST", LogsRoute, bytes.NewBuffer(body))
		if err != nil {
			logger.Errorf("%s - Failed to create HTTP request for log: %v", logPrefix, err)
			return
		}
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		if _, err := client.Do(req); err != nil {
			logger.Errorf("%s - Failed to send log to logging service: %v", logPrefix, err)
		}
	}()

	return nil
}

// GetLogger returns the singleton logger instance
func init() {
	once.Do(func() {
		logger = logrus.New()
		logger.SetOutput(os.Stdout)
		logger.SetLevel(logrus.InfoLevel)
		logger.SetFormatter(&logrus.TextFormatter{
			ForceColors:     true,
			FullTimestamp:   true,
			TimestampFormat: "15:04:05",
			PadLevelText:    true,
			CallerPrettyfier: func(f *runtime.Frame) (string, string) {
				return "", fmt.Sprintf(" - %s:%d", filepath.Base(f.File), f.Line)
			},
		})
		logger.SetReportCaller(true)
		logger.AddHook(&LoggingServiceHook{})
	})
}
