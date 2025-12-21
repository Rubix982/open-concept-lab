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
	"time"

	"github.com/sirupsen/logrus"
)

var (
	logger    *logrus.Logger
	once      sync.Once
	LogsRoute string
)

func init() {
	LogsRoute = fmt.Sprintf("%s/logs/batch", LOGGING_SERVICE_ROUTE)
}

// LoggingServiceHook sends log entries to an HTTP logging service in batches
type LoggingServiceHook struct {
	buffer    []map[string]interface{}
	mu        sync.Mutex
	batchSize int
}

func NewLoggingServiceHook() *LoggingServiceHook {
	hook := &LoggingServiceHook{
		buffer:    make([]map[string]interface{}, 0, 200),
		batchSize: 200, // Flush after 200 logs
	}

	// Start background flusher (every 5 seconds)
	go hook.periodicFlush()

	return hook
}

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

	h.mu.Lock()
	h.buffer = append(h.buffer, payload)
	shouldFlush := len(h.buffer) >= h.batchSize
	h.mu.Unlock()

	// Flush if buffer is full
	if shouldFlush {
		go h.flush()
	}

	return nil
}

// periodicFlush flushes logs every 5 seconds
func (h *LoggingServiceHook) periodicFlush() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		h.flush()
	}
}

// flush sends batched logs to the logging service
func (h *LoggingServiceHook) flush() {
	h.mu.Lock()
	if len(h.buffer) == 0 {
		h.mu.Unlock()
		return
	}

	// Copy buffer and clear it
	batch := make([]map[string]interface{}, len(h.buffer))
	copy(batch, h.buffer)
	h.buffer = h.buffer[:0] // Clear buffer
	h.mu.Unlock()

	// Send batch
	body, err := json.Marshal(map[string]interface{}{
		"logs":  batch,
		"count": len(batch),
	})
	if err != nil {
		fmt.Printf("Failed to marshal log batch (%d logs): %v\n", len(batch), err)
		return
	}

	req, err := http.NewRequest("POST", LogsRoute, bytes.NewBuffer(body))
	if err != nil {
		fmt.Printf("Failed to create HTTP request for log batch: %v\n", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Failed to send log batch (%d logs): %v\n", len(batch), err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("Logging service returned status %d for batch of %d logs\n", resp.StatusCode, len(batch))
	}
}

// Flush is called on shutdown to send remaining logs
func (h *LoggingServiceHook) Flush() {
	h.flush()
}

// GetLogger returns the singleton logger instance
func init() {
	once.Do(func() {
		logger = logrus.New()
		logger.SetOutput(os.Stdout)
		logger.SetLevel(logrus.DebugLevel)
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
