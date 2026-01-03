package main

import (
	"fmt"
	"runtime"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/sirupsen/logrus"
)

var (
	heapInUse = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "scraper_heap_inuse_bytes",
	})
	gcDuration = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name: "scraper_gc_duration_seconds",
	})
)

type MemoryMonitor struct {
	logger         *logrus.Logger
	lastNumGC      uint32
	lastTotalAlloc uint64
	lastCheckTime  time.Time
}

func NewMemoryMonitor(logger *logrus.Logger) *MemoryMonitor {
	return &MemoryMonitor{
		logger:        logger,
		lastCheckTime: time.Now(),
	}
}

func (mm *MemoryMonitor) LogMemoryStats() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	now := time.Now()
	elapsed := now.Sub(mm.lastCheckTime).Seconds()

	// Calculate deltas
	allocRate := float64(m.TotalAlloc-mm.lastTotalAlloc) / elapsed / 1024 / 1024
	gcRate := float64(m.NumGC-mm.lastNumGC) / elapsed

	// Heap utilization
	heapInUse := float64(m.HeapInuse) / float64(m.HeapSys) * 100

	fields := logrus.Fields{
		"alloc_mb":         m.Alloc / 1024 / 1024,
		"heap_inuse_mb":    m.HeapInuse / 1024 / 1024,
		"heap_idle_mb":     m.HeapIdle / 1024 / 1024,
		"heap_released_mb": m.HeapReleased / 1024 / 1024,
		"heap_util_pct":    fmt.Sprintf("%.1f", heapInUse),
		"stack_mb":         m.StackInuse / 1024 / 1024,
		"sys_mb":           m.Sys / 1024 / 1024,
		"num_gc":           m.NumGC,
		"gc_rate_per_sec":  fmt.Sprintf("%.2f", gcRate),
		"alloc_rate_mb_s":  fmt.Sprintf("%.2f", allocRate),
		"goroutines":       runtime.NumGoroutine(),
	}

	// GC pause stats (last cycle)
	if m.NumGC > 0 {
		lastPauseNs := m.PauseNs[(m.NumGC+255)%256]
		fields["last_gc_pause_ms"] = float64(lastPauseNs) / 1e6
	}

	// Alert conditions
	if heapInUse > 90 {
		mm.logger.Warn("⚠️  High heap utilization")
	}
	if m.NumGC-mm.lastNumGC > 10 && elapsed < 10 {
		mm.logger.Warn("⚠️  Excessive GC activity")
	}

	mm.logger.WithFields(fields).Info("📊 Memory stats")

	// Update state
	mm.lastTotalAlloc = m.TotalAlloc
	mm.lastNumGC = m.NumGC
	mm.lastCheckTime = now
}

func init() {
	prometheus.MustRegister(heapInUse, gcDuration)
}
