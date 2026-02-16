package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/sirupsen/logrus"
)

var (
	logger         ContextLogger
	internalLogger *logrus.Logger // For hook's own logging
	once           sync.Once
	LogsRoute      string
)

// LoggingServiceHook sends log entries to an HTTP logging service in batches
type LoggingServiceHook struct {
	buffer         []map[string]interface{}
	mu             sync.Mutex
	batchSize      int
	flushInterval  time.Duration
	circuitBreaker *LoggingCircuitBreaker
	inFire         atomic.Bool // Prevent re-entrant calls
}

type LoggingCircuitBreaker struct {
	state        atomic.Uint32 // 0=closed, 1=open, 2=half-open
	failureCount atomic.Uint32
	lastFailure  atomic.Int64
	lastSuccess  atomic.Int64
	threshold    uint32
	timeout      time.Duration

	// Track if we've logged the "service down" message
	downMessageLogged atomic.Bool
	droppedLogs       atomic.Uint64
	sentLogs          atomic.Uint64
}

// ContextLogger wraps logrus.Logger and auto-extracts colly.Context fields
type ContextLogger struct {
	logger *logrus.Logger
}

// NewContextLogger creates a logger that auto-includes context fields
func NewContextLogger(logger *logrus.Logger) ContextLogger {
	logger.SetReportCaller(true) // Log the caller information
	return ContextLogger{
		logger: logger,
	}
}

// extractFields uses reflection to extract all k-v pairs from colly.Context
func (cl *ContextLogger) extractFields(ctx *colly.Context) logrus.Fields {
	fields := logrus.Fields{}

	if ctx == nil {
		return fields
	}

	// colly.Context wraps a *sync.Map in field "contextMap"
	v := reflect.ValueOf(ctx).Elem()
	mapField := v.FieldByName("contextMap")

	if !mapField.IsValid() || mapField.IsNil() || mapField.Type() != reflect.TypeOf(&sync.Map{}) || mapField.IsZero() {
		return fields
	}

	if !mapField.CanInterface() {
		return fields
	}

	// Get the sync.Map
	syncMap, ok := mapField.Interface().(*sync.Map)
	if !ok {
		return fields
	}

	// Extract all key-value pairs
	syncMap.Range(func(key, value interface{}) bool {
		if keyStr, ok := key.(string); ok {
			fields[keyStr] = value
		}
		return true
	})

	return fields
}

// Info logs message with all context fields
func (cl *ContextLogger) Info(ctx *colly.Context, msg string) {
	cl.logger.WithFields(cl.extractFields(ctx)).Info(msg)
}

// Infof logs formatted message with all context fields
func (cl *ContextLogger) Infof(ctx *colly.Context, format string, args ...interface{}) {
	cl.logger.WithFields(cl.extractFields(ctx)).Infof(format, args...)
}

// Error logs error with all context fields
func (cl *ContextLogger) Error(ctx *colly.Context, msg string) {
	cl.logger.WithFields(cl.extractFields(ctx)).Error(msg)
}

// Errorf logs formatted error with all context fields
func (cl *ContextLogger) Errorf(ctx *colly.Context, format string, args ...interface{}) {
	cl.logger.WithFields(cl.extractFields(ctx)).Errorf(format, args...)
}

// WithError logs error with err field + context fields
func (cl *ContextLogger) WithError(ctx *colly.Context, err error) *logrus.Entry {
	return cl.logger.WithFields(cl.extractFields(ctx)).WithError(err)
}

// WithField adds additional field on top of context fields
func (cl *ContextLogger) WithField(ctx *colly.Context, key string, value interface{}) *logrus.Entry {
	fields := cl.extractFields(ctx)
	fields[key] = value
	return cl.logger.WithFields(fields)
}

// WithFields merges additional fields with context fields
func (cl *ContextLogger) WithFields(ctx *colly.Context, additionalFields logrus.Fields) *logrus.Entry {
	fields := cl.extractFields(ctx)
	for k, v := range additionalFields {
		fields[k] = v
	}
	return cl.logger.WithFields(fields)
}

// Debug logs debug message with context fields
func (cl *ContextLogger) Debug(ctx *colly.Context, msg string) {
	cl.logger.WithFields(cl.extractFields(ctx)).Debug(msg)
}

// Debugf logs formatted debug message with context fields
func (cl *ContextLogger) Debugf(ctx *colly.Context, format string, args ...interface{}) {
	cl.logger.WithFields(cl.extractFields(ctx)).Debugf(format, args...)
}

// Warn logs warning with context fields
func (cl *ContextLogger) Warn(ctx *colly.Context, msg string) {
	cl.logger.WithFields(cl.extractFields(ctx)).Warn(msg)
}

// Warnf logs formatted warning with context fields
func (cl *ContextLogger) Warnf(ctx *colly.Context, format string, args ...interface{}) {
	cl.logger.WithFields(cl.extractFields(ctx)).Warnf(format, args...)
}

// Fatal logs formatted warning with context fields
func (cl *ContextLogger) Fatal(ctx *colly.Context, format string) {
	cl.logger.WithFields(cl.extractFields(ctx)).Fatal(format)
}

// Fatalf logs formatted warning with context fields
func (cl *ContextLogger) Fatalf(ctx *colly.Context, format string, args ...interface{}) {
	cl.logger.WithFields(cl.extractFields(ctx)).Fatalf(format, args...)
}

// SetFields sets multiple fields in colly.Context at once
func (cl *ContextLogger) SetFields(ctx *colly.Context, fields map[string]interface{}) {
	if ctx == nil {
		return
	}

	for key, value := range fields {
		ctx.Put(key, value)
	}
}

// SetField sets a single field (alias for ctx.Put for consistency)
func (cl *ContextLogger) SetField(ctx *colly.Context, key string, value interface{}) {
	if ctx != nil {
		ctx.Put(key, value)
	}
}

const (
	CBStateClosed = iota
	CBStateOpen
	CBStateHalfOpen
)

const (
	flushInterval = 5 * time.Second
	batchSize     = 200
)

func NewLoggingServiceHook() *LoggingServiceHook {
	hook := &LoggingServiceHook{
		buffer:        make([]map[string]interface{}, 0, batchSize),
		batchSize:     batchSize, // Flush after 200 logs
		flushInterval: flushInterval,
		circuitBreaker: &LoggingCircuitBreaker{
			threshold: 3,                // Open after 3 failures
			timeout:   60 * time.Second, // Try again after 1 minute
		},
	}

	// Start background flusher (every 5 seconds)
	go func() {
		ticker := time.NewTicker(flushInterval)
		defer ticker.Stop()
		for range ticker.C {
			hook.flush()
		}
	}()

	return hook
}

func (h *LoggingServiceHook) Levels() []logrus.Level {
	return logrus.AllLevels[:logrus.InfoLevel+1]
}

func (h *LoggingServiceHook) Fire(entry *logrus.Entry) error {
	// Prevent re-entrant calls
	if !h.inFire.CompareAndSwap(false, true) {
		// Already inside Fire(), drop this log silently
		return nil
	}
	defer h.inFire.Store(false)

	// Catch panics in Fire() itself
	defer func() {
		if r := recover(); r != nil {
			// Log to stderr directly, bypass logger
			fmt.Fprintf(os.Stderr, "PANIC in LoggingServiceHook.Fire: %v\n", r)
		}
	}()

	// Don't log messages from the hook itself to prevent infinite loops
	if caller, ok := entry.Data["component"].(string); ok {
		if caller == "LoggingServiceHook" {
			return nil
		}
	}

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
	// If circuit is open and buffer is full, drop oldest logs
	if h.circuitBreaker.state.Load() == CBStateOpen {
		if len(h.buffer) >= h.batchSize*10 { // Max 10 batches worth
			// Drop oldest half
			h.buffer = h.buffer[len(h.buffer)/2:]
		}
	}
	h.mu.Unlock()

	// Flush if buffer is full
	if shouldFlush {
		go h.flush()
	}

	return nil
}

// flush sends batched logs to the logging service
func (h *LoggingServiceHook) flush() {
	h.mu.Lock()
	if len(h.buffer) == 0 {
		h.mu.Unlock()
		return
	}

	// Check circuit breaker BEFORE trying
	if !h.circuitBreaker.Allow() {
		// Circuit is open, drop logs silently
		h.circuitBreaker.droppedLogs.Add(uint64(len(h.buffer)))
		h.buffer = h.buffer[:0] // Clear buffer to prevent memory buildup
		h.mu.Unlock()
		return
	}

	logPrefix := "[LoggingServiceHookFlush]"

	// Copy buffer and clear it
	batch := make([]map[string]interface{}, len(h.buffer))
	copy(batch, h.buffer)
	h.buffer = h.buffer[:0]
	h.mu.Unlock()

	// Send batch
	err := h.sendBatch(batch)

	if err != nil {
		h.circuitBreaker.RecordFailure()

		// Only log on FIRST failure or state transitions
		if h.circuitBreaker.ShouldLogError() {
			internalLogger.Warnf("%s - Logging service unavailable, circuit breaker opened (logs will be dropped)", logPrefix)
		}
		return
	}

	// Success - record and maybe log recovery
	if h.circuitBreaker.RecordSuccess() {
		internalLogger.Infof("%s - ✓ Logging service recovered, circuit breaker closed", logPrefix)
	}
	h.circuitBreaker.sentLogs.Add(uint64(len(batch)))
}

func (h *LoggingServiceHook) sendBatch(batch []map[string]interface{}) error {
	body, err := json.Marshal(map[string]interface{}{
		"logs":  batch,
		"count": len(batch),
	})
	if err != nil {
		return fmt.Errorf("marshal failed: %w", err)
	}

	req, err := http.NewRequest("POST", LogsRoute, bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("request creation failed: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 5 * time.Second} // Shorter timeout for logs
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("bad status: %d", resp.StatusCode)
	}

	return nil
}

func (cb *LoggingCircuitBreaker) Allow() bool {
	state := cb.state.Load()

	switch state {
	case CBStateOpen:
		// Check if timeout elapsed
		lastFail := time.Unix(cb.lastFailure.Load(), 0)
		if time.Since(lastFail) > cb.timeout {
			// Try half-open
			if cb.state.CompareAndSwap(CBStateOpen, CBStateHalfOpen) {
				cb.downMessageLogged.Store(false) // Allow logging recovery
				return true
			}
		}
		return false // Still open

	case CBStateHalfOpen:
		// Allow ONE attempt
		return true

	case CBStateClosed:
		// Normal operation
		return true
	}

	return false
}

func (cb *LoggingCircuitBreaker) RecordFailure() {
	cb.lastFailure.Store(time.Now().Unix())

	state := cb.state.Load()

	if state == CBStateHalfOpen {
		// Failed in half-open, back to open
		cb.state.Store(CBStateOpen)
		cb.downMessageLogged.Store(false) // Allow re-logging
		return
	}

	if state == CBStateClosed {
		count := cb.failureCount.Add(1)
		if count >= cb.threshold {
			cb.state.Store(CBStateOpen)
			cb.downMessageLogged.Store(false) // Allow initial log
		}
	}
}

func (cb *LoggingCircuitBreaker) RecordSuccess() bool {
	cb.lastSuccess.Store(time.Now().Unix())

	state := cb.state.Load()
	wasOpen := (state == CBStateOpen || state == CBStateHalfOpen)

	if state != CBStateClosed {
		cb.state.Store(CBStateClosed)
		cb.failureCount.Store(0)
	}

	return wasOpen // Return true if we recovered from open state
}

func (cb *LoggingCircuitBreaker) ShouldLogError() bool {
	// Only log once when circuit opens
	return cb.downMessageLogged.CompareAndSwap(false, true)
}

// Flush is called on shutdown to send remaining logs
func (h *LoggingServiceHook) Flush() {
	h.flush()
}

func buildCollyContext(w http.ResponseWriter, r *http.Request) *colly.Context {
	ctx := colly.NewContext()

	// Extract query parameters
	universityID := r.URL.Query().Get("university_id")
	universityName := r.URL.Query().Get("name")
	department := r.URL.Query().Get("department")

	// Extract path parameters (if using a router like chi/mux)
	// universityID := chi.URLParam(r, "universityID")

	// Request metadata
	ctx.Put("request_id", generateRequestID())
	ctx.Put("timestamp", time.Now().Format(time.RFC3339))
	ctx.Put("remote_addr", r.RemoteAddr)
	ctx.Put("user_agent", r.UserAgent())

	// Query parameters
	if universityID != "" {
		ctx.Put("university_id", universityID)
	}
	if universityName != "" {
		ctx.Put("university_name", universityName)
	}
	if department != "" {
		ctx.Put("department", department)
	}

	// Pagination/filtering (if applicable)
	limit := r.URL.Query().Get("limit")
	if limit == "" {
		limit = "50" // default
	}
	ctx.Put("limit", limit)

	offset := r.URL.Query().Get("offset")
	if offset == "" {
		offset = "0"
	}
	ctx.Put("offset", offset)

	// Search/filter parameters
	searchQuery := r.URL.Query().Get("q")
	if searchQuery != "" {
		ctx.Put("search_query", searchQuery)
	}

	// Error tracking
	errors := []error{}
	ctx.Put("errors", &errors)

	// Metrics
	ctx.Put("pages_visited", 0)
	ctx.Put("start_time", time.Now())

	return ctx
}

// Helper function
func generateRequestID() string {
	return fmt.Sprintf("req_%d_%s", time.Now().Unix(), randomString(8))
}

func randomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}

func init() {
	initLogger()
}

func initLogger() {
	LogsRoute = fmt.Sprintf("%s/logs/batch", LOGGING_SERVICE_ROUTE)
	once.Do(func() {
		// Internal logger (no hooks, just stdout)
		internalLogger = logrus.New()
		internalLogger.SetOutput(os.Stdout)
		internalLogger.SetLevel(logrus.WarnLevel) // Only warnings/errors
		internalLogger.SetFormatter(&logrus.TextFormatter{
			ForceColors:     true,
			FullTimestamp:   true,
			TimestampFormat: "15:04:05",
			PadLevelText:    true,
		})

		// Main logger (with hooks)
		logger = NewContextLogger(logrus.New())
		logger.logger = internalLogger
		logger.logger.SetOutput(os.Stdout)
		logger.logger.SetLevel(logrus.DebugLevel)
		logger.logger.SetFormatter(&logrus.TextFormatter{
			ForceColors:     true,
			FullTimestamp:   true,
			TimestampFormat: "15:04:05",
			PadLevelText:    true,
			CallerPrettyfier: func(f *runtime.Frame) (string, string) {
				return "", fmt.Sprintf(" - %s:%d", filepath.Base(f.File), f.Line)
			},
		})
		logger.logger.SetReportCaller(true)
		logger.logger.AddHook(NewLoggingServiceHook())
		internalLogger.Debugf("Logger initialized")
	})
}
