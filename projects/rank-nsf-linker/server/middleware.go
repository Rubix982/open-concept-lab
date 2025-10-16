package main

import (
	"net/http"
	"time"

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

func GetRouter() *chi.Mux {
	r := chi.NewRouter()
	r.Use(RequestLogger)
	r.Get("/universities", getAllUniversitiesWithCoordinates)

	return r
}
