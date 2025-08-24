# The Competitive Programming Algorithm Toolbox

## **1. Basics & Foundations**

* **Prefix sums / Difference arrays**
* **Two pointers / Sliding window**
* **Binary search (on array, on answer, parametric search)**
* **Sorting tricks (coordinate compression, custom comparators)**
* **Hashing (rolling hash, string hashing, double hashing)**
* **Modular arithmetic (mod inverse, fast exponentiation, CRT basics)**

---

## **2. Greedy Techniques**

* Interval scheduling (earliest finishing time)
* Activity selection / Sweep line methods
* Huffman coding (optimal merge patterns)
* Greedy with sorting + priority queue (classic scheduling, intervals, tasks)
* Exchange argument proofs

---

## **3. Divide & Conquer / Binary Search Variants**

* Divide & conquer DP optimization
* Convex hull trick (for DP optimization)
* Ternary search (on unimodal functions)
* Meet-in-the-middle (subset sum, exponential problems)

---

## **4. Graph Theory**

* BFS / DFS (basic traversals)
* Topological sort
* Connected components (Union-Find / DSU)
* Dijkstra's algorithm (with heap)
* Bellman-Ford (for negative edges)
* Floyd-Warshall (all-pairs shortest paths)
* Minimum spanning tree (Kruskal, Prim)
* Bridges & articulation points (Tarjan's algorithm)
* Strongly connected components (Kosaraju, Tarjan)
* Eulerian path / circuit (Hierholzer's algorithm)
* Hamiltonian path (bitmask DP or backtracking)
* Max flow (Ford-Fulkerson, Edmonds-Karp, Dinic)
* Min-cost max flow
* Bipartite matching (Hungarian, Hopcroft-Karp)
* Network flow applications (assignment problems, circulation)

---

## **5. Trees**

* Binary lifting (LCA, ancestor queries)
* Heavy-light decomposition (path queries)
* Euler tour + RMQ trick for LCA
* Centroid decomposition
* Tree DP (classic rooted DP problems)
* Rerooting techniques (DP on trees with re-root transitions)

---

## **6. Dynamic Programming**

* Classic 1D/2D DP (knapsack, LIS, edit distance, coin change)
* Digit DP
* Subset DP (bitmask DP)
* SOS DP (sum over subsets)
* Interval DP (matrix chain multiplication, optimal binary search trees)
* DP on graphs (DAG longest path, etc.)
* DP + bitmasks (traveling salesman)
* DP with convex hull / divide & conquer optimization
* Tree DP (independent set, diameter, etc.)

---

## **7. Advanced Data Structures**

* Segment tree (point update, range query)
* Fenwick tree / BIT
* Persistent segment tree (k-th order statistics)
* Lazy propagation (range updates, range queries)
* Treaps, Splay trees
* Sparse table (RMQ, idempotent functions)
* Disjoint set union (with path compression, union by rank)
* Link-cut trees (dynamic trees)
* Mo's algorithm (offline queries)
* Wavelet trees (frequency/rank queries)

---

## **8. String Algorithms**

* KMP (pattern matching)
* Z-function
* Prefix function (pi array)
* Rabin-Karp hashing
* Suffix array (with LCP)
* Suffix automaton
* Aho-Corasick automaton (multiple pattern matching)
* Manacher's algorithm (longest palindrome)
* Trie / compressed trie
* Rolling hash tricks (substring equality, palindrome checking)

---

## **9. Geometry & Math**

* Convex hull (Graham scan, Andrew monotone chain)
* Rotating calipers (diameter, closest pair, width)
* Line sweep algorithms (events, intersections)
* Closest pair of points (divide & conquer)
* Circle intersection, polygon area (shoelace formula)
* Pick's theorem
* Fast Fourier Transform (FFT, NTT for polynomial multiplication)
* Matrix exponentiation
* Linear algebra (Gaussian elimination, matrix rank)
* Number theory (sieve of Eratosthenes, segmented sieve)
* GCD/LCM, extended Euclidean algorithm
* Modular inverse, Chinese remainder theorem
* Euler's totient, Mobius function
* Miller-Rabin primality test, Pollard rho factorization

---

## **10. Probability / Randomization**

* Monte Carlo algorithms (random primality testing)
* Randomized hashing
* Reservoir sampling
* Randomized quicksort / treaps

---

## **11. Specialized Techniques**

* Bit tricks (lowest set bit, bit masks for subsets)
* Meet-in-the-middle (for exponential search space)
* Inclusion-exclusion principle
* Fast Walsh-Hadamard transform (XOR convolutions)
* Dynamic connectivity (DSU rollback, divide & conquer on queries)
* Heavy-light + segment tree for dynamic paths
* Sprague-Grundy theorem (Nim games, impartial games)

---

## **Russian-Style Problem-Solving Map**

### **1. Spotting Hidden Invariants**

| Technique                  | Example Problems                                                  | Difficulty | Note                                                |
| -------------------------- | ----------------------------------------------------------------- | ---------- | --------------------------------------------------- |
| Track invariant quantities | [Game of Stones](https://codeforces.com/problemset/problem/359/B) | Medium     | Find what never changes to simplify decision-making |
| Parity / Modulus tricks    | [Even-Odd Game](https://codeforces.com/problemset/problem/451/B)  | Easy       | Often reduces complex operations to parity checks   |

---

### **2. Reduce to Canonical Form**

| Technique                   | Example Problems                                                             | Difficulty | Note                                   |
| --------------------------- | ---------------------------------------------------------------------------- | ---------- | -------------------------------------- |
| Sorting / Normalizing input | [Remove Duplicate Intervals](https://leetcode.com/problems/merge-intervals/) | Medium     | Makes greedy solutions apparent        |
| Coordinate compression      | [Compressed Array Queries](https://codeforces.com/problemset/problem/276/C)  | Hard       | Reduce large ranges to smaller indices |

---

### **3. Backward Reasoning**

| Technique                  | Example Problems                                                         | Difficulty | Note                                |
| -------------------------- | ------------------------------------------------------------------------ | ---------- | ----------------------------------- |
| Reverse simulation         | [Last Person Standing](https://codeforces.com/problemset/problem/602/B)  | Medium     | Think from end state to start       |
| Goal-oriented construction | [Constructing Sequence](https://codeforces.com/problemset/problem/977/C) | Medium     | Build answer by reasoning backwards |

---

### **4. Extremal Principle**

| Technique                    | Example Problems                                                              | Difficulty | Note                                    |
| ---------------------------- | ----------------------------------------------------------------------------- | ---------- | --------------------------------------- |
| Consider largest/smallest    | [Maximum Pair Sum](https://codeforces.com/problemset/problem/489/C)           | Medium     | Anchor reasoning on extremal element    |
| First/last element as anchor | [Minimum Swaps to Sort](https://leetcode.com/problems/minimum-swaps-to-sort/) | Medium     | Helps find forced moves and constraints |

---

### **5. Greedy Guess + Proof**

| Technique              | Example Problems                                                                        | Difficulty | Note                                                    |
| ---------------------- | --------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------- |
| Natural greedy choices | [Activity Selection](https://leetcode.com/problems/non-overlapping-intervals/)          | Easy       | Pick earliest end or largest gain and prove correctness |
| Check if greedy fails  | [Weighted Interval Scheduling](https://leetcode.com/problems/maximum-intervals-weight/) | Medium     | Test greedy on small cases                              |

---

### **6. Simplify to 1D / Projection**

| Technique                 | Example Problems                                                      | Difficulty | Note                                  |
| ------------------------- | --------------------------------------------------------------------- | ---------- | ------------------------------------- |
| Project 2D -> 1D          | [Points on a Line](https://codeforces.com/problemset/problem/103/B)   | Medium     | Reduces complexity                    |
| Treat features separately | [Skyline Problem](https://leetcode.com/problems/the-skyline-problem/) | Hard       | Separate dimensions / simplify object |

---

### **7. Symmetry & Grouping**

| Technique                      | Example Problems                                                            | Difficulty | Note                        |
| ------------------------------ | --------------------------------------------------------------------------- | ---------- | --------------------------- |
| Treat equivalent objects alike | [Graph Coloring](https://codeforces.com/problemset/problem/1139/B)          | Medium     | Reduce state space          |
| Exploit symmetry               | [Mirror Array Operations](https://codeforces.com/problemset/problem/1669/C) | Medium     | Avoid redundant computation |

---

### **8. Small Examples & Pattern Guessing**

| Technique               | Example Problems                                                              | Difficulty | Note                           |
| ----------------------- | ----------------------------------------------------------------------------- | ---------- | ------------------------------ |
| Test tiny inputs        | [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) | Medium     | Reveals hidden patterns        |
| Explore all small cases | [Permutation Cycles](https://codeforces.com/problemset/problem/499/B)         | Medium     | Helps predict general behavior |

---

### **9. Count, Don't Simulate**

| Technique                       | Example Problems                                                       | Difficulty | Note                                         |
| ------------------------------- | ---------------------------------------------------------------------- | ---------- | -------------------------------------------- |
| Combinatorial counting          | [Counting Rectangles](https://codeforces.com/problemset/problem/166/B) | Medium     | Count possibilities instead of brute-forcing |
| DP / math instead of simulation | [Unique Paths](https://leetcode.com/problems/unique-paths/)            | Medium     | Mathematical shortcuts                       |

---

### **10. Transform Operations**

| Technique                            | Example Problems                                                              | Difficulty | Note                                                 |
| ------------------------------------ | ----------------------------------------------------------------------------- | ---------- | ---------------------------------------------------- |
| Replace swaps with position tracking | [Minimum Swaps to Sort](https://leetcode.com/problems/minimum-swaps-to-sort/) | Medium     | Track positions instead of performing actual swaps   |
| Simplify operations                  | [Interval Addition](https://leetcode.com/problems/range-addition/)            | Medium     | Convert complicated operations to simpler arithmetic |

---

### **11. Problem Duality**

| Technique             | Example Problems                                                                             | Difficulty | Note                         |
| --------------------- | -------------------------------------------------------------------------------------------- | ---------- | ---------------------------- |
| Complement sets       | [Number of Subsets](https://leetcode.com/problems/count-of-subsets/)                         | Medium     | Solve “not A” instead of “A” |
| Min → Max / Max → Min | [Minimize Max Distance](https://leetcode.com/problems/minimize-max-distance-to-gas-station/) | Medium     | Flip perspective             |

---

### **12. Memory-less Thinking / State Reduction**

| Technique                 | Example Problems                                                           | Difficulty | Note                         |
| ------------------------- | -------------------------------------------------------------------------- | ---------- | ---------------------------- |
| Reduce DP state           | [House Robber III](https://leetcode.com/problems/house-robber-iii/)        | Medium     | Only store essential info    |
| Track key parameters only | [Game State Optimization](https://codeforces.com/problemset/problem/117/C) | Medium     | Avoid storing entire history |
