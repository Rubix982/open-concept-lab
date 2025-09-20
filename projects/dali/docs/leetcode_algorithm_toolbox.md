# LeetCode Algorithm Toolbox

- [LeetCode Algorithm Toolbox](#leetcode-algorithm-toolbox)
  - [**1. Arrays \& Strings**](#1-arrays--strings)
  - [**2. Linked Lists**](#2-linked-lists)
  - [**3. Stacks \& Queues**](#3-stacks--queues)
  - [**4. Trees \& Graphs**](#4-trees--graphs)
  - [**5. Heaps / Priority Queues**](#5-heaps--priority-queues)
  - [**6. Dynamic Programming (DP)**](#6-dynamic-programming-dp)
  - [**7. Hashing \& Maps**](#7-hashing--maps)
  - [**8. Bit Manipulation**](#8-bit-manipulation)
  - [**9. Math \& Number Theory**](#9-math--number-theory)
  - [**10. Advanced / Misc**](#10-advanced--misc)
  - [**LeetCode Pattern Map**](#leetcode-pattern-map)
    - [**1. Array \& String Patterns**](#1-array--string-patterns)
    - [**2. Linked List Patterns**](#2-linked-list-patterns)
    - [**3. Stack \& Queue Patterns**](#3-stack--queue-patterns)
    - [**4. Tree \& Graph Patterns**](#4-tree--graph-patterns)
    - [**5. Heap / Priority Queue Patterns**](#5-heap--priority-queue-patterns)
    - [**6. Dynamic Programming Patterns**](#6-dynamic-programming-patterns)
    - [**7. Hashing / Map Patterns**](#7-hashing--map-patterns)
    - [**8. Bit Manipulation Patterns**](#8-bit-manipulation-patterns)
    - [**9. Math \& Number Theory**](#9-math--number-theory-1)
    - [**10. Binary Search \& Optimization**](#10-binary-search--optimization)
    - [**11. Advanced / Misc Patterns**](#11-advanced--misc-patterns)
  - [**System Design Algorithm \& Technique Toolbox**](#system-design-algorithm--technique-toolbox)
    - [**1. Caching \& Load Balancing**](#1-caching--load-balancing)
    - [**2. Storage \& Indexing**](#2-storage--indexing)
    - [**3. Distributed Systems**](#3-distributed-systems)
    - [**4. Networking**](#4-networking)
    - [**5. Monitoring \& Observability**](#5-monitoring--observability)
    - [**6. Security \& Reliability**](#6-security--reliability)
    - [**7. Scheduling \& Resource Management**](#7-scheduling--resource-management)

## **1. Arrays & Strings**

- Two pointers (e.g., sliding window, merging, partitioning)
  - [Two Sum II - Input array is sorted (LeetCode #167)](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/)
  - [Squares of a Sorted Array (LeetCode #977)](https://leetcode.com/problems/squares-of-a-sorted-array/)
- Prefix sums / suffix sums
- Kadane's algorithm (max subarray)
- Cyclic arrays / rotations
- Frequency counting / hashmap tricks
- Sorting-based techniques

---

## **2. Linked Lists**

- Slow & fast pointers (detect cycles, middle node, palindrome)
- Reversing linked lists (full or partial)
- Merge two lists / merge K lists
- Dummy node technique for simplifying insertions/deletions

---

## **3. Stacks & Queues**

- Monotonic stack (next greater / smaller element)
- Sliding window maximum (deque)
- Min-stack / max-stack design problems
- BFS queue usage patterns

---

## **4. Trees & Graphs**

- DFS / BFS (iterative & recursive)
- Binary tree traversals (preorder, inorder, postorder, level order)
- Tree DP / recursive accumulation
- Lowest Common Ancestor (LCA) techniques
- Graph traversals: adjacency list / matrix, visited set, topological sort
- Union-Find / Disjoint Set Union (DSU)

---

## **5. Heaps / Priority Queues**

- Min / max heap usage
- Sliding window median / kth largest element
- Merge K sorted lists or arrays
- Event simulation / interval scheduling

---

## **6. Dynamic Programming (DP)**

- 1D & 2D DP (classic: knapsack, edit distance, LIS, LCS)
- State compression
- Memoization + recursion
- DP on trees / graphs

---

## **7. Hashing & Maps**

- Counting frequency / two-sum / three-sum / n-sum variants
- Hashing arrays, strings, or tuples for uniqueness
- Sliding window + hash map (substring problems)

---

## **8. Bit Manipulation**

- XOR tricks (single number, subsets, swaps)
- Subset generation using bits
- Counting bits / checking powers of 2
- Masking techniques

---

## **9. Math & Number Theory**

- GCD / LCM
- Prime sieve / factorization
- Modular arithmetic
- Combinatorics / probability patterns

---

## **10. Advanced / Misc**

- Binary search (classic, on answer, or tricky conditions)
- Ternary search (optimization problems)
- Sliding window over strings / arrays with constraints
- Union of intervals / interval DP
- Top K problems (heap / quickselect)
- Segment trees / Fenwick trees (range queries / updates)

---

Perfect. Let's build a **Mega LeetCode Pattern Map**. I'll structure it so that each **pattern/technique** has **3–5 representative problems** you can practice, with difficulty and a brief note about why it matters. This will give you a **muscle-memory roadmap**, not just a list.

---

## **LeetCode Pattern Map**

---

### **1. Array & String Patterns**

| Pattern           | Example Problems                                                                                                                | Difficulty | Note                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------ |
| Sliding Window    | [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) | Medium     | Classic substring max length   |
| Sliding Window    | [Minimum Size Subarray Sum](https://leetcode.com/problems/minimum-size-subarray-sum/)                                           | Medium     | Dynamic window length          |
| Prefix/Suffix Sum | [Range Sum Query - Immutable](https://leetcode.com/problems/range-sum-query-immutable/)                                         | Easy       | Precompute sums                |
| Kadane's          | [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/)                                                             | Easy       | 1D max sum DP                  |
| Two Pointers      | [3Sum](https://leetcode.com/problems/3sum/)                                                                                     | Medium     | Sorting + two-pointer          |
| Hash Map Counting | [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/)                                                   | Medium     | Count prefix sums with hashmap |

---

### **2. Linked List Patterns**

| Pattern              | Example Problems                                                                            | Difficulty | Note                |
| -------------------- | ------------------------------------------------------------------------------------------- | ---------- | ------------------- |
| Slow & Fast Pointers | [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/)                       | Easy       | Detect cycle        |
| Reversal             | [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/)                   | Easy       | Reverse entire list |
| Merge Patterns       | [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/)             | Easy       | Classic merge       |
| Dummy Node Technique | [Remove Nth Node From End](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) | Medium     | Simplify edge cases |

---

### **3. Stack & Queue Patterns**

| Pattern             | Example Problems                                                                                      | Difficulty | Note                       |
| ------------------- | ----------------------------------------------------------------------------------------------------- | ---------- | -------------------------- |
| Monotonic Stack     | [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/)       | Hard       | Classic stack optimization |
| Stack-based Parsing | [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/)                                 | Easy       | Stack validation           |
| Sliding Window Max  | [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/)                       | Hard       | Deque implementation       |
| Queue / BFS         | [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) | Medium     | Standard BFS               |

---

### **4. Tree & Graph Patterns**

| Pattern                | Example Problems                                                                                                  | Difficulty | Note                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------- | ---------------------- |
| DFS / BFS              | [Number of Islands](https://leetcode.com/problems/number-of-islands/)                                             | Medium     | Standard grid DFS/BFS  |
| Tree DP / Recursion    | [Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/)                                   | Hard       | Recursion + DP         |
| Lowest Common Ancestor | [Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) | Medium     | Recursive solution     |
| Union-Find             | [Redundant Connection](https://leetcode.com/problems/redundant-connection/)                                       | Medium     | Detect cycles in graph |
| Topological Sort       | [Course Schedule](https://leetcode.com/problems/course-schedule/)                                                 | Medium     | Prerequisite ordering  |

---

### **5. Heap / Priority Queue Patterns**

| Pattern                     | Example Problems                                                                                  | Difficulty | Note                        |
| --------------------------- | ------------------------------------------------------------------------------------------------- | ---------- | --------------------------- |
| Kth Largest / Smallest      | [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/) | Medium     | Heap selection              |
| Merge K Sorted Lists        | [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/)                       | Hard       | Min-heap merge              |
| Event Simulation / Timeline | [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/)                               | Medium     | Heap for interval end-times |

---

### **6. Dynamic Programming Patterns**

| Pattern       | Example Problems                                                                        | Difficulty | Note               |
| ------------- | --------------------------------------------------------------------------------------- | ---------- | ------------------ |
| 1D DP         | [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/)                       | Easy       | Fibonacci-style DP |
| 2D DP         | [Unique Paths](https://leetcode.com/problems/unique-paths/)                             | Medium     | Grid traversal DP  |
| Knapsack      | [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) | Medium     | Classic knapsack   |
| DP on Strings | [Edit Distance](https://leetcode.com/problems/edit-distance/)                           | Hard       | Classic string DP  |
| DP on Trees   | [House Robber III](https://leetcode.com/problems/house-robber-iii/)                     | Medium     | DP on tree nodes   |

---

### **7. Hashing / Map Patterns**

| Pattern         | Example Problems                                                                  | Difficulty | Note                     |
| --------------- | --------------------------------------------------------------------------------- | ---------- | ------------------------ |
| Frequency Count | [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) | Medium     | Hash map + heap          |
| Subarray Sum    | [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/)     | Medium     | Prefix sums + map        |
| Deduplication   | [Group Anagrams](https://leetcode.com/problems/group-anagrams/)                   | Medium     | Canonical string hashing |

---

### **8. Bit Manipulation Patterns**

| Pattern          | Example Problems                                              | Difficulty | Note               |
| ---------------- | ------------------------------------------------------------- | ---------- | ------------------ |
| XOR Tricks       | [Single Number](https://leetcode.com/problems/single-number/) | Easy       | XOR to find unique |
| Subset / Mask DP | [Counting Bits](https://leetcode.com/problems/counting-bits/) | Medium     | Bitmasking         |
| Check Power of 2 | [Power of Two](https://leetcode.com/problems/power-of-two/)   | Easy       | Bit tricks         |

---

### **9. Math & Number Theory**

| Pattern             | Example Problems                                                                                        | Difficulty | Note                 |
| ------------------- | ------------------------------------------------------------------------------------------------------- | ---------- | -------------------- |
| GCD / LCM           | [Greatest Common Divisor of Strings](https://leetcode.com/problems/greatest-common-divisor-of-strings/) | Easy       | String + GCD analogy |
| Prime Factorization | [Ugly Number II](https://leetcode.com/problems/ugly-number-ii/)                                         | Medium     | Multiples of primes  |
| Modular Arithmetic  | [Pow(x, n)](https://leetcode.com/problems/powx-n/)                                                      | Medium     | Fast exponentiation  |
| Combinatorics       | [Combinations](https://leetcode.com/problems/combinations/)                                             | Medium     | Recursive generation |

---

### **10. Binary Search & Optimization**

| Pattern                    | Example Problems                                                                                                                       | Difficulty | Note                         |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ---------------------------- |
| Classic Binary Search      | [Binary Search](https://leetcode.com/problems/binary-search/)                                                                          | Easy       | Standard search              |
| Search on Answer           | [Capacity To Ship Packages Within D Days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/)                      | Medium     | Binary search on constraints |
| Sliding Window + Condition | [Longest Subarray of 1's After Deleting One Element](https://leetcode.com/problems/longest-subarray-of-1s-after-deleting-one-element/) | Medium     | Two-pointer + condition      |

---

### **11. Advanced / Misc Patterns**

| Pattern                | Example Problems                                                                                          | Difficulty | Note                        |
| ---------------------- | --------------------------------------------------------------------------------------------------------- | ---------- | --------------------------- |
| Interval Merge / Union | [Merge Intervals](https://leetcode.com/problems/merge-intervals/)                                         | Medium     | Sorting + interval handling |
| Segment Tree           | [Range Sum Query - Mutable](https://leetcode.com/problems/range-sum-query-mutable/)                       | Hard       | Segment tree practice       |
| Fenwick Tree           | [Count of Smaller Numbers After Self](https://leetcode.com/problems/count-of-smaller-numbers-after-self/) | Hard       | BIT tree / Fenwick tree     |
| Two-Pointer Trick      | [3Sum Closest](https://leetcode.com/problems/3sum-closest/)                                               | Medium     | Sorting + two-pointer       |

## **System Design Algorithm & Technique Toolbox**

### **1. Caching & Load Balancing**

- **Eviction Policies** → LRU, LFU, ARC (used in Redis, Memcached, OS page replacement).
- **Hashing Techniques** → Consistent Hashing, Rendezvous Hashing (used in load balancers, sharded DBs).
- **Bloom Filters / Count-Min Sketch** → Probabilistic membership & frequency checks (used in CDNs, databases).
- **LRU Cache Implementation** → Map + Doubly Linked List.

### **2. Storage & Indexing**

- **B-Trees & B+ Trees** → Core of relational DB indexes.
- **LSM Trees** → Write-optimized storage (Cassandra, LevelDB, RocksDB).
- **Skip Lists** → Ordered map alternative (used in Redis).
- **Trie / Radix Trees** → Prefix-based indexing (DNS, IP routing, search engines).
- **Inverted Index** → Search engines, log search (Lucene, Elasticsearch).

### **3. Distributed Systems**

- **Leader Election** → Paxos, Raft basics.
- **Consensus** → 2PC, 3PC, Raft log replication.
- **Quorum Reads/Writes** → Cassandra/Dynamo style trade-offs.
- **Vector Clocks / Lamport Timestamps** → Event ordering in distributed systems.
- **Gossip Protocols** → Cluster membership, failure detection.

### **4. Networking**

- **TCP Congestion Control** → Reno, CUBIC, BBR.
- **Load Shedding & Circuit Breakers** → Resilience under failure.
- **CDN Caching Algorithms** → Edge cache invalidation, TTLs.
- **Consistent Hashing for CDNs**.
- **Retry with Exponential Backoff + Jitter** → Prevents thundering herd.

### **5. Monitoring & Observability**

- **Time-Series Data Structures** → Round-Robin DB (RRD), TSDB compaction.
- **Approximate Aggregates** → HyperLogLog (unique counts), Count-Min Sketch.
- **Reservoir Sampling** → Streaming metrics, log analysis.

### **6. Security & Reliability**

- **Merkle Trees** → Data integrity in Git, blockchains, distributed storage.
- **CAP Theorem Tradeoffs** → Partition tolerance choices.
- **Shamir's Secret Sharing** → Key distribution.
- **Hash Chains / HMACs** → Secure logging, authentication.

### **7. Scheduling & Resource Management**

- **Fair Queuing Algorithms** → Weighted Fair Queuing, DRR (network routers, Kubernetes scheduling).
- **Priority Inversion Handling** → OS schedulers.
- **Token Bucket / Leaky Bucket** → Rate limiting (APIs, load balancers).
- **Backpressure** → Streaming systems like Kafka.
