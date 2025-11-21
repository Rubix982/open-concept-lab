# **Exploring Unique and Advanced Algorithms**

## **1. Introduction**

Most programmers learn classic algorithms like Dijkstra's, Merge Sort, or Binary Search. But beyond the fundamentals lies a world of **obscure, specialized, and highly optimized algorithms** used in advanced domains such as computational geometry, string matching, cryptography, parallel computing, and randomized algorithms.  

These algorithms are less commonly taught but extremely powerful when applied in the right context. Understanding them can provide a **strategic edge in system design, research, and competitive programming**.

---

- [**Exploring Unique and Advanced Algorithms**](#exploring-unique-and-advanced-algorithms)
  - [**1. Introduction**](#1-introduction)
  - [**2. Graph Algorithms**](#2-graph-algorithms)
    - [**2.1 Hopcroft-Karp Algorithm**](#21-hopcroft-karp-algorithm)
    - [**2.2 Edmonds' Blossom Algorithm**](#22-edmonds-blossom-algorithm)
    - [**2.3 Push-Relabel Maximum Flow**](#23-push-relabel-maximum-flow)
    - [**2.4 Stoer-Wagner Min Cut**](#24-stoer-wagner-min-cut)
    - [**2.5 Dynamic Graph Algorithms**](#25-dynamic-graph-algorithms)
  - [**3. String and Text Algorithms**](#3-string-and-text-algorithms)
    - [**3.1 Knuth-Morris-Pratt (KMP)**](#31-knuth-morris-pratt-kmp)
    - [**3.2 Z-Algorithm**](#32-z-algorithm)
    - [**3.3 Aho-Corasick Automaton**](#33-aho-corasick-automaton)
    - [**3.4 Ukkonen's Algorithm (Suffix Trees)**](#34-ukkonens-algorithm-suffix-trees)
    - [**3.5 Burrows-Wheeler Transform (BWT)**](#35-burrows-wheeler-transform-bwt)
    - [**3.6 Manacher's Algorithm**](#36-manachers-algorithm)
  - [**4. Computational Geometry**](#4-computational-geometry)
    - [**4.1 Convex Hull (Graham Scan, Chan's Algorithm)**](#41-convex-hull-graham-scan-chans-algorithm)
    - [**4.2 Sweep Line Algorithms (Bentley-Ottmann)**](#42-sweep-line-algorithms-bentley-ottmann)
    - [**4.3 Voronoi Diagrams / Delaunay Triangulation**](#43-voronoi-diagrams--delaunay-triangulation)
    - [**4.4 Rotating Calipers**](#44-rotating-calipers)
    - [**4.5 Range Searching Algorithms**](#45-range-searching-algorithms)
  - [**5. Number Theory \& Cryptography**](#5-number-theory--cryptography)
    - [**5.1 Fast Fourier Transform (FFT)**](#51-fast-fourier-transform-fft)
    - [**5.2 Miller-Rabin Primality Test**](#52-miller-rabin-primality-test)
    - [**5.3 Pollard's Rho Algorithm**](#53-pollards-rho-algorithm)
    - [**5.4 Montgomery Multiplication**](#54-montgomery-multiplication)
    - [**5.5 Elliptic Curve Algorithms**](#55-elliptic-curve-algorithms)
  - [**6. Randomized \& Approximation Algorithms**](#6-randomized--approximation-algorithms)
    - [**6.1 Monte Carlo Methods**](#61-monte-carlo-methods)
    - [**6.2 Las Vegas Algorithms**](#62-las-vegas-algorithms)
    - [**6.3 Randomized QuickSort**](#63-randomized-quicksort)
    - [**6.4 Approximate Counting (Flajolet-Martin)**](#64-approximate-counting-flajolet-martin)
    - [**6.5 Simulated Annealing**](#65-simulated-annealing)
  - [**7. Parallel and External Memory Algorithms**](#7-parallel-and-external-memory-algorithms)
    - [**7.1 MapReduce Algorithms**](#71-mapreduce-algorithms)
    - [**7.2 Parallel Prefix Sum (Scan)**](#72-parallel-prefix-sum-scan)
    - [**7.3 External Merge Sort**](#73-external-merge-sort)
    - [**7.4 Cache-Oblivious Algorithms**](#74-cache-oblivious-algorithms)
  - [**8. Obscure \& Specialized Algorithms**](#8-obscure--specialized-algorithms)
    - [**8.1 Dancing Links (DLX)**](#81-dancing-links-dlx)
    - [**8.2 Reservoir Sampling**](#82-reservoir-sampling)
    - [**8.3 Online Bipartite Matching (Karp-Vazirani-Vazirani)**](#83-online-bipartite-matching-karp-vazirani-vazirani)
    - [**8.4 Gale-Shapley Stable Matching**](#84-gale-shapley-stable-matching)
    - [**8.5 Kinetic Data Algorithms**](#85-kinetic-data-algorithms)
  - [**9 Persistent Data Structures**](#9-persistent-data-structures)
    - [Core Concept](#core-concept)
    - [Fundamental Techniques](#fundamental-techniques)
      - [Path Copying (Fat Node Method)](#path-copying-fat-node-method)
      - [How it works:](#how-it-works)
      - [Node Copying vs. Fat Nodes](#node-copying-vs-fat-nodes)
    - [Key Examples](#key-examples)
      - [Persistent Segment Tree](#persistent-segment-tree)
        - [Structure](#structure)
        - [Application](#application)
        - [Example Problem](#example-problem)
    - [Persistent-Union Find (Disjoint Set)](#persistent-union-find-disjoint-set)
      - [Solution](#solution)
      - [Complexity](#complexity)
      - [Application](#application-1)
    - [Persistent Treap](#persistent-treap)
      - [Why Treaps Work Well](#why-treaps-work-well)
      - [Operations](#operations)
      - [Use Cases](#use-cases)
    - [Persistent Array](#persistent-array)
      - [Implementation (Radix Tree)](#implementation-radix-tree)
    - [Persistent Red-Black Tress](#persistent-red-black-tress)
      - [Solution](#solution-1)
      - [Complexity](#complexity-1)
    - [Real-World Applications](#real-world-applications)
      - [Version Control Systems (Git)](#version-control-systems-git)
      - [Databases With Time-Travel - PostgreSQL MVCC (Multi-Version Concurrency Control)](#databases-with-time-travel---postgresql-mvcc-multi-version-concurrency-control)
      - [Datomic Database](#datomic-database)
      - [Functional Programming Languages](#functional-programming-languages)
      - [Undo/Redo Systems](#undoredo-systems)
      - [Blockchain \& Immutable Ledgers](#blockchain--immutable-ledgers)
      - [Computational Geometry](#computational-geometry)
      - [Trade-offs](#trade-offs)
    - [Performance Characteristics](#performance-characteristics)
  - [**9. Conclusion**](#9-conclusion)

---

## **2. Graph Algorithms**

### **2.1 Hopcroft-Karp Algorithm**

- **Concept:** Efficient algorithm for maximum bipartite matching in `O(E√V)`.  
- **Use-Cases:** Task assignment, scheduling, network flow.  
- **Obscure Fact:** Faster than augmenting-path algorithms for large bipartite graphs.  

---

### **2.2 Edmonds' Blossom Algorithm**

- **Concept:** Polynomial-time algorithm for maximum matching in general graphs.  
- **Use-Cases:** Network design, social network analysis.  
- **Why Rare:** Implementation complexity (shrinking blossoms).  

---

### **2.3 Push-Relabel Maximum Flow**

- **Concept:** Max flow algorithm with preflow and push/relabel operations.  
- **Use-Cases:** Network optimization, circulation problems.  
- **Comparison:** Often faster in practice than Edmonds-Karp.  

---

### **2.4 Stoer-Wagner Min Cut**

- **Concept:** Global minimum cut in undirected graphs in near-quadratic time.  
- **Use-Cases:** Network reliability, clustering.  

---

### **2.5 Dynamic Graph Algorithms**

- **Concept:** Maintain connectivity, shortest paths, or MSTs as the graph changes.  
- **Use-Cases:** Real-time road networks, evolving social graphs.  

---

## **3. String and Text Algorithms**

### **3.1 Knuth-Morris-Pratt (KMP)**

- Linear-time substring search with prefix function.  

### **3.2 Z-Algorithm**

- Linear-time substring matching alternative to KMP.  

### **3.3 Aho-Corasick Automaton**

- Multi-pattern search using a trie with failure links.  
- Used in intrusion detection systems.  

### **3.4 Ukkonen's Algorithm (Suffix Trees)**

- Online linear-time suffix tree construction.  

### **3.5 Burrows-Wheeler Transform (BWT)**

- Core of bzip2 and FM-index.  

### **3.6 Manacher's Algorithm**

- Finds longest palindromic substring in O(n).  

---

## **4. Computational Geometry**

### **4.1 Convex Hull (Graham Scan, Chan's Algorithm)**

- Find smallest convex polygon containing points.  

### **4.2 Sweep Line Algorithms (Bentley-Ottmann)**

- Detect all line segment intersections.  

### **4.3 Voronoi Diagrams / Delaunay Triangulation**

- Partition space by nearest neighbor.  

### **4.4 Rotating Calipers**

- Compute width/diameter of convex polygons.  

### **4.5 Range Searching Algorithms**

- Orthogonal range searching, interval trees.  

---

## **5. Number Theory & Cryptography**

### **5.1 Fast Fourier Transform (FFT)**

- Used for fast polynomial and convolution operations.  

### **5.2 Miller-Rabin Primality Test**

- Randomized primality testing.  

### **5.3 Pollard's Rho Algorithm**

- Integer factorization via random walks.  

### **5.4 Montgomery Multiplication**

- Efficient modular multiplication.  

### **5.5 Elliptic Curve Algorithms**

- Basis of modern cryptography.  

---

## **6. Randomized & Approximation Algorithms**

### **6.1 Monte Carlo Methods**

- Probabilistic algorithms with bounded error.  

### **6.2 Las Vegas Algorithms**

- Always correct, random runtime.  

### **6.3 Randomized QuickSort**

- Avoids worst-case pivoting.  

### **6.4 Approximate Counting (Flajolet-Martin)**

- Early basis of HyperLogLog.  

### **6.5 Simulated Annealing**

- Randomized optimization method.  

---

## **7. Parallel and External Memory Algorithms**

### **7.1 MapReduce Algorithms**

- Divide computation across nodes.  

### **7.2 Parallel Prefix Sum (Scan)**

- Fundamental in GPU programming.  

### **7.3 External Merge Sort**

- Sorting large datasets with limited RAM.  

### **7.4 Cache-Oblivious Algorithms**

- Designed without explicit cache tuning.  

---

## **8. Obscure & Specialized Algorithms**

### **8.1 Dancing Links (DLX)**

- Donald Knuth's efficient exact cover solver.  

### **8.2 Reservoir Sampling**

- Sample k items from streaming data.  

### **8.3 Online Bipartite Matching (Karp-Vazirani-Vazirani)**

- Randomized algorithm for online matching.  

### **8.4 Gale-Shapley Stable Matching**

- Stable marriage problem solver.  

### **8.5 Kinetic Data Algorithms**

- Maintain properties as points move.  

## **9 Persistent Data Structures**

### Core Concept

Persistent data structures preserve all previous versions of themselves when modified, rather than destructively updating in-place. Each modification creates a new version while keeping old versions accessible and fully functional.

Types of Persistence

* Partially Persistent: Can access all old versions but only modify the latest
* Fully Persistent: Can access AND modify any version (branching history)
* Confluently Persistent: Can combine multiple versions into a new version

### Fundamental Techniques

#### Path Copying (Fat Node Method)

When modifying a node, copy only the nodes along the path from root to the modified node. Share unchanged subtrees between versions.

Example: Persistent Binary Tree
Time Complexity: O(log n) per operation
Space per version: O(log n) additional nodes

#### How it works:

Insert/update at leaf: copy path from root to leaf
All other nodes remain shared

Each version maintains its own root pointer

#### Node Copying vs. Fat Nodes

1. Path Copying,
   1. Create new nodes with updated values
   2. Point to existing children where unchanged
   3. Lightweight and cache-friendly
2. Fat Nodes,
   1. Store all historical values in each node
   2. Each modification adds timestamp + value
   3. Better when many updates to same nodes

### Key Examples

#### Persistent Segment Tree

Use Case: Query any version of a range structure

##### Structure

* Each update creates O(lg n) new nodes
* Old versions remain queryable
* Total space: O(m lg n) for m updates

##### Application

* Time-series range queries
* "What was the sum of range [L,R] at time T?"
* Computational geometry (point-in-time sweeps)

##### Example Problem

```text
Given array modifications over time, answer:
"What was the maximum value in range [10, 50] 
after the 37th update?"
```

### Persistent-Union Find (Disjoint Set)

Challenge: Union-Find uses path compression (destructive)

#### Solution

* Remove path compression OR
* Use lazy path copying with timestamps
* Maintain version tree modified of union operations

#### Complexity

* Without path compression: O(log n) per operation
* With persistent path compression: O(log^2 n)

#### Application

* Dynamic connectivity queries at different times
* "Were nodes A and B connected after update 15?"

### Persistent Treap

#### Why Treaps Work Well

* Randomized structure naturally supports path copying
* Split/merge operations creates new roots
* Expected O(log n) per operation

#### Operations

* Split: Returns two new treaps
* Merge: Creates new root
* Insert/delete via split+merge

#### Use Cases

* Versioned ordered sets
* Rope data structure (text editors)
* Implicit key structures

### Persistent Array

Goal: Support O(1) access and O(log n) updates

#### Implementation (Radix Tree)

* 32-ary or 64-ary tree
* Array indices as keys
* Only copy path to modified element

Space: O(log n) is around O(1) practically for 32-bit indices

### Persistent Red-Black Tress

Challenge: Red-black trees require rotations affecting multiple nodes

#### Solution

* Copy nodes involved in rotations
* Maintain balance properties per version
* Each rotation affects O(1) nodes

#### Complexity

* Insert/Delete: O(log n) time, O(log n) space per operation
* Access any version: O(log n)

### Real-World Applications

#### Version Control Systems (Git)

* Each commit is a version
* Trees are shared between commits (unchanged directories)
* Only differences are stored

#### Databases With Time-Travel - PostgreSQL MVCC (Multi-Version Concurrency Control)

* Each transaction sees a consistent snapshot
* Old versions maintained for rollback
* Garbage collection removes old versions

#### Datomic Database

* Immutable facts with timestamps
* Query database at any point in time
* Built on persistent data structures

#### Functional Programming Languages

* Clojure,
  * All core data structures are persistent
  * Structural sharing for efficiency
  * Enables safe concurrent programming

Example:

```clojure
(def v1 [1 2 3 4 5])
(def v2 (assoc v1 2 99))  ; v1 unchanged, v2 shares structure
```

#### Undo/Redo Systems

* Text Editors,
  * Each edit creates new version
  * Jump to any previous state instantly
  * No need to reverse operations
* Graphics Software,
  * Non-destructive editing
  * Layer History
  * Branching edits

#### Blockchain & Immutable Ledgers

* Each block is a new version
* Previous states remain accessible
* Merkle trees for efficient verification

#### Computational Geometry

* Sweepline with Persistent BST,
  * Maintain event structure across sweep
  * Query geometric relationships at different x-coordinates
  * Rollback to previous sweep positions

#### Trade-offs

* Advantages,
  * Safety: No mutation means no race conditions
  * Simplicity: Easier to reason about
  * History: Access any past state O(1) switching
  * Undo: Free undo/redo functionality
  * Parallelism: Safety share between threads
* Disadvantages,
  * Space: O(log n) overhead per update (vs O(1) mutable)
  * Constant factors: Copying has overhead
  * Cache: More pointer chasing, less cache friendly
  * GC Pressure: Creates more objects (in managed languages)

### Performance Characteristics

| Operation Mutable Persistent (Path Copy)        |
| :---------------------------------------------- |
| Access  O(1) or O(log n)  Same as mutable       |
| Update  O(1) or O(log n)  Same + O(log n) space |
| Access old version  N/A O(1) version switch     |
| Space per version O(n)  O(log n)                |
|                                                 |

---

## **9. Conclusion**

These algorithms often remain hidden in advanced textbooks or research papers, but they offer **superior performance in specialized scenarios**. By mastering them, engineers can approach **systems, databases, cryptography, and geometry problems** with powerful tools that others might overlook.
