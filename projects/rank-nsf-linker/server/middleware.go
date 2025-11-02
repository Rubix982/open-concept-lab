package main

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/middleware"
	"github.com/go-chi/chi/v5"
	"github.com/sirupsen/logrus"
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
	return logger.WithFields(logrus.Fields{
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
		LogRequest(r, r.RemoteAddr, ww.status, duration).Info("Handled request")
	})
}

func PreventRequestIfPipelineIsInProgress(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if isPipelineInProgress("populate_postgres") {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Header().Set("Retry-After", "60")
			w.Write([]byte("Service temporarily unavailable: Database population in progress. Please try again shortly."))
			return
		}
		next.ServeHTTP(w, r)
	})
}

func GetRouter() *chi.Mux {
	r := chi.NewRouter()
	r.Use(RequestLogger)
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)
	r.Use(PreventRequestIfPipelineIsInProgress)

	// Set a timeout value on the request context (ctx), that will signal
	// through ctx.Done() that the request has timed out and further
	// processing should be stopped.
	r.Use(middleware.Timeout(60 * time.Second))

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	r.Get("/universities/summary", getUniversitySummary)
	r.Get("/universities", getAllUniversitiesWithCoordinates)

	return r
}
