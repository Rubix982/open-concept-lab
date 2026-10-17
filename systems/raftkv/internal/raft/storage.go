package raft

import (
	"bytes"
	"encoding/gob"
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"sync"
)

// State is what Raft must not forget across a crash.
type State struct {
	Term     int
	VotedFor int
	Log      []Entry
}

// Storage keeps a node's State. Save returns only once the state is durable.
type Storage interface {
	Save(State) error
	Load() (State, bool, error)
}

// FileStorage keeps State in one file, replaced atomically: written to a
// temporary file, fsynced, renamed over the old one, and the folder fsynced.
// A crash at any point leaves either the old state or the new one.
type FileStorage struct{ Path string }

func (f FileStorage) Save(s State) error {
	var buf bytes.Buffer
	if err := gob.NewEncoder(&buf).Encode(s); err != nil {
		return err
	}
	tmp := f.Path + ".tmp"
	file, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	if _, err := file.Write(buf.Bytes()); err != nil {
		file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(tmp, f.Path); err != nil {
		return err
	}
	dir, err := os.Open(filepath.Dir(f.Path))
	if err != nil {
		return err
	}
	defer dir.Close()

	return dir.Sync()
}

func (f FileStorage) Load() (State, bool, error) {
	data, err := os.ReadFile(f.Path)
	if errors.Is(err, fs.ErrNotExist) {
		return State{}, false, nil
	}
	if err != nil {
		return State{}, false, err
	}
	var s State
	if err := gob.NewDecoder(bytes.NewReader(data)).Decode(&s); err != nil {
		return State{}, false, err
	}

	return s, true, nil
}

// MemStorage keeps State in memory: for tests, where a "restart" is a new Node
// given the same MemStorage.
type MemStorage struct {
	mu    sync.Mutex
	state *State
}

func (m *MemStorage) Save(s State) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	copied := State{Term: s.Term, VotedFor: s.VotedFor, Log: append([]Entry(nil), s.Log...)}
	m.state = &copied

	return nil
}

func (m *MemStorage) Load() (State, bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.state == nil {
		return State{}, false, nil
	}

	return State{Term: m.state.Term, VotedFor: m.state.VotedFor, Log: append([]Entry(nil), m.state.Log...)}, true, nil
}
