# Postgres Index Type

There are six kinds of indexes in Postgres,

1. B-Tree (Generalized)
   1. For general purposes
   2. `=`, `<`, `>,` `<=`, `>=`, `BETWEEN`, `IN`
2. GiST (Generalized Search Tree)
   1. Geometric Data Types in Postgres,
      1. POINT
      2. PATHS
      3. POLYGON
      4. BOX
      5. LINE
   2. `<->` (locations within a circle)
   3. Real-time and non real-time use cases
3. SP-GiST (Space Partitioned Generalized Search Tree)
   1. For non-balanced tree structures
   2. Non-balanced tree structures
4. GIN
   1. Generalized Inverted Index
   2. Full text searches
5. BRIN
   1. Block Range Index
6. Hash
   1. Hash based index for equality comparisons

---

Further GiST reading about use cases and questions about hot caches, write contention, caching strategies, in-memory, hot-spots, and top ranking.

Using Kafka, Redis, hot cache keys for fast reads -- background workers to update these cache keys really quickly.
