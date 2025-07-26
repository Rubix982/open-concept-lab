package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"

	"github.com/sirupsen/logrus"
)

var (
	logger *logrus.Logger
	once   sync.Once
)

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
	})
}
