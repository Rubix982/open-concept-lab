package kv

import (
	"errors"
	"math/rand"
	"net"
	"net/rpc"
	"sync"
	"time"
)

// ErrUnknown means the client gave up without an answer: the operation may
// have taken effect, or may still. A checker must treat it as possibly applied.
var ErrUnknown = errors.New("kv: outcome unknown")

// Client talks to the cluster, finding the leader by hint and by trying. One
// Client issues one operation at a time, numbered so retries apply once.
type Client struct {
	addrs    []string
	id       int64
	seq      int64
	leader   int
	rpcLimit time.Duration
	giveUp   time.Duration

	mu    sync.Mutex
	conns map[int]*rpc.Client
}

func NewClient(addrs []string, id int64, rpcLimit, giveUp time.Duration) *Client {
	return &Client{addrs: addrs, id: id, rpcLimit: rpcLimit, giveUp: giveUp, conns: map[int]*rpc.Client{}}
}

// Get and Put return ErrUnknown when no server answered within giveUp.
func (c *Client) Get(key string) (string, error) {
	return c.do(Op{Kind: "get", Key: key})
}

func (c *Client) Put(key, value string) error {
	_, err := c.do(Op{Kind: "put", Key: key, Value: value})
	return err
}

func (c *Client) do(op Op) (string, error) {
	c.seq++
	op.ClientID, op.Seq = c.id, c.seq
	deadline := time.Now().Add(c.giveUp)
	for time.Now().Before(deadline) {
		var reply Reply
		err := c.call(c.leader, &Args{Op: op}, &reply)
		switch {
		case err == nil && reply.Err == "":
			return reply.Value, nil
		case err == nil && reply.Leader >= 0 && reply.Leader != c.leader:
			c.leader = reply.Leader
		default:
			c.leader = rand.Intn(len(c.addrs))
			time.Sleep(20 * time.Millisecond)
		}
	}

	return "", ErrUnknown
}

func (c *Client) call(server int, args *Args, reply *Reply) error {
	c.mu.Lock()
	conn := c.conns[server]
	c.mu.Unlock()
	if conn == nil {
		raw, err := net.DialTimeout("tcp", c.addrs[server], c.rpcLimit)
		if err != nil {
			return err
		}
		conn = rpc.NewClient(raw)
		c.mu.Lock()
		c.conns[server] = conn
		c.mu.Unlock()
	}
	call := conn.Go("KV.Do", args, reply, make(chan *rpc.Call, 1))
	select {
	case done := <-call.Done:
		if done.Error != nil {
			c.forget(server, conn)
		}
		return done.Error
	case <-time.After(c.rpcLimit):
		c.forget(server, conn)
		return ErrTimeout
	}
}

func (c *Client) forget(server int, conn *rpc.Client) {
	c.mu.Lock()
	if c.conns[server] == conn {
		delete(c.conns, server)
	}
	c.mu.Unlock()
	conn.Close()
}

// Close drops every connection.
func (c *Client) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	for s, conn := range c.conns {
		conn.Close()
		delete(c.conns, s)
	}
}
