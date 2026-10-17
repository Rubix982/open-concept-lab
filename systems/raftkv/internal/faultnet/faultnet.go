// Package faultnet puts a TCP proxy on each one-way link between nodes, so a
// test can cut and heal the real network between real processes. A cut link
// closes its open connections and refuses new ones, the way a partition looks
// to a process: connections reset, dials fail.
package faultnet

import (
	"io"
	"net"
	"sync"
)

// Link forwards connections from its own address to Target while up.
type Link struct {
	Target string

	listener net.Listener
	mu       sync.Mutex
	isCut    bool
	conns    map[net.Conn]struct{}
	closed   bool
}

// Listen opens a link on a free local port.
func Listen(target string) (*Link, error) {
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	link := &Link{Target: target, listener: l, conns: map[net.Conn]struct{}{}}
	go link.accept()

	return link, nil
}

// Addr is where a node dials to reach Target through this link.
func (l *Link) Addr() string { return l.listener.Addr().String() }

// Cut drops every open connection and refuses new ones until Heal.
func (l *Link) Cut() {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.isCut = true
	for c := range l.conns {
		c.Close()
		delete(l.conns, c)
	}
}

func (l *Link) Heal() {
	l.mu.Lock()
	l.isCut = false
	l.mu.Unlock()
}

func (l *Link) IsCut() bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.isCut
}

// Close stops the link for good.
func (l *Link) Close() {
	l.mu.Lock()
	l.closed = true
	l.mu.Unlock()
	l.listener.Close()
	l.Cut()
}

// track registers both halves of a forwarded connection, unless the link is
// cut, in which case it closes them and answers false.
func (l *Link) track(cs ...net.Conn) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.isCut || l.closed {
		for _, c := range cs {
			c.Close()
		}
		return false
	}
	for _, c := range cs {
		l.conns[c] = struct{}{}
	}
	return true
}

func (l *Link) untrack(cs ...net.Conn) {
	l.mu.Lock()
	defer l.mu.Unlock()
	for _, c := range cs {
		delete(l.conns, c)
	}
}

func (l *Link) accept() {
	for {
		in, err := l.listener.Accept()
		if err != nil {
			return
		}
		go l.forward(in)
	}
}

func (l *Link) forward(in net.Conn) {
	if l.IsCut() {
		in.Close()
		return
	}
	out, err := net.Dial("tcp", l.Target)
	if err != nil {
		in.Close()
		return
	}
	if !l.track(in, out) {
		return
	}
	var wg sync.WaitGroup
	pipe := func(dst, src net.Conn) {
		defer wg.Done()
		io.Copy(dst, src)
		// Either side ending ends both: a half-open link would hide a cut.
		dst.Close()
		src.Close()
	}
	wg.Add(2)
	go pipe(out, in)
	go pipe(in, out)
	wg.Wait()
	l.untrack(in, out)
}

// Mesh is the full set of one-way links among n nodes: Link(i, j) carries
// node i's connections to node j.
type Mesh struct {
	links [][]*Link
}

// NewMesh builds links to the given node addresses.
func NewMesh(nodeAddrs []string) (*Mesh, error) {
	n := len(nodeAddrs)
	m := &Mesh{links: make([][]*Link, n)}
	for i := range n {
		m.links[i] = make([]*Link, n)
		for j := range n {
			if i == j {
				continue
			}
			link, err := Listen(nodeAddrs[j])
			if err != nil {
				m.Close()
				return nil, err
			}
			m.links[i][j] = link
		}
	}
	return m, nil
}

// PeerAddrs is what node i is told its peers' addresses are: its own links.
// Its own entry is empty; a node never dials itself.
func (m *Mesh) PeerAddrs(i int) []string {
	out := make([]string, len(m.links))
	for j, link := range m.links[i] {
		if link != nil {
			out[j] = link.Addr()
		}
	}
	return out
}

// Partition cuts every link between the two sides, both ways, and heals the
// rest. A node in neither side is left connected to everyone.
func (m *Mesh) Partition(side []int) {
	in := map[int]bool{}
	for _, s := range side {
		in[s] = true
	}
	for i, row := range m.links {
		for j, link := range row {
			if link == nil {
				continue
			}
			if in[i] != in[j] {
				link.Cut()
			} else {
				link.Heal()
			}
		}
	}
}

// HealAll restores every link.
func (m *Mesh) HealAll() { m.Partition(nil) }

func (m *Mesh) Close() {
	for _, row := range m.links {
		for _, link := range row {
			if link != nil {
				link.Close()
			}
		}
	}
}
