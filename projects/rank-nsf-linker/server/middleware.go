package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/middleware"
	"github.com/go-chi/chi/v5"
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
		LogRequest(r, r.RemoteAddr, ww.status, duration).Debug("Handled request")
	})
}

func PreventRequestIfPipelineIsNotCompleted(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		pipelineStatus := GetPipelineStatus(cast.ToString(PIPELINE_POPULATE_POSTGRES))
		if pipelineStatus == cast.ToString(PIPELINE_STATUS_COMPLETED) {
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

	r.Post("/universities/summary", getUniversitySummary)
	r.Get("/universities", getAllUniversitiesWithCoordinates)
	r.Get("/universities/top", getTopUniversitiesSummary)
	r.Get("/universities/top-funded", getTopFundedUniversities)
	r.Get("/universities/most-awards", getMostAwardsUniversities)

	// Professor endpoints
	r.Get("/professors/by-university", getProfessorsByUniversity)

	// Stats endpoints
	r.Get("/stats/university-count", getUniversityCount)
	r.Get("/stats/professor-count", getProfessorCount)
	r.Get("/stats/award-count", getAwardCount)
	r.Get("/stats/funding-total", getTotalFunding)
	r.Get("/stats/avg-funding-per-award", getAvgFundingPerAward)

	// Filter/Metadata endpoints
	r.Get("/filters/available-areas", getAvailableAreas)
	r.Get("/filters/available-universities", getAvailableUniversities)
	r.Get("/filters/available-years", getAvailableYears)

	// Search API
	r.Post("/search/faculty", searchFacultyByResearch)

	return r
}
