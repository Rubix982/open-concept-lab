# Go Concurrency & Synchronization - Complete Guide

## Overview of Go Concurrency Primitives

Go provides several powerful concurrency mechanisms:

1. **Goroutines** - Lightweight threads managed by Go runtime
2. **Channels** - Communication mechanism between goroutines  
3. **Mutexes** - Mutual exclusion locks (`sync.Mutex`)
4. **RWMutex** - Reader-writer locks (`sync.RWMutex`)
5. **WaitGroups** - Synchronization for multiple goroutines (`sync.WaitGroup`)
6. **Once** - Execute code exactly once (`sync.Once`)
7. **Atomic Operations** - Lock-free operations (`sync/atomic`)
8. **Condition Variables** - Conditional waiting (`sync.Cond`)
9. **Context** - Cancellation and timeout handling (`context`)

---

## 1. Goroutines - Lightweight Concurrency

### **What are Goroutines?**

- Managed by Go runtime (not OS threads)
- ~2KB initial stack size (vs 2MB for OS threads)
- Multiplexed onto OS threads by Go scheduler
- Communicating Sequential Processes (CSP) model

### **Basic Usage:**

```go
package main

import (
    "fmt"
    "time"
)

func sayHello(name string) {
    for i := 0; i < 5; i++ {
        fmt.Printf("Hello %s - %d\n", name, i)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    // Sequential execution
    sayHello("Sequential")
    
    // Concurrent execution
    go sayHello("Goroutine-1")
    go sayHello("Goroutine-2")
    
    // Wait for goroutines (naive approach)
    time.Sleep(1 * time.Second)
}
```

### **Goroutine Lifecycle:**

```go
func goroutineLifecycle() {
    // Anonymous goroutine
    go func() {
        fmt.Println("Anonymous goroutine executed")
    }()
    
    // Goroutine with parameters
    message := "Hello from closure"
    go func(msg string) {
        fmt.Println(msg)
    }(message)
    
    // Goroutine returning values (via channels)
    resultChan := make(chan int)
    go func() {
        result := heavyComputation()
        resultChan <- result
    }()
    
    result := <-resultChan
    fmt.Printf("Result: %d\n", result)
}
```

---

## 2. Channels - Communication Mechanism

### **Channel Types:**

```go
// Unbuffered channel (synchronous)
ch := make(chan int)

// Buffered channel (asynchronous)
buffered := make(chan int, 10)

// Receive-only channel
var recvOnly <-chan int = ch

// Send-only channel  
var sendOnly chan<- int = ch

// Channel of channels
metaChan := make(chan chan int)
```

### **Channel Operations:**

```go
func channelOperations() {
    ch := make(chan int, 3)
    
    // Send operations
    ch <- 1
    ch <- 2
    ch <- 3
    
    // Receive operations
    val1 := <-ch                    // Blocking receive
    val2, ok := <-ch               // Non-blocking with status
    
    // Select statement (non-blocking)
    select {
    case val := <-ch:
        fmt.Printf("Received: %d\n", val)
    case <-time.After(1 * time.Second):
        fmt.Println("Timeout!")
    default:
        fmt.Println("No value available")
    }
    
    // Close channel
    close(ch)
    
    // Range over channel
    for val := range ch {
        fmt.Printf("Value: %d\n", val)
    }
}
```

### **Producer-Consumer Pattern:**

```go
func producerConsumer() {
    jobs := make(chan int, 100)
    results := make(chan int, 100)
    
    // Start workers
    numWorkers := 3
    for w := 1; w <= numWorkers; w++ {
        go worker(w, jobs, results)
    }
    
    // Send jobs
    numJobs := 9
    for j := 1; j <= numJobs; j++ {
        jobs <- j
    }
    close(jobs)
    
    // Collect results
    for r := 1; r <= numJobs; r++ {
        <-results
    }
}

func worker(id int, jobs <-chan int, results chan<- int) {
    for job := range jobs {
        fmt.Printf("Worker %d processing job %d\n", id, job)
        time.Sleep(time.Second) // Simulate work
        results <- job * 2
    }
}
```

---

## 3. sync.Mutex - Mutual Exclusion

### **Basic Mutex Usage:**

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Counter struct {
    mu    sync.Mutex
    value int
}

func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

func (c *Counter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}

func main() {
    counter := &Counter{}
    
    // Start 1000 goroutines incrementing counter
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }
    
    wg.Wait()
    fmt.Printf("Final counter value: %d\n", counter.Value())
}
```

### **Common Mutex Patterns:**

#### **Protecting Shared State:**

```go
type SafeMap struct {
    mu sync.Mutex
    m  map[string]int
}

func NewSafeMap() *SafeMap {
    return &SafeMap{
        m: make(map[string]int),
    }
}

func (sm *SafeMap) Set(key string, value int) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    sm.m[key] = value
}

func (sm *SafeMap) Get(key string) (int, bool) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    val, ok := sm.m[key]
    return val, ok
}

func (sm *SafeMap) Delete(key string) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    delete(sm.m, key)
}
```

#### **Lazy Initialization:**

```go
type LazyResource struct {
    mu       sync.Mutex
    resource *ExpensiveResource
}

func (lr *LazyResource) Get() *ExpensiveResource {
    lr.mu.Lock()
    defer lr.mu.Unlock()
    
    if lr.resource == nil {
        lr.resource = NewExpensiveResource()
    }
    return lr.resource
}
```

---

## 4. sync.RWMutex - Reader-Writer Locks

### **When to Use RWMutex:**

- Multiple concurrent readers are safe
- Only one writer allowed at a time
- Readers block writers, writers block everyone
- Better performance for read-heavy workloads

### **RWMutex Example:**

```go
type ReadWriteCounter struct {
    mu    sync.RWMutex
    value int
}

func (rwc *ReadWriteCounter) Increment() {
    rwc.mu.Lock()         // Exclusive lock for writing
    defer rwc.mu.Unlock()
    rwc.value++
}

func (rwc *ReadWriteCounter) Value() int {
    rwc.mu.RLock()        // Shared lock for reading
    defer rwc.mu.RUnlock()
    return rwc.value
}

// Benchmark read-heavy workload
func benchmarkRWMutex() {
    counter := &ReadWriteCounter{}
    
    // Start many readers
    for i := 0; i < 100; i++ {
        go func() {
            for j := 0; j < 10000; j++ {
                _ = counter.Value() // Many concurrent reads
            }
        }()
    }
    
    // Start few writers
    for i := 0; i < 5; i++ {
        go func() {
            for j := 0; j < 100; j++ {
                counter.Increment() // Few concurrent writes
                time.Sleep(time.Millisecond)
            }
        }()
    }
}
```

### **Performance Comparison:**

```go
// Mutex vs RWMutex benchmark
func BenchmarkMutex(b *testing.B) {
    var mu sync.Mutex
    var data int
    
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            mu.Lock()
            _ = data // Read operation
            mu.Unlock()
        }
    })
}

func BenchmarkRWMutex(b *testing.B) {
    var mu sync.RWMutex
    var data int
    
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            mu.RLock()
            _ = data // Read operation
            mu.RUnlock()
        }
    })
}
```

---

## 5. sync.WaitGroup - Goroutine Synchronization

### **Basic WaitGroup Pattern:**

```go
func waitGroupExample() {
    var wg sync.WaitGroup
    
    urls := []string{
        "https://golang.org",
        "https://github.com",
        "https://stackoverflow.com",
    }
    
    for _, url := range urls {
        wg.Add(1) // Increment counter
        
        go func(u string) {
            defer wg.Done() // Decrement counter when done
            fetchURL(u)
        }(url)
    }
    
    wg.Wait() // Wait for all goroutines to complete
    fmt.Println("All URLs fetched")
}

func fetchURL(url string) {
    resp, err := http.Get(url)
    if err != nil {
        fmt.Printf("Error fetching %s: %v\n", url, err)
        return
    }
    defer resp.Body.Close()
    fmt.Printf("Fetched %s: %s\n", url, resp.Status)
}
```

### **Worker Pool with WaitGroup:**

```go
func workerPool() {
    const numWorkers = 3
    const numJobs = 10
    
    jobs := make(chan int, numJobs)
    var wg sync.WaitGroup
    
    // Start workers
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, &wg)
    }
    
    // Send jobs
    for j := 1; j <= numJobs; j++ {
        jobs <- j
    }
    close(jobs)
    
    wg.Wait() // Wait for all workers to finish
}

func worker(id int, jobs <-chan int, wg *sync.WaitGroup) {
    defer wg.Done()
    for job := range jobs {
        fmt.Printf("Worker %d processing job %d\n", id, job)
        time.Sleep(time.Second)
    }
}
```

---

## 6. sync.Once - Execute Exactly Once

### **Singleton Pattern:**

```go
type Singleton struct {
    data string
}

var (
    instance *Singleton
    once     sync.Once
)

func GetSingleton() *Singleton {
    once.Do(func() {
        instance = &Singleton{data: "singleton data"}
        fmt.Println("Singleton created")
    })
    return instance
}

// Safe for concurrent access
func testSingleton() {
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            s := GetSingleton()
            fmt.Printf("Got singleton: %p\n", s)
        }()
    }
    
    wg.Wait()
}
```

### **Expensive Initialization:**

```go
type Database struct {
    connection *sql.DB
    once       sync.Once
}

func (db *Database) Connect() error {
    var err error
    db.once.Do(func() {
        db.connection, err = sql.Open("postgres", "connection_string")
        if err == nil {
            fmt.Println("Database connected")
        }
    })
    return err
}
```

---

## 7. sync/atomic - Lock-Free Operations

### **Atomic Operations:**

```go
import (
    "sync/atomic"
    "unsafe"
)

// Atomic integers
func atomicIntegers() {
    var counter int64
    
    // Atomic increment
    atomic.AddInt64(&counter, 1)
    
    // Atomic load
    value := atomic.LoadInt64(&counter)
    
    // Atomic store  
    atomic.StoreInt64(&counter, 100)
    
    // Compare and swap
    swapped := atomic.CompareAndSwapInt64(&counter, 100, 200)
    fmt.Printf("Swapped: %t\n", swapped)
}

// Atomic pointers
type Node struct {
    data int
    next *Node
}

func atomicPointers() {
    var head unsafe.Pointer
    
    // Atomic store
    newNode := &Node{data: 42}
    atomic.StorePointer(&head, unsafe.Pointer(newNode))
    
    // Atomic load
    currentHead := (*Node)(atomic.LoadPointer(&head))
    
    // Compare and swap
    anotherNode := &Node{data: 84}
    swapped := atomic.CompareAndSwapPointer(
        &head,
        unsafe.Pointer(currentHead),
        unsafe.Pointer(anotherNode),
    )
    fmt.Printf("Head swapped: %t\n", swapped)
}
```

### **Lock-Free Counter:**

```go
type AtomicCounter struct {
    value int64
}

func (ac *AtomicCounter) Increment() {
    atomic.AddInt64(&ac.value, 1)
}

func (ac *AtomicCounter) Decrement() {
    atomic.AddInt64(&ac.value, -1)
}

func (ac *AtomicCounter) Value() int64 {
    return atomic.LoadInt64(&ac.value)
}

// Benchmark: Atomic vs Mutex
func BenchmarkAtomicCounter(b *testing.B) {
    counter := &AtomicCounter{}
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            counter.Increment()
        }
    })
}
```

---

## 8. sync.Cond - Condition Variables

### **Producer-Consumer with Cond:**

```go
type Queue struct {
    mu    sync.Mutex
    cond  *sync.Cond
    items []int
}

func NewQueue() *Queue {
    q := &Queue{
        items: make([]int, 0),
    }
    q.cond = sync.NewCond(&q.mu)
    return q
}

func (q *Queue) Enqueue(item int) {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    q.items = append(q.items, item)
    q.cond.Signal() // Wake up one waiting consumer
}

func (q *Queue) Dequeue() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    for len(q.items) == 0 {
        q.cond.Wait() // Wait for items to be available
    }
    
    item := q.items[0]
    q.items = q.items[1:]
    return item
}

func (q *Queue) DequeueAll() []int {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    for len(q.items) == 0 {
        q.cond.Wait()
    }
    
    items := make([]int, len(q.items))
    copy(items, q.items)
    q.items = q.items[:0]
    return items
}
```

---

## 9. Context - Cancellation and Timeouts

### **Basic Context Usage:**

```go
import (
    "context"
    "fmt"
    "time"
)

func contextBasics() {
    // Background context
    ctx := context.Background()
    
    // Context with timeout
    ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
    defer cancel()
    
    // Context with cancellation
    ctx, cancel = context.WithCancel(ctx)
    defer cancel()
    
    // Context with deadline
    deadline := time.Now().Add(5 * time.Second)
    ctx, cancel = context.WithDeadline(ctx, deadline)
    defer cancel()
    
    // Context with value
    ctx = context.WithValue(ctx, "userID", 12345)
}
```

### **HTTP Request with Context:**

```go
func httpWithContext(ctx context.Context, url string) error {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return err
    }
    
    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    // Process response
    return nil
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    err := httpWithContext(ctx, "https://httpbin.org/delay/3")
    if err != nil {
        fmt.Printf("Request failed: %v\n", err)
    }
}
```

### **Goroutine Cancellation:**

```go
func cancellableWorker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d cancelled: %v\n", id, ctx.Err())
            return
        default:
            // Do work
            fmt.Printf("Worker %d working...\n", id)
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func contextCancellation() {
    ctx, cancel := context.WithCancel(context.Background())
    
    // Start workers
    for i := 1; i <= 3; i++ {
        go cancellableWorker(ctx, i)
    }
    
    // Let them work for a while
    time.Sleep(3 * time.Second)
    
    // Cancel all workers
    cancel()
    time.Sleep(1 * time.Second)
}
```

---

## 10. Advanced Concurrency Patterns

### **Fan-Out/Fan-In Pattern:**

```go
func fanOutFanIn() {
    input := make(chan int)
    
    // Fan-out: distribute work to multiple workers
    numWorkers := 3
    workers := make([]<-chan int, numWorkers)
    
    for i := 0; i < numWorkers; i++ {
        worker := make(chan int)
        workers[i] = worker
        
        go func(in <-chan int, out chan<- int) {
            defer close(out)
            for n := range in {
                out <- n * n // Square the number
            }
        }(input, worker)
    }
    
    // Fan-in: collect results from all workers
    output := fanIn(workers...)
    
    // Send input
    go func() {
        defer close(input)
        for i := 1; i <= 10; i++ {
            input <- i
        }
    }()
    
    // Collect results
    for result := range output {
        fmt.Printf("Result: %d\n", result)
    }
}

func fanIn(inputs ...<-chan int) <-chan int {
    output := make(chan int)
    var wg sync.WaitGroup
    
    for _, input := range inputs {
        wg.Add(1)
        go func(in <-chan int) {
            defer wg.Done()
            for value := range in {
                output <- value
            }
        }(input)
    }
    
    go func() {
        wg.Wait()
        close(output)
    }()
    
    return output
}
```

### **Pipeline Pattern:**

```go
func pipeline() {
    // Stage 1: Generate numbers
    numbers := generate(1, 2, 3, 4, 5)
    
    // Stage 2: Square numbers
    squares := square(numbers)
    
    // Stage 3: Filter even squares
    evens := filterEven(squares)
    
    // Consume results
    for result := range evens {
        fmt.Printf("Result: %d\n", result)
    }
}

func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

func filterEven(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            if n%2 == 0 {
                out <- n
            }
        }
    }()
    return out
}
```

### **Worker Pool with Rate Limiting:**

```go
import "golang.org/x/time/rate"

func rateLimitedWorkerPool() {
    // Rate limiter: 10 requests per second
    limiter := rate.NewLimiter(rate.Limit(10), 1)
    
    jobs := make(chan Job, 100)
    results := make(chan Result, 100)
    
    // Start workers
    numWorkers := 5
    var wg sync.WaitGroup
    
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go rateLimitedWorker(limiter, jobs, results, &wg)
    }
    
    // Send jobs
    go func() {
        defer close(jobs)
        for i := 0; i < 50; i++ {
            jobs <- Job{ID: i, Data: fmt.Sprintf("job-%d", i)}
        }
    }()
    
    // Close results channel when all workers are done
    go func() {
        wg.Wait()
        close(results)
    }()
    
    // Collect results
    for result := range results {
        fmt.Printf("Processed job %d\n", result.JobID)
    }
}

func rateLimitedWorker(limiter *rate.Limiter, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
    defer wg.Done()
    
    for job := range jobs {
        // Wait for rate limiter
        limiter.Wait(context.Background())
        
        // Process job
        result := processJob(job)
        results <- result
    }
}
```

---

## 11. Common Concurrency Anti-Patterns

### **Race Conditions:**

```go
// BAD: Race condition
var counter int

func badIncrement() {
    for i := 0; i < 1000; i++ {
        go func() {
            counter++ // Race condition!
        }()
    }
}

// GOOD: Proper synchronization
var (
    counter int
    mu      sync.Mutex
)

func goodIncrement() {
    for i := 0; i < 1000; i++ {
        go func() {
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }
}
```

### **Deadlocks:**

```go
// BAD: Potential deadlock
func deadlockExample() {
    var mu1, mu2 sync.Mutex
    
    go func() {
        mu1.Lock()
        time.Sleep(100 * time.Millisecond)
        mu2.Lock() // Potential deadlock
        mu2.Unlock()
        mu1.Unlock()
    }()
    
    go func() {
        mu2.Lock()
        time.Sleep(100 * time.Millisecond)
        mu1.Lock() // Potential deadlock
        mu1.Unlock()
        mu2.Unlock()
    }()
}

// GOOD: Consistent lock ordering
func avoidDeadlock() {
    var mu1, mu2 sync.Mutex
    
    lockInOrder := func(m1, m2 *sync.Mutex) {
        m1.Lock()
        m2.Lock()
        defer m2.Unlock()
        defer m1.Unlock()
        // Do work
    }
    
    go lockInOrder(&mu1, &mu2)
    go lockInOrder(&mu1, &mu2) // Same order
}
```

### **Goroutine Leaks:**

```go
// BAD: Goroutine leak
func goroutineLeak() {
    ch := make(chan int)
    
    go func() {
        val := <-ch // Blocks forever if no sender
        fmt.Println(val)
    }()
    
    // Channel never receives value - goroutine leaks
}

// GOOD: Use context for cancellation
func noGoroutineLeak() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    ch := make(chan int)
    
    go func() {
        select {
        case val := <-ch:
            fmt.Println(val)
        case <-ctx.Done():
            fmt.Println("Timeout or cancellation")
        }
    }()
}
```

---

## 12. Performance Best Practices

### **Choosing the Right Synchronization:**

```go
// Mutex vs Channel decision matrix:

// Use Mutex when:
// - Protecting shared state
// - Short critical sections
// - Multiple readers/writers

type MutexCounter struct {
    mu    sync.Mutex
    value int
}

func (m *MutexCounter) Increment() {
    m.mu.Lock()
    m.value++ // Short critical section
    m.mu.Unlock()
}

// Use Channels when:
// - Communication between goroutines
// - Data flow/pipeline patterns
// - Signaling events

func channelCounter() {
    counter := 0
    ch := make(chan struct{})
    
    go func() {
        for range ch {
            counter++ // Only one goroutine modifies
        }
    }()
    
    // Multiple goroutines can send
    for i := 0; i < 100; i++ {
        ch <- struct{}{}
    }
}
```

### **Memory Model Considerations:**

```go
// Go memory model guarantees:
// 1. Within a single goroutine, reads and writes appear in program order
// 2. Synchronization operations create happens-before relationships

var a, b int

func memoryModel() {
    // Goroutine 1
    go func() {
        a = 1  // Write 1
        b = 2  // Write 2
    }()
    
    // Goroutine 2
    go func() {
        if b == 2 {    // Read 2
            fmt.Println(a) // May print 0 or 1!
        }
    }()
}

// Use synchronization to establish happens-before:
func synchronizedMemoryModel() {
    var mu sync.Mutex
    
    go func() {
        mu.Lock()
        a = 1
        b = 2
        mu.Unlock()
    }()
    
    go func() {
        mu.Lock()
        if b == 2 {
            fmt.Println(a) // Guaranteed to print 1
        }
        mu.Unlock()
    }()
}
```

---

## 13. Testing Concurrent Code

### **Race Detection:**

```bash
# Run with race detector
go run -race main.go
go test -race ./...
```

### **Testing with Goroutines:**

```go
func TestConcurrentCounter(t *testing.T) {
    counter := &SafeCounter{}
    numGoroutines := 100
    numIncrements := 1000
    
    var wg sync.WaitGroup
    
    for i := 0; i < numGoroutines; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < numIncrements; j++ {
                counter.Increment()
            }
        }()
    }
    
    wg.Wait()
    
    expected := numGoroutines * numIncrements
    if counter.Value() != expected {
        t.Errorf("Expected %d, got %d", expected, counter.Value())
    }
}
```

### **Timeout Testing:**

```go
func TestWithTimeout(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    done := make(chan struct{})
    
    go func() {
        defer close(done)
        // Long-running operation
        time.Sleep(2 * time.Second)
    }()
    
    select {
    case <-done:
        t.Error("Operation should have timed out")
    case <-ctx.Done():
        // Expected timeout
    }
}
```

---

## 14. Interview Questions

### **Common Concurrency Questions:**

1. **"Explain the difference between goroutines and OS threads."**
   - Goroutines: lightweight, managed by Go runtime, multiplexed onto OS threads
   - OS threads: heavy, managed by kernel, 1:1 mapping to kernel threads

2. **"When would you use a buffered vs unbuffered channel?"**
   - Unbuffered: Synchronous communication, sender blocks until receiver ready
   - Buffered: Asynchronous communication up to buffer size, decouples sender/receiver

3. **"How do you detect and prevent race conditions?"**
   - Detection: `-race` flag, static analysis tools
   - Prevention: Mutexes, channels, atomic operations

4. **"Design a thread-safe cache with TTL."**

```go
type CacheItem struct {
    value  interface{}
    expiry time.Time
}

type TTLCache struct {
    mu    sync.RWMutex
    items map[string]*CacheItem
    ttl   time.Duration
}

func (c *TTLCache) Set(key string, value interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = &CacheItem{
        value:  value,
        expiry: time.Now().Add(c.ttl),
    }
}

func (c *TTLCache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, exists := c.items[key]
    if !exists || time.Now().After(item.expiry) {
        return nil, false
    }
    return item.value, true
}
```

---

## 15. Real-World Patterns

### **Circuit Breaker:**

```go
type CircuitBreaker struct {
    mu          sync.RWMutex
    state       State
    failures    int
    maxFailures int
    timeout     time.Duration
    lastFailure time.Time
}

type State int

const (
    Closed State = iota
    Open
    HalfOpen
)

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.RLock()
    state := cb.state
    failures := cb.failures
    cb.mu.RUnlock()
    
    if state == Open {
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.mu.Lock()
            cb.state = HalfOpen
            cb.mu.Unlock()
        } else {
            return errors.New("circuit breaker is open")
        }
    }
    
    err := fn()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = Open
        }
    } else {
        cb.failures = 0
        cb.state = Closed
    }
    
    return err
}
```

### **Connection Pool:**

```go
type ConnectionPool struct {
    mu    sync.Mutex
    conns chan *Connection
    
    factory    func() (*Connection, error)
    maxSize    int
    currentSize int
}

func NewConnectionPool(factory func() (*Connection, error), maxSize int) *ConnectionPool {
    return &ConnectionPool{
        conns:   make(chan *Connection, maxSize),
        factory: factory,
        maxSize: maxSize,
    }
}

func (p *ConnectionPool) Get() (*Connection, error) {
    select {
    case conn := <-p.conns:
        return conn, nil
    default:
        p.mu.Lock()
        defer p.mu.Unlock()
        
        if p.currentSize < p.maxSize {
            conn, err := p.factory()
            if err == nil {
                p.currentSize++
            }
            return conn, err
        }
        
        // Block until connection available
        return <-p.conns, nil
    }
}

func (p *ConnectionPool) Put(conn *Connection) {
    select {
    case p.conns <- conn:
    default:
        // Pool is full, close connection
        conn.Close()
        p.mu.Lock()
        p.currentSize--
        p.mu.Unlock()
    }
}
```

---

*This comprehensive guide covers Go's concurrency primitives and patterns. Understanding these concepts is essential for writing efficient, safe concurrent programs in Go.*
