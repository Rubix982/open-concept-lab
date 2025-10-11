# Geometric/Mathematical Algorithms

- [Geometric/Mathematical Algorithms](#geometricmathematical-algorithms)
  - [Number Theory](#number-theory)
  - [Computational Algebra](#computational-algebra)
  - [2D Geometry](#2d-geometry)
  - [3D Geometry](#3d-geometry)
  - [Advanced Topics](#advanced-topics)
  - [References](#references)
    - [General](#general)
    - [Algorithm Based](#algorithm-based)

## Number Theory

- **Fundamental operations**: Euclid's algorithm for GCD (and LCM via GCD), extended GCD (solve linear Diophantine equations) [^1] [^gcd]; fast exponentiation (binary exponentiation) for large powers [^1] [^binary-exp].
- **Primes & factorization**: Sieve of Eratosthenes (and its variants like segmented or linear sieve) to list primes [^2] [^sieve]; probabilistic and deterministic primality tests (e.g. Miller-Rabin) and integer factorization methods (e.g. Pollard's Rho) [^2] [^factorization].
- **Number-theoretic functions**: Euler's totient function, Möbius function, divisor-count and sum-of-divisors functions [^3]; Legendre's formula for prime factors of factorial, Catalan numbers and other special sequences.
- **Modular arithmetic**: Modular inverse (via extended GCD or Fermat's little theorem), modular exponentiation (fast pow) [^1] [^mod-inv]; Chinese Remainder Theorem (CRT) [^crt] and Garner's algorithm to solve systems of congruences [^4] [^garners]; discrete logarithm (baby-step/giant-step) for solving ax ≡ b (mod m) [^4] [^discrete-log].
- **Combinatorial number theory**: Computation of n choose k mod p using Lucas's theorem or Fermat's theorem; Catalan numbers, Stirling numbers, and other binomial/multinomial combinatorics (often via dynamic programming or Lucas/multiplicative formulas).
- **Bitwise/Integer techniques**: Bit manipulation tricks (like `__builtin_popcount`, bit masks) and enumerating submasks for subset convolution [^5] [^bitmask]; arbitrary-precision arithmetic (big integers) when dealing with very large values [^5] [^bigint].

## Computational Algebra

- **Polynomial operations**: Fast polynomial multiplication via FFT or NTT in `O(n log n)` [^6] [^fft]; long polynomial division and modular arithmetic on polynomials. Multipoint evaluation and interpolation (Lagrange, Newton) for polynomial values or coefficients [^7] [^poly].
- **Fast Fourier Transform (FFT/NTT)**: Use FFT (or Number-Theoretic Transform modulo prime) to perform convolutions and multiply polynomials/large integers in `O(n log n)` [^6]. Important for problems involving cyclic convolutions or large-scale multiplications.
- **Formal power series**: Operations on series (inverse, logarithm, exponentiation of power series) using divide-and-conquer or Hensel lifting techniques (see cp-algorithms "Operations on polynomials and series" [^6] [^poly-series]).
- **Linear algebra**: Gaussian elimination for solving linear systems and computing determinants [^8] [^gauss]; matrix exponentiation for linear recurrences (fast doubling or binary exponentiation of matrices); computing matrix rank [^8]. These are used in solving recurrences, count walks in graphs, etc.
- **Advanced arithmetic**: Fast algorithms for exponentiation of large exponents (modular exponentiation by binary splitting), CRT-based reconstruction of integers, and radix/Gray-code manipulations [^9]. (For instance, Garner's algorithm [^10] is often used in conjunction with CRT.) [^1]

## 2D Geometry

- **Basic primitives**: Point/vector operations (addition, subtraction), dot product, cross product and orientation tests (clockwise/ccw) for area tests. These form the foundation of most geometry problems (e.g. computing projection lengths or checking collinearity).
- **Line and segment**: Intersection of two lines (solve linear equations), checking if two segments intersect (orientation tests + bounding boxes) [^11]; distance from point to line or segment. Useful building blocks for geometry problems [^geom-primitives].
- **Circle operations**: Intersecting a line and circle, intersecting two circles, and finding common tangents between circles [^12]; computing arc lengths or sector areas when needed [^circle].
- **Polygon geometry**: Polygon area using the shoelace formula (oriented area of triangle sum) [^13]; checking if a point lies inside a polygon (ray-casting or winding rule, or binary-search in a convex polygon) [^13] [^polygon]; Minkowski sum of convex polygons; lattice-point formulas like Pick's theorem [^13].
- **Convex hull**: Compute the convex hull of a set of points using Graham's scan or Andrew's monotone chain in `O(n log n)` [^14] (the smallest convex polygon containing all points). These algorithms are asymptotically optimal for this problem [^14]. Common variants include whether to include collinear boundary points [^cht].
- **Rotating calipers**: Once a convex hull is built, use rotating calipers to find the diameter (farthest pair of points), width, or minimum-area enclosing rectangle in linear time. This technique also applies to problems like finding the minimum distance between convex shapes.
- **Convex hull trick**: A data-structure technique (often Li Chao tree or deque optimization) for dynamic programming with lines, finding max/min of many linear functions efficiently [^15] [^convex-hull] .
- **Sweep-line methods**: Bentley-Ottmann style sweep-line to detect any intersecting pair of segments; sweep-line (divide and conquer) for closest-pair-of-points in `O(n log n)` [^16] [^sweep]; line sweeping for other ordering problems.
- **Voronoi/Delaunay**: Construct Voronoi diagrams or Delaunay triangulations (e.g. by Fortune's algorithm or incremental triangulation) [^16]. Useful for nearest-neighbor and proximity problems [^delaunay].
- **Other constructs**: Half-plane intersection (find polygon common to a set of half-planes) [^17]; computing the minimum enclosing circle (smallest circle covering all points) [^17]; handling Manhattan-distance geometry (rotating coordinates to reduce to 45°-rotated plane) [^17] [^half-plane].

## 3D Geometry

- **3D primitives**: 3D point/vector operations, dot and cross product in 3D, and the scalar triple product (volume of parallelepipeds). These are used to compute angles, areas, and volumes in 3D.
- **Planes and lines**: Represent a plane by a normal vector and offset, and a line by point-direction. Compute intersections: line-plane intersection, plane-plane intersection (line), and the distance from a point to a plane or line. Also compute angles between planes, or between line and plane.
- **Polyhedra**: Algorithms for 3D convex hull (e.g. Quickhull or incremental) to find the convex polyhedron of points; computing volume of a tetrahedron or general polyhedron (via tetrahedral decomposition). Check if a point lies inside a 3D convex hull using half-space tests.
- **Rotations and transforms**: 3D rotations (using rotation matrices or quaternions) and 3D geometry transforms (if relevant to problems). (Note: explicit references for 3D-specific CP algorithms were not found in our sources, but these are natural extensions of the 2D primitives.)

## Advanced Topics

- **Numerical methods**: Binary and ternary search for real-valued optimization or unimodal functions [^18]; Newton's method (Newton-Raphson) for solving equations in continuous math [^18]; Simpson's rule for numerical integration [^18]. Simulated annealing and other randomized optimization techniques may appear in very hard problems [^ternary].
- **Inclusion-exclusion and counting**: Advanced counting techniques (principle of inclusion-exclusion, fast subset convolution) and group-theory-based counting (Burnside's lemma) are often important for combinatorial math problems. (While not geometry per se, these are key mathematical tools in contests.)
- **Miscellaneous optimization**: Advanced algorithms like Hungarian algorithm for assignment, Kirchhoff's matrix-tree theorem for counting spanning trees, etc., while more combinatorial, rely on mathematical properties. Fast greedy or DP optimizations (divide-and-conquer DP, convex/ Knuth opt) involve underlying math [^dp-opt].
- **Data structure usage in math problems**: Sometimes math problems use data structures (Fenwick tree, segment tree) for speed, or bitsets for fast convolution. These bridge algorithmic and mathematical skills.

Each topic above is widely used in contests (ICPC, Codeforces, AtCoder, etc.) and is discussed in competitive programming references [^14] [^6] [^1] [^13].

---

## References

### General

[^1]: [1](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^2]: [2](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^3]: [3](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^4]: [4](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^5]: [5](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^9]: [9](Binary Exponentiation - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/binary-exp.html>)
[^6]: [6](Operations on polynomials and series - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/polynomial.html>)
[^7]: [7](Operations on polynomials and series - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/polynomial.html>)
[^11]: [11](Operations on polynomials and series - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/polynomial.html>)
[^12]: [12](Operations on polynomials and series - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/polynomial.html>)
[^13]: [13](Operations on polynomials and series - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/polynomial.html>)
[^8]: [8](Discrete Root - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/discrete-root.html>)
[^15]: [15](Discrete Root - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/discrete-root.html>)
[^16]: [16](Discrete Root - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/discrete-root.html>)
[^17]: [17](Discrete Root - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/discrete-root.html>)
[^18]: [18](Discrete Root - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/discrete-root.html>)
[^10]: [10](Garner's Algorithm - Algorithms for Competitive Programming <https://cp-algorithms.com/algebra/garners-algorithm.html>)
[^14]: [14](Convex hull construction - Algorithms for Competitive Programming <https://cp-algorithms.com/geometry/convex-hull.html>)

### Algorithm Based

[^gcd]: [GCD & Extended Euclidean Algorithm](https://cp-algorithms.com/algebra/euclid.html)  
[^binary-exp]: [Binary Exponentiation](https://cp-algorithms.com/algebra/binary-exp.html)  
[^sieve]: [Prime Sieve](https://cp-algorithms.com/algebra/sieve-of-eratosthenes.html)  
[^factorization]: [Primality & Factorization](https://cp-algorithms.com/algebra/primality_tests.html)  
[^mod-inv]: [Modular Inverse](https://cp-algorithms.com/algebra/module-inverse.html)  
[^crt]: [Chinese Remainder Theorem](https://cp-algorithms.com/algebra/chinese-remainder-theorem.html)  
[^garners]: [Garner's Algorithm](https://cp-algorithms.com/algebra/garners-algorithm.html)  
[^discrete-log]: [Discrete Logarithm](https://cp-algorithms.com/algebra/discrete-log.html)  
[^bitmask]: [Bitmask Techniques](https://cp-algorithms.com/algebra/all-submasks.html)  
[^bigint]: [Arbitrary Precision Arithmetic](https://cp-algorithms.com/algebra/big-integer.html)  
[^fft]: [Fast Fourier Transform](https://cp-algorithms.com/algebra/fft.html)  
[^poly]: [Polynomial Interpolation](https://cp-algorithms.com/algebra/polynomial.html)  
[^poly-series]: [Power Series Operations](https://cp-algorithms.com/algebra/polynomial.html#operations-on-series)  
[^gauss]: [Gaussian Elimination](https://cp-algorithms.com/linear_algebra/linear-system-gauss.html)  
[^geom-primitives]: [Basic Geometry Primitives](https://cp-algorithms.com/geometry/basic-geometry.html)  
[^circle]: [Circle Geometry](https://cp-algorithms.com/geometry/circle-circle-intersection.html)  
[^polygon]: [Polygon Geometry](https://cp-algorithms.com/geometry/oriented-triangle-area.html)  
[^convex-hull]: [Convex Hull Construction](https://cp-algorithms.com/geometry/convex-hull.html)  
[^cht]: [Convex Hull Trick](https://cp-algorithms.com/geometry/convex_hull_trick.html)  
[^sweep]: [Closest Pair of Points](https://cp-algorithms.com/geometry/closest-points.html)  
[^delaunay]: [Delaunay Triangulation](https://cp-algorithms.com/geometry/delaunay.html)  
[^half-plane]: [Half-Plane Intersection](https://cp-algorithms.com/geometry/halfplane-intersection.html)  
[^ternary]: [Ternary Search](https://cp-algorithms.com/num_methods/ternary_search.html)  
[^dp-opt]: [DP Optimization Techniques](https://cp-algorithms.com/dp/divide-and-conquer-dp.html)  
