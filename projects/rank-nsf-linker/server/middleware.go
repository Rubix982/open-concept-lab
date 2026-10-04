package main

import (
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/go-chi/chi/middleware"
	chi "github.com/go-chi/chi/v5"
	colly "github.com/gocolly/colly/v2"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cast"
)

// ResponseWriter wrapper to capture HTTP status
type statusResponseWriter struct {
	http.ResponseWriter
	status int
}

func (w *statusResponseWriter) WriteHeader(code int) {
	w.status = code
	w.ResponseWriter.WriteHeader(code)
}

func LogRequest(r *http.Request, remote string, status int, duration time.Duration) *logrus.Entry {
	return logger.WithFields(colly.NewContext(), logrus.Fields{
		"method":   r.Method,
		"path":     r.URL.Path,
		"remote":   remote,
		"status":   status,
		"duration": duration,
	})
}

// RequestLogger middleware
func RequestLogger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap ResponseWriter to capture status
		ww := &statusResponseWriter{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(ww, r)

		duration := time.Since(start)
		LogRequest(r, r.RemoteAddr, ww.status, duration).Debug("Handled request")
	})
}

// explorerReady reports whether the explorer tables hold data, cached for 30 seconds. The build step
// replaces them in one transaction, so once they exist they can be served while later steps
// (embedding, which only affects search ranking) still run.
var explorerReadyCache struct {
	sync.Mutex
	at    time.Time
	ready bool
}

func explorerReady() bool {
	explorerReadyCache.Lock()
	defer explorerReadyCache.Unlock()
	if explorerReadyCache.ready || time.Since(explorerReadyCache.at) < 30*time.Second {
		return explorerReadyCache.ready
	}
	explorerReadyCache.at = time.Now()
	db, err := GetDB()
	if err != nil {
		return false
	}
	var ready bool
	if db.QueryRow(`SELECT EXISTS (SELECT 1 FROM explorer_faculty) AND EXISTS (SELECT 1 FROM explorer_universities)`).
		Scan(&ready) == nil {
		explorerReadyCache.ready = ready
	}
	return explorerReadyCache.ready
}

func PreventRequestIfPipelineIsNotCompleted(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			next.ServeHTTP(w, r)
			return
		}
		pipelineStatus := GetPipelineStatus(colly.NewContext(), cast.ToString(PIPELINE_POPULATE_POSTGRES))
		if pipelineStatus == cast.ToString(PIPELINE_STATUS_COMPLETED) ||
			(strings.HasPrefix(r.URL.Path, "/explorer/") && explorerReady()) {
			next.ServeHTTP(w, r)
			return
		}

		httpStatus := http.StatusServiceUnavailable
		if pipelineStatus == cast.ToString(PIPELINE_STATUS_FAILED) {
			httpStatus = http.StatusInternalServerError
		}

		w.WriteHeader(httpStatus)
		w.Header().Set("Server-Status", fmt.Sprintf("%s/%s", string(PIPELINE_POPULATE_POSTGRES), pipelineStatus))
		w.Header().Set("Content-Type", "text/plain")
		w.Header().Set("Retry-After", "60")
		w.Write([]byte("Service temporarily unavailable. Please try again shortly."))
	})
}

func GetRouter() *chi.Mux {
	r := chi.NewRouter()
	r.Use(RequestLogger)
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)
	r.Use(PreventRequestIfPipelineIsNotCompleted)

	// Set a timeout value on the request context (ctx), that will signal
	// through ctx.Done() that the request has timed out and further
	// processing should be stopped.
	r.Use(middleware.Timeout(60 * time.Second))

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// Student-facing explorer (explorer_api.go)
	mountExplorerRoutes(r)

	return r
}
