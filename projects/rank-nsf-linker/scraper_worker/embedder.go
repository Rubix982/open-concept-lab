package scraperworker

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"sync"
)

type Embedder struct {
	cmd    *exec.Cmd
	stdin  io.WriteCloser
	stdout *bufio.Scanner
	mutex  sync.Mutex
}

func NewEmbedder() (*Embedder, error) {
	cmd := exec.Command("python3", getEmbedderFilePath())

	// Create pipes
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("failed to get stdin pipe: %w", err)
	}

	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("failed to get stdout pipe: %w", err)
	}

	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("failed to start embedder process: %w", err)
	}

	return &Embedder{
		cmd:    cmd,
		stdin:  stdin,
		stdout: bufio.NewScanner(stdoutPipe),
	}, nil
}

func (e *Embedder) Embed(text string) ([]float32, error) {
	e.mutex.Lock()
	defer e.mutex.Unlock()

	// Prepare payload
	payload := map[string]string{"text": text}
	data, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	// Write to python process
	_, err = fmt.Fprintln(e.stdin, string(data))
	if err != nil {
		return nil, fmt.Errorf("failed to write to embedder: %w", err)
	}

	// Read response
	if !e.stdout.Scan() {
		return nil, fmt.Errorf("embedder process closed unexpectedly")
	}

	respBytes := e.stdout.Bytes()
	var vector []float32
	if err := json.Unmarshal(respBytes, &vector); err != nil {
		return nil, fmt.Errorf("failed to unmarshal vector: %w, data: %s", err, string(respBytes))
	}

	return vector, nil
}

func (e *Embedder) Close() error {
	e.stdin.Close()
	return e.cmd.Wait()
}
