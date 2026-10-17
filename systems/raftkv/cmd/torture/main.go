// Command torture runs a raftkv cluster as real processes on real sockets,
// injects faults while clients work, and checks what the clients saw.
//
//	go run ./cmd/torture -nodes 5 -clients 8 -duration 20s -seed 1
//
// Faults: a node killed with SIGKILL and restarted from its state file, and a
// network partition, cut in the TCP proxies every node-to-node link runs
// through. Exit status 0 means every key's history was linearizable and the
// cluster made progress; anything else is a failure, with the history kept.
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"

	"raftkv/internal/check"
	"raftkv/internal/faultnet"
	"raftkv/internal/kv"
)

func main() {
	nodes := flag.Int("nodes", 5, "cluster size")
	clients := flag.Int("clients", 8, "concurrent clients")
	duration := flag.Duration("duration", 20*time.Second, "how long clients run")
	seed := flag.Int64("seed", 1, "seed for operations and faults")
	keys := flag.Int("keys", 5, "distinct keys")
	minOps := flag.Int("min-ops", 200, "completed operations needed to count as progress")
	out := flag.String("out", "out", "folder for the history and the run's logs")
	flag.Parse()

	if err := run(*nodes, *clients, *keys, *minOps, *duration, *seed, *out); err != nil {
		fmt.Fprintln(os.Stderr, "torture:", err)
		os.Exit(1)
	}
}

// cluster is the processes, their ports and the links between them.
type cluster struct {
	bin, dir string
	addrs    []string
	mesh     *faultnet.Mesh
	logs     []*os.File

	mu    sync.Mutex
	procs []*exec.Cmd // nil while a node is down
}

func run(n, clients, keys, minOps int, duration time.Duration, seed int64, out string) error {
	runDir, err := os.MkdirTemp("", "raftkv-torture-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(runDir)
	if err := os.MkdirAll(out, 0o755); err != nil {
		return err
	}
	bin := filepath.Join(runDir, "node")
	if b, err := exec.Command("go", "build", "-o", bin, "./cmd/node").CombinedOutput(); err != nil {
		return fmt.Errorf("build node: %v\n%s", err, b)
	}

	c := &cluster{bin: bin, dir: runDir, procs: make([]*exec.Cmd, n)}
	for range n {
		addr, err := freePort()
		if err != nil {
			return err
		}
		c.addrs = append(c.addrs, addr)
	}
	if c.mesh, err = faultnet.NewMesh(c.addrs); err != nil {
		return err
	}
	defer c.mesh.Close()
	for i := range n {
		f, err := os.Create(filepath.Join(out, fmt.Sprintf("node-%d.log", i)))
		if err != nil {
			return err
		}
		defer f.Close()
		c.logs = append(c.logs, f)
		if err := c.start(i); err != nil {
			return err
		}
	}
	defer c.stopAll()

	fmt.Printf("cluster: %d node processes, %d proxied links, %d clients, %v, seed %d\n",
		n, n*(n-1), clients, duration, seed)

	start := time.Now()
	since := func() int64 { return time.Since(start).Nanoseconds() }
	var hmu sync.Mutex
	var history []check.Op
	record := func(op check.Op) {
		hmu.Lock()
		history = append(history, op)
		hmu.Unlock()
	}

	stopFaults := make(chan struct{})
	faults := make(chan string, 1024)
	var fwg sync.WaitGroup
	fwg.Add(1)
	go func() {
		defer fwg.Done()
		c.injectFaults(rand.New(rand.NewSource(seed)), stopFaults, faults)
	}()

	var cwg sync.WaitGroup
	end := start.Add(duration)
	for id := range clients {
		cwg.Add(1)
		go func(id int) {
			defer cwg.Done()
			rng := rand.New(rand.NewSource(seed*1000 + int64(id)))
			cl := kv.NewClient(c.addrs, int64(id+1), 300*time.Millisecond, 2*time.Second)
			defer cl.Close()
			for seq := 0; time.Now().Before(end); seq++ {
				key := fmt.Sprintf("k%d", rng.Intn(keys))
				op := check.Op{Client: id, Key: key, Call: since()}
				if rng.Intn(2) == 0 {
					op.Kind, op.Value = "put", fmt.Sprintf("c%d-%d", id, seq)
					err := cl.Put(key, op.Value)
					op.Return, op.Unknown = since(), err != nil
				} else {
					op.Kind = "get"
					v, err := cl.Get(key)
					if err != nil {
						continue // a read that never returned shows nothing; leave it out
					}
					op.Return, op.Value = since(), v
				}
				record(op)
			}
		}(id)
	}
	cwg.Wait()
	close(stopFaults)
	fwg.Wait()
	close(faults)

	var faultLog []string
	for f := range faults {
		faultLog = append(faultLog, f)
	}
	completed, unknown := 0, 0
	for _, op := range history {
		if op.Unknown {
			unknown++
		} else {
			completed++
		}
	}
	sort.Slice(history, func(i, j int) bool { return history[i].Call < history[j].Call })
	path := filepath.Join(out, fmt.Sprintf("history-seed%d.json", seed))
	if err := writeJSON(path, history); err != nil {
		return err
	}
	fmt.Printf("faults: %d (%s)\n", len(faultLog), summarize(faultLog))
	fmt.Printf("operations: %d completed, %d with unknown outcome; history in %s\n", completed, unknown, path)

	failed := false
	verdicts, err := check.ByKey(history)
	if err != nil {
		return err
	}
	for _, v := range verdicts {
		state := "linearizable"
		if !v.OK {
			state, failed = "NOT LINEARIZABLE: "+v.Why, true
		}
		fmt.Printf("  %-4s %5d ops  %s\n", v.Key, v.Ops, state)
	}
	if completed < minOps {
		return fmt.Errorf("no progress: %d completed operations, need %d", completed, minOps)
	}
	if failed {
		return fmt.Errorf("a history was not linearizable; see %s", path)
	}
	fmt.Println("PASS")

	return nil
}

// injectFaults alternates calm, crash-and-restart and partition-and-heal.
func (c *cluster) injectFaults(rng *rand.Rand, stop <-chan struct{}, log chan<- string) {
	n := len(c.addrs)
	sleep := func(min, max time.Duration) bool {
		select {
		case <-time.After(min + time.Duration(rng.Int63n(int64(max-min)))):
			return true
		case <-stop:
			return false
		}
	}
	for sleep(500*time.Millisecond, 1500*time.Millisecond) {
		switch rng.Intn(3) {
		case 0: // crash one node, restart it from disk
			victim := rng.Intn(n)
			c.kill(victim)
			log <- "crash"
			if !sleep(300*time.Millisecond, 2*time.Second) {
				c.start(victim)
				return
			}
			c.start(victim)
		case 1: // partition: a random side of 1 or 2 nodes
			perm := rng.Perm(n)
			side := perm[:1+rng.Intn(2)]
			c.mesh.Partition(side)
			log <- "partition"
			ok := sleep(500*time.Millisecond, 2500*time.Millisecond)
			c.mesh.HealAll()
			if !ok {
				return
			}
		case 2: // crash during a partition
			perm := rng.Perm(n)
			c.mesh.Partition(perm[:2])
			c.kill(perm[2])
			log <- "partition+crash"
			ok := sleep(500*time.Millisecond, 2*time.Second)
			c.mesh.HealAll()
			c.start(perm[2])
			if !ok {
				return
			}
		}
	}
}

func (c *cluster) start(i int) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.procs[i] != nil {
		return nil
	}
	peers := c.mesh.PeerAddrs(i)
	cmd := exec.Command(c.bin, "-id", fmt.Sprint(i), "-listen", c.addrs[i],
		"-peers", strings.Join(peers, ","), "-data", filepath.Join(c.dir, fmt.Sprintf("n%d", i)))
	cmd.Stderr = c.logs[i]
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return err
	}
	if err := cmd.Start(); err != nil {
		return err
	}
	ready := make(chan bool, 1)
	go func() {
		s := bufio.NewScanner(stdout)
		ok := s.Scan() && strings.HasPrefix(s.Text(), "ready")
		ready <- ok
		for s.Scan() {
		}
	}()
	select {
	case ok := <-ready:
		if !ok {
			return fmt.Errorf("node %d did not start", i)
		}
	case <-time.After(5 * time.Second):
		return fmt.Errorf("node %d did not become ready", i)
	}
	c.procs[i] = cmd

	return nil
}

func (c *cluster) kill(i int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if p := c.procs[i]; p != nil {
		p.Process.Signal(syscall.SIGKILL)
		p.Wait()
		c.procs[i] = nil
	}
}

func (c *cluster) stopAll() {
	for i := range c.procs {
		c.kill(i)
	}
}

func freePort() (string, error) {
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return "", err
	}
	defer l.Close()
	return l.Addr().String(), nil
}

func writeJSON(path string, v any) error {
	b, err := json.MarshalIndent(v, "", " ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0o644)
}

func summarize(events []string) string {
	counts := map[string]int{}
	for _, e := range events {
		counts[e]++
	}
	var parts []string
	for _, k := range []string{"crash", "partition", "partition+crash"} {
		if counts[k] > 0 {
			parts = append(parts, fmt.Sprintf("%d %s", counts[k], k))
		}
	}
	return strings.Join(parts, ", ")
}
