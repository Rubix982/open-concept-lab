// Command node runs one raftkv server as its own process: Raft and the
// key-value store on one TCP port, state in one file under -data.
//
//	node -id 0 -listen 127.0.0.1:7000 -peers ,127.0.0.1:7101,127.0.0.1:7102 -data /tmp/n0
//
// -peers lists every node's address in ID order; this node's own entry is
// ignored (leave it empty). It prints "ready" once it is serving.
package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"net/rpc"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"raftkv/internal/kv"
	"raftkv/internal/raft"
)

func main() {
	id := flag.Int("id", 0, "this node's ID, from 0")
	listen := flag.String("listen", "127.0.0.1:0", "address to serve Raft and clients on")
	peers := flag.String("peers", "", "comma-separated addresses of all nodes, in ID order")
	data := flag.String("data", "", "folder for this node's state file")
	heartbeat := flag.Duration("heartbeat", 50*time.Millisecond, "leader heartbeat interval")
	flag.Parse()

	addrs := strings.Split(*peers, ",")
	if *id < 0 || *id >= len(addrs) || *data == "" {
		log.Fatal("node: need -id within -peers, and -data")
	}
	if err := os.MkdirAll(*data, 0o755); err != nil {
		log.Fatal(err)
	}
	l, err := net.Listen("tcp", *listen)
	if err != nil {
		log.Fatal(err)
	}

	apply := make(chan raft.ApplyMsg, 1024)
	transport := raft.NewTCPTransport(addrs, 4**heartbeat)
	node, err := raft.New(raft.Config{
		ID: *id, Peers: len(addrs), Transport: transport,
		Storage: raft.FileStorage{Path: filepath.Join(*data, "state")},
		Apply:   apply, Heartbeat: *heartbeat, Seed: time.Now().UnixNano(),
	})
	if err != nil {
		log.Fatal(err)
	}
	server := rpc.NewServer()
	if err := server.RegisterName("Raft", &raft.RPCService{Node: node}); err != nil {
		log.Fatal(err)
	}
	if err := server.RegisterName("KV", kv.NewServer(node, apply, time.Second)); err != nil {
		log.Fatal(err)
	}
	go server.Accept(l)
	fmt.Println("ready", l.Addr())

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, syscall.SIGINT)
	<-stop
	l.Close()
	node.Stop()
	transport.Close()
}
