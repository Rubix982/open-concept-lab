# Database Locking & Parallelism Interview Questions

## **1. Lock Types & Granularity**

### Basic Questions

- **Shared vs Exclusive locks** - when does each apply and why?
- **Row-level vs page-level vs table-level locking** - performance tradeoffs?
- **Intent locks** - how do they optimize lock acquisition in hierarchical systems?
- **Gap locks** in InnoDB - how do they prevent phantom reads?
- **Next-key locks** - combination of record + gap locks, when used?

### Advanced Scenarios

- Design a custom lock manager for a distributed database
- How would you implement fair queuing for lock requests?
- Explain lock escalation - when does MySQL/PostgreSQL escalate locks?
- How do you handle lock timeouts vs deadlock detection?

## **2. Deadlock Scenarios**

### Classic Deadlock Example

```sql
-- Transaction A
BEGIN;
UPDATE users SET name='Alice' WHERE id=1;
UPDATE orders SET status='pending' WHERE user_id=2;

-- Transaction B  
BEGIN;
UPDATE orders SET status='complete' WHERE user_id=1;
UPDATE users SET name='Bob' WHERE id=2;
-- Deadlock occurs here!
```

### Interview Questions

- How would you detect this deadlock programmatically?
- What are the prevention strategies (lock ordering, timeouts, etc.)?
- Design a deadlock detection algorithm for distributed systems
- How do databases choose which transaction to abort in a deadlock?
- Implement a wait-for graph for deadlock detection

## **3. Isolation Level Deep Dive**

### Isolation Levels Comparison

| Level | Dirty Read | Non-repeatable Read | Phantom Read | Locking Overhead |
|-------|------------|-------------------|--------------|------------------|
| Read Uncommitted | Yes | Yes | Yes | Minimal |
| Read Committed | No | Yes | Yes | Low |
| Repeatable Read | No | No | Yes* | Medium |
| Serializable | No | No | No | High |

*Note: InnoDB prevents phantom reads at Repeatable Read level

### Scenario-Based Questions

- An e-commerce app needs to show consistent inventory across pages - which isolation level?
- Banking system transferring money between accounts - isolation requirements?
- Analytics dashboard reading from OLTP database - isolation choice?
- How does MVCC change the locking behavior at each isolation level?

## **4. Database Scaling Challenges**

### Read Scaling

- **Read replicas** - how to handle read-after-write consistency?
- **Connection pooling** - how do you distribute connections across replicas?
- **Replica lag** - strategies to handle stale reads?
- **Load balancing** - session affinity vs round-robin for read queries?

### Write Scaling  

- **Sharding strategies** - range vs hash vs directory-based partitioning
- **Hot partitions** - identification and redistribution techniques
- **Cross-shard transactions** - 2PC vs saga pattern vs eventual consistency
- **Shard rebalancing** - online vs offline approaches

### Specific Scenarios

```sql
-- Hot partition problem
-- All users born in 2000 end up on same shard
CREATE TABLE users (
    id BIGINT,
    birth_year INT,
    -- Sharded by birth_year % 10
);

-- Better sharding strategy?
CREATE TABLE users (
    id BIGINT,
    user_hash VARCHAR(32), -- hash(id + salt)
    birth_year INT,
    -- Shard by user_hash
);
```

## **5. MVCC (Multi-Version Concurrency Control)**

### Implementation Details

- How does PostgreSQL implement MVCC with tuple versioning?
- InnoDB's undo logs vs PostgreSQL's tuple approach - tradeoffs?
- Snapshot isolation - how are consistent snapshots maintained?
- Transaction ID assignment and visibility rules

### Performance Implications

- **Vacuum processes** - when do they run and impact on performance?
- **Bloat management** - detecting and handling table/index bloat
- **Long-running transactions** - impact on MVCC cleanup
- **Read-only transaction optimization** - how databases optimize these

### Interview Questions

- Design MVCC for a new database engine
- How would you handle a transaction running for 24 hours?
- Explain the visibility map in PostgreSQL
- Compare MVCC with traditional 2PL (Two-Phase Locking)

## **6. Lock-Free Data Structures**

### Core Concepts

- **Compare-and-swap (CAS)** operations and atomic primitives
- **ABA problem** - what is it and how to solve it?
- **Memory ordering** - sequential consistency vs relaxed ordering
- **Lock-free vs wait-free** guarantees - difference and examples

### Implementation Challenges

```cpp
// Lock-free counter - identify the race condition
class LockFreeCounter {
    std::atomic<int> count{0};
public:
    void increment() {
        int old_val = count.load();
        while (!count.compare_exchange_weak(old_val, old_val + 1)) {
            // What happens here in high contention?
        }
    }
};
```

### Database Applications

- Lock-free hash tables for buffer pools
- Atomic operations for reference counting
- RCU (Read-Copy-Update) in database internals
- Lock-free queues for transaction logging

## **7. Advanced Concurrency Patterns**

### Optimistic vs Pessimistic Locking

```sql
-- Pessimistic: Lock immediately
SELECT * FROM inventory WHERE product_id = 123 FOR UPDATE;
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 123;

-- Optimistic: Check version on update
SELECT quantity, version FROM inventory WHERE product_id = 123;
UPDATE inventory 
SET quantity = quantity - 1, version = version + 1 
WHERE product_id = 123 AND version = ?;
```

### When to use each approach?

- High contention scenarios
- Long-running transactions
- Distributed systems considerations

## **8. Real-World System Design Questions**

### **Scenario 1: Concert Ticket Booking**

- 100K users trying to book 5K seats simultaneously
- Prevent overselling while maintaining performance
- Handle partial failures and rollbacks
- Design for both SQL and NoSQL approaches

### **Scenario 2: Banking System**

- Transfer money between accounts (ACID requirements)
- Handle distributed transactions across data centers
- Implement fraud detection with minimal latency impact
- Design for regulatory compliance (audit trails)

### **Scenario 3: Social Media Feed**

- Millions of concurrent reads and writes
- Ensure users see consistent view of their timeline
- Handle celebrity users with millions of followers
- Balance between freshness and performance

### **Scenario 4: Inventory Management**

- E-commerce platform with real-time inventory
- Multiple warehouses and distribution centers
- Handle reservation vs allocation
- Design for Black Friday traffic (100x normal load)

## **9. Database-Specific Questions**

### **PostgreSQL**

- Explain advisory locks and use cases
- How does autovacuum work and when might it cause issues?
- Table-level locks during DDL operations - mitigation strategies?
- Connection pooling with PgBouncer - transaction vs session pooling?

### **MySQL/InnoDB**

- Gap locking behavior and impact on concurrency
- Clustered vs secondary index locking differences
- How does InnoDB handle foreign key locking?
- Online DDL operations - which ones lock the table?

### **MongoDB**

- Document-level vs collection-level locking evolution
- WiredTiger storage engine concurrency improvements
- Optimistic concurrency control in MongoDB
- Sharding and balancer lock implications

## **10. Performance Troubleshooting**

### **Lock Contention Diagnosis**

```sql
-- PostgreSQL: Find blocking queries
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype;

-- MySQL: Check for lock waits
SELECT * FROM performance_schema.data_lock_waits;
```

### **Optimization Strategies**

- Index design to reduce lock duration
- Query optimization to minimize lock scope
- Connection pooling tuning
- Read replica strategies for read-heavy workloads

### **Monitoring and Alerting**

- Key metrics to monitor for lock contention
- Setting up alerts for deadlock frequency
- Performance schema/pg_stat_* tables usage
- Lock wait time SLA definitions

## **11. Distributed Database Challenges**

### **Consensus Protocols**

- Raft vs PBFT for distributed locking
- How does Google Spanner implement distributed locks?
- CAP theorem implications for locking systems
- Partition tolerance during lock acquisition

### **Distributed Deadlock Detection**

- Algorithms for detecting deadlocks across nodes
- Timeout-based vs detection-based approaches
- False positive handling in distributed environments
- Performance impact of distributed deadlock detection

## **Sample Interview Flow**

### **Question**: "Design a distributed reservation system for airline seats"

**Expected Discussion Points:**

1. **Consistency Requirements**: Strong vs eventual consistency
2. **Concurrency Control**: Optimistic vs pessimistic locking
3. **Partitioning Strategy**: By flight, by route, or by time?
4. **Conflict Resolution**: What happens when two users book the same seat?
5. **Performance Requirements**: Response time vs throughput
6. **Failure Handling**: Network partitions, node failures
7. **Scalability**: Peak booking times (holidays, sales)

**Follow-up Questions:**

- How would you handle overbooking scenarios?
- What if the system needs to support holds/reservations?
- How do you ensure audit compliance?
- Performance testing strategy for this system?

---

*This document covers the most common and challenging database locking and parallelism interview questions. Practice implementing these concepts and be prepared to discuss tradeoffs and real-world implications.*
