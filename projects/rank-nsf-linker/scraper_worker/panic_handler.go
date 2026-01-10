package main

import (
	"fmt"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strconv"
	"strings"
	"sync/atomic"

	"github.com/gocolly/colly/v2"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/sirupsen/logrus"
)

const (
	WORKER_GO_ROUTINE_NAME       = "nsf-scraper-worker-go-routine"
	WORKER_GO_ROUTINE_RECOVER_ID = "worker-%d"

	MAIN_GO_ROUTINE_NAME       = "nsf-scraper-main-entry"
	MAIN_GO_ROUTINE_RECOVER_ID = "main"

	PROCESS_JOB_GO_ROUTINE_NAME       = "nsf-scraper-process-job"
	PROCESS_JOB_GO_ROUTINE_RECOVER_ID = "process-job-%d"
)

var panicCounter = prometheus.NewCounterVec(
	prometheus.CounterOpts{
		Name: "scraper_panics_total",
		Help: "Total number of recovered panics",
	},
	[]string{"component"},
)

type PanicHandler struct {
	panicCount  atomic.Uint32
	serviceName string
	restartFunc func() error // optional: service restart logic
}

func NewPanicHandler(serviceName string) *PanicHandler {
	return &PanicHandler{
		serviceName: serviceName,
	}
}

func (ph *PanicHandler) Recover(component string) {
	recoverCtx := colly.NewContext()
	logger.SetFields(recoverCtx, map[string]interface{}{
		"component": component,
	})
	if r := recover(); r != nil {
		count := ph.panicCount.Add(1)

		// Get caller info
		pc, file, line, _ := runtime.Caller(2)
		funcName := runtime.FuncForPC(pc).Name()

		// Format stack trace
		stack := debug.Stack()
		logger.WithFields(recoverCtx, logrus.Fields{
			"stack": string(stack),
		}).Debug("Stack trace")
		stackLines := strings.Split(string(stack), "\n")

		// Take only relevant frames (skip runtime internals)
		relevantStack := []string{}
		for i := 0; i < len(stackLines) && i < 20; i++ {
			if strings.Contains(stackLines[i], ph.serviceName) {
				relevantStack = append(relevantStack, stackLines[i])
			}
		}

		logger.WithFields(recoverCtx, logrus.Fields{
			"panic":         fmt.Sprintf("%v", r),
			"component":     component,
			"function":      funcName,
			"location":      fmt.Sprintf("%s:%d", filepath.Base(file), line),
			"panic_count":   count,
			"goroutine_id":  getGoroutineID(),
			"stack_summary": strings.Join(relevantStack, " → "),
		}).Error("🚨 PANIC RECOVERED")

		// Alert if too many panics
		if count > 5 {
			logger.Fatal(recoverCtx, "⛔ Too many panics - shutting down")
		}

		// Optional: try restart
		if ph.restartFunc != nil {
			logger.Warn(recoverCtx, "♻️  Attempting component restart...")
			if err := ph.restartFunc(); err != nil {
				logger.WithError(recoverCtx, err).Error("Failed to restart component")
			}
		}
		panicCounter.WithLabelValues(component).Inc()
	}
}

// Extract goroutine ID from stack trace
func getGoroutineID() uint64 {
	b := make([]byte, 64)
	n := runtime.Stack(b, false)
	idField := strings.Fields(strings.TrimPrefix(string(b[:n]), "goroutine "))[0]
	id, _ := strconv.ParseUint(idField, 10, 64)
	return id
}

func handlePanic(serviceName string, component string) {
	NewPanicHandler(serviceName).Recover(component)
}

func init() {
	prometheus.MustRegister(panicCounter)
}
