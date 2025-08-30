# PostgreSQL Index Types - Complete Guide

## Overview of PostgreSQL Index Access Methods

PostgreSQL supports 6 different index types, each optimized for specific data structures and query patterns:

1. **B-Tree** - Default, general-purpose index
2. **GiST** - Generalized Search Tree for geometric and custom data types  
3. **SP-GiST** - Space-Partitioned GiST for non-balanced tree structures
4. **GIN** - Generalized Inverted Index for composite values
5. **BRIN** - Block Range Index for very large, naturally ordered tables
6. **Hash** - Hash-based index for equality comparisons

- [PostgreSQL Index Types - Complete Guide](#postgresql-index-types---complete-guide)
  - [Overview of PostgreSQL Index Access Methods](#overview-of-postgresql-index-access-methods)
  - [1. B-Tree Indexes](#1-b-tree-indexes)
    - [**When to Use:**](#when-to-use)
    - [**Structure:**](#structure)
    - [**Examples:**](#examples)
    - [**Performance Characteristics:**](#performance-characteristics)
  - [2. GiST Indexes (Generalized Search Tree)](#2-gist-indexes-generalized-search-tree)
    - [**When to Use:**](#when-to-use-1)
    - [**Structure:**](#structure-1)
    - [**Examples:**](#examples-1)
    - [**Built-in Operator Classes:**](#built-in-operator-classes)
    - [GiST — Interview-level, real-world use-case scenarios](#gist--interview-level-real-world-use-case-scenarios)
      - [1) Geospatial nearest-neighbor for delivery / rideshare](#1-geospatial-nearest-neighbor-for-delivery--rideshare)
        - [Hot Zone, Write Contentions -- Detail](#hot-zone-write-contentions----detail)
          - [A — Caching hot zones (detailed)](#a--caching-hot-zones-detailed)
          - [1) High-level architectures (3 common approaches)](#1-high-level-architectures-3-common-approaches)
          - [A1: Precomputed tile cache (grid / H3 / geohash)](#a1-precomputed-tile-cache-grid--h3--geohash)
          - [A2: Hotspot-specific caches](#a2-hotspot-specific-caches)
          - [A3: Hierarchical cache with fallback](#a3-hierarchical-cache-with-fallback)
        - [2) Cache key design \& stored value](#2-cache-key-design--stored-value)
        - [1) Refresh / invalidation strategies](#1-refresh--invalidation-strategies)
          - [TTL (Time-to-Live)](#ttl-time-to-live)
          - [Sliding TTL (refresh-on-read)](#sliding-ttl-refresh-on-read)
          - [Proactive push updates (publish/subscribe)](#proactive-push-updates-publishsubscribe)
          - [Background periodic refresh](#background-periodic-refresh)
          - [Stale-while-revalidate (SWR)](#stale-while-revalidate-swr)
          - [On-demand + delta updates](#on-demand--delta-updates)
        - [4) Cache consistency model \& staleness tolerance](#4-cache-consistency-model--staleness-tolerance)
        - [5) Concrete example: Redis tile cache + incremental updates](#5-concrete-example-redis-tile-cache--incremental-updates)
        - [6) Handling borders and multi-tile queries](#6-handling-borders-and-multi-tile-queries)
      - [B — Handling write contention (detailed)](#b--handling-write-contention-detailed)
        - [1) Strategies to reduce index churn](#1-strategies-to-reduce-index-churn)
          - [B1: Only update when necessary (movement threshold)](#b1-only-update-when-necessary-movement-threshold)
          - [B2: Batch updates / write aggregation](#b2-batch-updates--write-aggregation)
          - [B3: Use an in-memory system for live updates + periodic sync](#b3-use-an-in-memory-system-for-live-updates--periodic-sync)
          - [B4: Partitioning by region](#b4-partitioning-by-region)
          - [B5: Use lower `fillfactor` on GiST index \& table](#b5-use-lower-fillfactor-on-gist-index--table)
          - [B6: Use MVCC-friendly patterns: append-only + compaction](#b6-use-mvcc-friendly-patterns-append-only--compaction)
          - [B7: Use an alternative index or storage for moving objects](#b7-use-an-alternative-index-or-storage-for-moving-objects)
        - [2) Concrete hybrid architecture (recommended)](#2-concrete-hybrid-architecture-recommended)
        - [3) Example: Redis GEO for live NN + Postgres for durable store](#3-example-redis-geo-for-live-nn--postgres-for-durable-store)
        - [4) Index maintenance \& bloat mitigation in Postgres](#4-index-maintenance--bloat-mitigation-in-postgres)
        - [5) Handling race conditions and correctness](#5-handling-race-conditions-and-correctness)
        - [Monitoring \& metrics you must track](#monitoring--metrics-you-must-track)
          - [Quick checklist / playbook](#quick-checklist--playbook)
        - [TL;DR (two-sentence summary)](#tldr-two-sentence-summary)
      - [2) Geofencing / polygon containment (e.g., advertising, zoning)](#2-geofencing--polygon-containment-eg-advertising-zoning)
      - [3) Time-range scheduling \& exclusion constraints (reservations, calendar)](#3-time-range-scheduling--exclusion-constraints-reservations-calendar)
      - [4) IP/network containment (access control, geolocation, threat hunting)](#4-ipnetwork-containment-access-control-geolocation-threat-hunting)
      - [5) Full-text search with ranking \& write-heavy tradeoffs](#5-full-text-search-with-ranking--write-heavy-tradeoffs)
      - [6) Similarity / fuzzy text search using `pg_trgm` (LIKE / ILIKE / similarity)](#6-similarity--fuzzy-text-search-using-pg_trgm-like--ilike--similarity)
      - [7) Hierarchical / bounding-box queries for CAD / games (collision detection)](#7-hierarchical--bounding-box-queries-for-cad--games-collision-detection)
      - [8) Custom data types / extensible operators (app-specific spatial or similarity types)](#8-custom-data-types--extensible-operators-app-specific-spatial-or-similarity-types)
      - [9) Temporal \& multidimensional queries (combining time + geometry)](#9-temporal--multidimensional-queries-combining-time--geometry)
      - [10) Exclusion constraints for complex business rules (beyond ranges)](#10-exclusion-constraints-for-complex-business-rules-beyond-ranges)
    - [Are GiST indexes only valuable for real-time systems?](#are-gist-indexes-only-valuable-for-real-time-systems)
      - [Why GiST applies beyond real-time](#why-gist-applies-beyond-real-time)
      - [When GiST is *especially* good for non-real-time (concrete scenarios)](#when-gist-is-especially-good-for-non-real-time-concrete-scenarios)
      - [When you might *not* pick GiST (and better alternatives for batch)](#when-you-might-not-pick-gist-and-better-alternatives-for-batch)
      - [Practical patterns for using GiST in non-real-time jobs](#practical-patterns-for-using-gist-in-non-real-time-jobs)
      - [Interview-level comparative decision matrix (real-time vs batch)](#interview-level-comparative-decision-matrix-real-time-vs-batch)
      - [Interview talking points (ready-to-say)](#interview-talking-points-ready-to-say)
      - [Quick examples for non-real-time tasks](#quick-examples-for-non-real-time-tasks)
      - [Cross-case decision points (GiST vs alternatives)](#cross-case-decision-points-gist-vs-alternatives)
      - [Performance, tuning, and pitfalls to mention](#performance-tuning-and-pitfalls-to-mention)
      - [Possible interview questions you should be ready to answer](#possible-interview-questions-you-should-be-ready-to-answer)
  - [3. SP-GiST Indexes (Space-Partitioned GiST)](#3-sp-gist-indexes-space-partitioned-gist)
    - [**When to Use:**](#when-to-use-2)
    - [**Structure:**](#structure-2)
    - [**Examples:**](#examples-2)
    - [**Built-in Operator Classes:**](#built-in-operator-classes-1)
  - [4. GIN Indexes (Generalized Inverted Index)](#4-gin-indexes-generalized-inverted-index)
    - [**When to Use:**](#when-to-use-3)
    - [**Structure:**](#structure-3)
    - [**Examples:**](#examples-3)
    - [**GIN Tips and Tricks:**](#gin-tips-and-tricks)
    - [When GIN on `jsonb` is a good idea](#when-gin-on-jsonb-is-a-good-idea)
      - [Quick examples](#quick-examples)
      - [Tradeoffs \& gotchas (say these in an interview)](#tradeoffs--gotchas-say-these-in-an-interview)
      - [Decision checklist (short)](#decision-checklist-short)
      - [How to validate in practice](#how-to-validate-in-practice)
      - [Interview talking points (concise)](#interview-talking-points-concise)
  - [5. BRIN Indexes (Block Range Index)](#5-brin-indexes-block-range-index)
    - [**When to Use:**](#when-to-use-4)
    - [**Structure:**](#structure-4)
    - [**Examples:**](#examples-4)
    - [**BRIN Maintenance:**](#brin-maintenance)
  - [6. Hash Indexes](#6-hash-indexes)
    - [**When to Use:**](#when-to-use-5)
    - [**Structure:**](#structure-5)
    - [**Examples:**](#examples-5)
    - [**Hash Index Limitations:**](#hash-index-limitations)
  - [Index Selection Strategy](#index-selection-strategy)
    - [**Decision Matrix:**](#decision-matrix)
    - [**Real-World Examples:**](#real-world-examples)
  - [Advanced Index Techniques](#advanced-index-techniques)
    - [**Partial Indexes:**](#partial-indexes)
    - [**Expression Indexes:**](#expression-indexes)
    - [**Multi-Column Indexes:**](#multi-column-indexes)
  - [Performance Monitoring](#performance-monitoring)
    - [**Index Usage Statistics:**](#index-usage-statistics)
    - [**Index Size Analysis:**](#index-size-analysis)
  - [Index Maintenance](#index-maintenance)
    - [**REINDEX Operations:**](#reindex-operations)
    - [**Index Bloat Detection:**](#index-bloat-detection)
  - [Interview Questions](#interview-questions)
    - [**Common Index Questions:**](#common-index-questions)

---

## 1. B-Tree Indexes

### **When to Use:**

- Equality and range queries (`=`, `<`, `>`, `BETWEEN`, `IN`)
- Sorting operations (`ORDER BY`)
- Pattern matching with anchored patterns (`LIKE 'prefix%'`)
- Most general-purpose scenarios

### **Structure:**

```text
Root Node: [50, 100]
         /      |      \
   [10,30]   [60,80]   [120,150]
  /   |   \   /  |  \    /   |   \
[5] [15] [35] [55][75][90] [110][130][160]
```

### **Examples:**

```sql
-- Default B-tree index
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_orders_date ON orders (created_at);

-- Multi-column B-tree
CREATE INDEX idx_user_status ON users (status, created_at);

-- Partial B-tree index
CREATE INDEX idx_active_users ON users (email) WHERE status = 'active';

-- Expression index
CREATE INDEX idx_lower_email ON users (LOWER(email));
```

### **Performance Characteristics:**

- **Time Complexity:** O(log n) for searches
- **Space Overhead:** ~2-3x the indexed data size
- **Concurrent Access:** Excellent (page-level locking)

---

## 2. GiST Indexes (Generalized Search Tree)

### **When to Use:**

- Geometric data (points, lines, polygons, circles)
- Full-text search
- Network addresses (inet/cidr)
- Range types
- Custom data types with spatial properties

### **Structure:**

GiST organizes data in a tree where:

- Internal nodes contain predicates (bounding boxes)
- Leaf nodes contain the actual indexed values
- Supports overlapping regions (unlike B-tree)

### **Examples:**

```sql
-- Geometric queries
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    coordinates POINT
);
CREATE INDEX idx_locations_gist ON locations USING GIST (coordinates);

-- Query: Find points within a circle
SELECT * FROM locations 
WHERE coordinates <-> point(0,0) < 10;

-- Full-text search
CREATE INDEX idx_documents_fts ON documents USING GIST (to_tsvector('english', content));

-- Network addresses  
CREATE INDEX idx_network_gist ON access_log USING GIST (client_ip inet_ops);

-- Range types
CREATE INDEX idx_reservations_period ON reservations USING GIST (time_range);
```

### **Built-in Operator Classes:**

- `point_ops`, `box_ops`, `polygon_ops`, `circle_ops`
- `inet_ops`, `cidr_ops`
- `range_ops` for range types
- `tsvector_ops` for full-text search

### GiST — Interview-level, real-world use-case scenarios

Below are compact, realistic interview-style scenarios you can talk through. Each one shows the **problem**, **why GiST fits**, a short **SQL example**, and **tradeoffs / tuning** points you can discuss in an interview.

---

#### 1) Geospatial nearest-neighbor for delivery / rideshare

**Problem:** Given a fleet of drivers, find the nearest available drivers to a rider in under 100ms.
**Why GiST:** GiST supports KNN searches (`<->`) on geometric types (point) and efficiently prunes search with bounding regions. Good for read-heavy geo queries with spatial operators.
**SQL:**

```sql
CREATE TABLE drivers (id serial PRIMARY KEY, location geometry(Point, 4326), status text);
CREATE INDEX idx_drivers_loc_gist ON drivers USING GIST (location);
-- KNN
SELECT id, ST_Distance(location, ST_SetSRID(ST_Point(lon, lat),4326)) AS dist
FROM drivers
WHERE status = 'available'
ORDER BY location <-> ST_SetSRID(ST_Point(lon, lat),4326)
LIMIT 10;
```

**Interview points:** CRS choice (use geography for meters), clustering for locality, caching hot zones, fallback when many updates (write contention). GiST may be preferred over SP-GiST/GiN for complex spatial queries.

##### Hot Zone, Write Contentions -- Detail

###### A — Caching hot zones (detailed)

**What is a "hot zone"?**

A geographic area with very high query volume (airport, stadium, busy downtown). Instead of doing an exact DB nearest-neighbor query every request, you keep a precomputed, quickly-accessible result for that area (e.g., top N available drivers) and serve it from cache. This reduces DB read load and latency.

###### 1) High-level architectures (3 common approaches)

###### A1: Precomputed tile cache (grid / H3 / geohash)

- Divide map into tiles (fixed grid, geohash, or H3 hexes).
- For each tile, cache a list of nearest available drivers (IDs + last-known location + timestamp).
- On query, determine tile(s) covering user location, return cached list and optionally do a lightweight re-rank.

Pros: simple, deterministic; cache keys are small.
Cons: edge cases at tile borders, staleness.

###### A2: Hotspot-specific caches

- Identify hotspots (manually, analytics, or by tracking traffic) and keep specialized caches for each hotspot: e.g., `hot:airport:DXB:top20`.
- Refresh frequency can be higher than other tiles.

Pros: targeted optimization for the busiest areas.
Cons: needs hotspot detection & management.

###### A3: Hierarchical cache with fallback

- Level 1: in-process memory for extremely hot tiles (millisecond access).
- Level 2: distributed cache (Redis) for general tile cache.
- Level 3: fallback to Postgres GiST query for cold/uncached tiles.

Pros: fastest path for hottest queries and robust fallback.
Cons: more infra complexity.

---

##### 2) Cache key design & stored value

Example key patterns:

- `drivers:tile:{geohash}` -> value: JSON list of `{driver_id, lon, lat, status, last_seen_ts}` sorted by precomputed distance.
- `hot:zone:{zone_id}` -> value: cached top-20 driver IDs (with timestamps).

Stored payloads:

- Minimal data required for the immediate response (driver\_id, distance bucket, ETA estimate optional).
- Keep timestamps so client can decide to re-validate if too old.

---

##### 1) Refresh / invalidation strategies

###### TTL (Time-to-Live)

- Simple: set TTL = e.g., 2s, 5s, or 10s for hotspots.
- Pros: simple.
- Cons: extra DB hits on expiry and wasted updates if no queries.

###### Sliding TTL (refresh-on-read)

- If a key is read frequently, extend TTL to keep it hot.
- Implementation: on GET, if TTL < X, extend TTL by Y.

###### Proactive push updates (publish/subscribe)

- Drivers update their location to an ingest stream (Kafka). A background worker updates cached tiles for nearby tiles and pushes updates to Redis.
- Very responsive and reduces DB load.

###### Background periodic refresh

- Every N seconds refresh popular tiles by recomputing `ORDER BY <->` for that tile and writing to cache.

###### Stale-while-revalidate (SWR)

- Serve cached value (even slightly stale), and asynchronously refresh in background. Perfect for low-latency UX with eventual correction.

###### On-demand + delta updates

- Use small messages of driver movement to update the affected tile caches incrementally instead of recomputing whole tile lists.

---

##### 4) Cache consistency model & staleness tolerance

- Rideshare can tolerate small staleness (drivers move seconds between updates). Aim for **soft real-time**: cached data < 5s old for hotspots.
- Design systems assuming **eventual consistency**: cached top-N are approximate; on user select, re-check driver availability with a transaction before confirming assignment.

---

##### 5) Concrete example: Redis tile cache + incremental updates

**Cache schema**

- Key: `tile:{geohash}`
- Value: Sorted Set (Redis ZSET) where score = precomputed distance to tile center or last update timestamp.
- Commands:

  - `ZADD tile:abc123 score driver_id`
  - `ZREVRANGE tile:abc123 0 19 WITHSCORES` → top 20 drivers

**Update flow**

1. Driver client sends location to API.
2. API writes location to Redis (ZADD into few nearby tiles) and to an append-only log (Kafka) for offline processing / historical writes.
3. Periodic worker compacts Redis keys (remove stale driver entries by TTL or by last\_seen < T).

**Read flow**

1. Rider query -> compute geohash `h` -> `ZREVRANGE tile:h 0 19`
2. Map driver IDs to small cached driver records (`HMGET drivers:{id}`) or fetch a few from DB if driver details missing.
3. Optionally: call Postgres to re-rank top 20 by exact `ST_Distance` if strict correctness required, else confirm availability upon assignment.

---

##### 6) Handling borders and multi-tile queries

- When user is near tile boundary, query current tile plus 8 neighbors and merge results by distance. This avoids missing nearby drivers in neighboring tiles.

---

#### B — Handling write contention (detailed)

Write contention arises because every driver location update means updating a row and the spatial index (GiST). If updates are frequent, index maintenance and row-level/page-level contention can slow reads/writes and bloat indexes.

##### 1) Strategies to reduce index churn

###### B1: Only update when necessary (movement threshold)

- Only write to DB/cache when location change exceeds X meters (e.g., 50m). This reduces write volume.
- SQL example:

```sql
-- pseudocode: update only if moved more than 50 meters
WITH prior AS (
  SELECT id, location FROM drivers WHERE id = :id
)
UPDATE drivers
SET location = :new_geom, last_seen = now()
FROM prior
WHERE drivers.id = :id
  AND ST_Distance(prior.location::geography, :new_geom::geography) > 50;
```

This reduces index writes by ignoring tiny GPS jitter.

###### B2: Batch updates / write aggregation

- Collect frequent updates in a fast-write staging table or in-memory store and apply periodic bulk updates to the main table (every 1-5 seconds).
- Staging table/unlogged table reduces write amplification.
- Use `INSERT ... ON CONFLICT (id) DO UPDATE SET location = EXCLUDED.location` for upserts in bulk.

###### B3: Use an in-memory system for live updates + periodic sync

- Use Redis / Memcached / specialized in-memory store to receive location updates; Postgres remains the durable store and is updated asynchronously.
- This offloads heavy update traffic from the DB and avoids GiST churn.

###### B4: Partitioning by region

- Partition drivers table by region or geohash prefix. Each partition has its own index — updates only affect a single partition/index reducing contention hotspots.
- Example:

```sql
CREATE TABLE drivers (id bigint primary key, location geometry(Point,4326), region text) PARTITION BY LIST (region);
-- partitions: drivers_nyc, drivers_dxb, etc.
```

###### B5: Use lower `fillfactor` on GiST index & table

- Reduce page splits and hot page contention. Set fillfactor to leave free space for in-place updates.

```sql
ALTER TABLE drivers SET (fillfactor = 70);
CREATE INDEX idx_drivers_loc_gist ON drivers USING GIST (location) WITH (fillfactor = 70);
```

Note: For GiST, `fillfactor` on the index can be set to reduce page splits — check your PG version docs.

###### B6: Use MVCC-friendly patterns: append-only + compaction

- Store immutable location events in an append-only table, and periodically create a compacted view of latest locations. The compacted view is used for reads and rebuilt periodically. This avoids frequent updates on a single row.

###### B7: Use an alternative index or storage for moving objects

- For extremely high update rates, consider using specialized spatial stores optimized for moving objects (in-memory index, GeoMesa, or vector/ANN libs). Postgres is fine up to moderate write rates, but above some scale, hybrid infra is better.

---

##### 2) Concrete hybrid architecture (recommended)

**Small-to-medium scale (<=100k drivers, moderate updates)**:

- Use Postgres primary with GiST index for location.
- Use Redis for caching hotspots & recent updates.
- Apply movement threshold updates (ignore tiny movements).
- Monitor index bloat and VACUUM regularly; tune `maintenance_work_mem` and `autovacuum`.

**Large scale (hundreds of thousands to millions, high update rate)**:

- Use in-memory geo store as the source-of-truth for near-instant queries (Redis GEO or specialized ANN). Persist events to Kafka.
- Periodically (every 1-5s) batch-sync latest positions to Postgres (staging -> upsert).
- Postgres supports analytical queries, historical queries, and durable backups; Redis handles real-time lookups and hotspots.
- For critical consistency (assignment), always recheck availability in Postgres or the authoritative system during confirmation.

---

##### 3) Example: Redis GEO for live NN + Postgres for durable store

**Write path (driver location update)**

1. Driver -> API -> update Redis:

```bash
GEOADD drivers_geo lon lat driver:{id}
HSET driver:{id} lon lon lat lat last_seen ts
EXPIRE driver:{id} 30
```

2. Push event to Kafka `driver_updates` for background sync worker.

**Read path (nearest drivers)**

1. `GEOSEARCH drivers_geo BYFENCE ...` or `GEOADIUS` to get N nearest IDs fast.
2. Optionally fetch driver details from `HGETALL driver:{id}`.
3. On assignment, do `SELECT ... FROM drivers WHERE id = ? FOR UPDATE` in Postgres to confirm and reserve.

---

##### 4) Index maintenance & bloat mitigation in Postgres

- Monitor `pg_stat_user_indexes` and `pg_relation_size` for index size.
- Run `VACUUM`/`ANALYZE` regularly; tune autovacuum thresholds for high-update tables.
- Use `REINDEX CONCURRENTLY` during off-peak if index bloat becomes severe.
- Consider `pg_repack` if lots of dead tuples accumulate, to reduce bloat without long locks.

---

##### 5) Handling race conditions and correctness

- Because caches are eventually consistent, always **finalize assignments with a DB transaction** that `SELECT FOR UPDATE` the driver row and check `status='available'` before confirming. If not available, reassign from the next candidate.
- Use optimistic fallback & retry policy: if you reserve a driver but they accept elsewhere, the transaction will fail and you retry with next candidate.

---

##### Monitoring & metrics you must track

- Cache hit ratio (Redis GET hits vs misses) for hotspot keys.
- Query p95/p99 latency for nearest-neighbor DB queries.
- Number of GiST index updates per second and index size growth.
- `pg_stat_activity` wait events and `pg_locks` to detect contention.
- Driver update rate (updates/sec) and percent of updates ignored by movement threshold.
- Error/retry rates on assignment transactions (indicates stale caches).

---

###### Quick checklist / playbook

1. **Start simple**: GiST + small Redis cache for hotspots + movement threshold.
2. **Measure**: hits, misses, update rate, index bloat, latency.
3. **If write contention grows**: add batching or move updates to Redis + async sync.
4. **If read volume grows**: add tile caching & multi-level cache (in-process -> Redis).
5. **Always final-commit in DB**: confirm assignment with `SELECT ... FOR UPDATE`.
6. **Tune**: fillfactor, autovacuum, maintenance\_work\_mem, `gin_pending_list_limit` if using GIN elsewhere.

---

##### TL;DR (two-sentence summary)

Use caching (tile/geohash/hotspot) and a hierarchical approach (in-process → Redis → Postgres) to serve very-low-latency queries for hot zones, with SWR or proactive refresh to keep results fresh. For write contention, reduce index churn (threshold updates, batching, partitioning), offload real-time updates to an in-memory store, and sync periodically to Postgres for durability and analytical workloads — always recheck availability in a DB transaction when assigning a driver.

---

#### 2) Geofencing / polygon containment (e.g., advertising, zoning)

**Problem:** Quickly find which polygonal zones contain a point (user location → which campaign to show).
**Why GiST:** GiST can index polygons and uses bounding boxes for overlap tests, then rechecks exact containment.
**SQL:**

```sql
CREATE TABLE zones (id serial PRIMARY KEY, geom geometry(Polygon,4326), campaign_id int);
CREATE INDEX idx_zones_gist ON zones USING GIST (geom);
SELECT campaign_id FROM zones
WHERE ST_Contains(geom, ST_SetSRID(ST_Point(lon, lat),4326));
```

**Tradeoffs:** Bounding-box recheck causes false positives (cheap). If many tiny polygons overlap, index selectivity drops. Consider tiling/clustering or partitioning by region.

---

#### 3) Time-range scheduling & exclusion constraints (reservations, calendar)

**Problem:** Prevent overlapping bookings for a room/resource.
**Why GiST:** GiST supports range types and can back `EXCLUSION` constraints to enforce "no overlapping ranges" atomically.
**SQL:**

```sql
CREATE TABLE bookings (
  id serial PRIMARY KEY,
  room_id int,
  period tsrange
);
CREATE INDEX idx_bookings_period_gist ON bookings USING GIST (room_id, period);
ALTER TABLE bookings
  ADD CONSTRAINT no_overlap EXCLUDE USING GIST (room_id WITH =, period WITH &&);
```

**Interview points:** GiST + `&&` lets DB enforce constraints without heavy application logic. Explain VACUUM implications for range indexes and how long transactions can block constraint checks.

---

#### 4) IP/network containment (access control, geolocation, threat hunting)

**Problem:** Fast lookup: which network block covers an IP, or find overlapping CIDR ranges.
**Why GiST:** Operator classes like `inet_ops` let GiST index `inet/cidr` and use containment/overlap operators efficiently.
**SQL:**

```sql
CREATE TABLE nets (id serial, net cidr);
CREATE INDEX idx_nets_gist ON nets USING GIST (net inet_ops);
SELECT * FROM nets WHERE net >>= '192.168.1.10';
```

**Tradeoffs:** For pure equality lookups a B-Tree or hash could be fine; GiST shines when using ranges/containment semantics.

---

#### 5) Full-text search with ranking & write-heavy tradeoffs

**Problem:** Text search where you need flexible ranking or combine text search with spatial/range operators, and better write characteristics than GIN.
**Why GiST:** `tsvector` can be indexed with GiST (`tsvector_ops`) — slower than GIN for pure read, but smaller and better for write-heavy workloads and for combined queries (e.g., FTS + geometry).
**SQL:**

```sql
CREATE INDEX idx_docs_fts_gist ON documents USING GIST (to_tsvector('english', content));
SELECT id, ts_rank_cd(to_tsvector(content), plainto_tsquery('cloud')) AS rank
FROM documents WHERE to_tsvector('english',content) @@ plainto_tsquery('cloud')
ORDER BY rank DESC LIMIT 20;
```

**Interview nuance:** Usually GIN is preferred for fast lookups; explain when GiST is a reasonable alternative (smaller index, cheaper updates, combined operator queries).

---

#### 6) Similarity / fuzzy text search using `pg_trgm` (LIKE / ILIKE / similarity)

**Problem:** Implement "fuzzy" name search that supports similarity ranking and fast LIKE `'%foo%'`.
**Why GiST:** `pg_trgm` provides `gist_trgm_ops`. GiST can be smaller and offer faster writes than GIN for some workloads and supports KNN similarity.
**SQL:**

```sql
CREATE INDEX idx_users_name_trgm_gist ON users USING GIST (name gist_trgm_ops);
SELECT id, similarity(name, 'jonathan') AS sim
FROM users
WHERE name % 'jonathan'
ORDER BY sim DESC LIMIT 10;
```

**Points to mention:** GIN often outperforms for pure trigram lookup; GiST supports index ordering useful for top-N similarity.

---

#### 7) Hierarchical / bounding-box queries for CAD / games (collision detection)

**Problem:** Quickly find objects whose bounding boxes intersect a query box (e.g., in a game engine or CAD app).
**Why GiST:** GiST indexes rectangles/boxes and supports overlap tests efficiently; it is good for dynamic datasets with frequent inserts/updates.
**SQL:**

```sql
CREATE TABLE sprites (id serial, bbox box);
CREATE INDEX idx_sprites_bbox_gist ON sprites USING GIST (bbox);
SELECT id FROM sprites WHERE bbox && box '((x1,y1),(x2,y2))';
```

**Interview angle:** Talk about brush heuristics, bucket sizes, false positives and how to recheck exact geometry in application code.

---

#### 8) Custom data types / extensible operators (app-specific spatial or similarity types)

**Problem:** You created a domain-specific type (e.g., chemical substructure fingerprints) and need indexable operators.
**Why GiST:** GiST is extensible — you can implement custom compress/consistent/picksplit methods and register operator classes. Used heavily in PostGIS and other extensions.
**Example (conceptual):**

```sql
-- register a custom operator class for molecule type and create gist index
CREATE INDEX idx_molecules_gist ON molecules USING GIST (fingerprint gist_molecule_ops);
```

**Interview takeaways:** Describe API for GiST operator support (`consistent`, `union`, `compress`, `decompress`, `picksplit`) and why this is powerful for domain-specific accelerations.

---

#### 9) Temporal & multidimensional queries (combining time + geometry)

**Problem:** Query: "What assets were inside region X during time interval Y?" (spatio-temporal queries)
**Why GiST:** GiST can index composite columns (e.g., `BOX` + `tsrange`) or support composite operator classes to prune on multiple dimensions and combine spatial + temporal operators.
**SQL sketch:**

```sql
CREATE TABLE events (id serial, region geometry(Polygon,4326), period tsrange);
CREATE INDEX idx_events_gist ON events USING GIST (region, period);
-- Query uses ST_Intersects(region, the_geom) AND period && tsrange(...)
```

**Tradeoffs:** Composite GiST indexes can be powerful but watch selectivity; sometimes multi-index strategies and `AND`-merge are better.

---

#### 10) Exclusion constraints for complex business rules (beyond ranges)

**Problem:** Enforce "no two records with same owner and overlapping geometry" or "no overlapping time+resource combos."
**Why GiST:** Exclusion constraints using GiST can atomically enforce complex invariants at the DB level.
**SQL:**

```sql
ALTER TABLE resource_usage
  ADD CONSTRAINT no_overlap_geom EXCLUDE USING GIST (resource_id WITH =, geom WITH &&);
```

**Interview point:** Explain how enforcement occurs during insert/update and how it interacts with concurrent transactions.

### Are GiST indexes only valuable for real-time systems?

Short answer: **GiST use-cases are *not* limited to real-time systems.** GiST shines anytime you need index support for *overlap/containment/nearest-neighbor* semantics or custom operator classes — whether queries run millisecond-latency in a live service **or** as part of nightly batch jobs, interactive analytics, ETL, or data-cleaning pipelines. Below I'll show why, when it's appropriate for non-real-time workloads, what alternatives to consider, and give interview-ready talking points and examples for offline/batch contexts.

#### Why GiST applies beyond real-time

- **Same operator semantics**: Containment (`&&`, `@>`, `ST_Contains`), overlap, and KNN are useful for batch analytics, historical spatial joins, deduplication, and validation — not just live lookups.
- **Repetitive ad-hoc queries**: Data analysts running repeated spatial joins or time+space filters on the same dataset benefit from an index even if queries run hourly or nightly.
- **Enforcing constraints at load time**: `EXCLUDE USING GIST` enforces invariants (e.g., no overlapping reservations, no overlapping geometries for same resource) during bulk load or ETL validation.
- **Data-wrangling and dedupe**: Fuzzy matching and similarity (e.g., `gist_trgm_ops`) are often used in offline deduping, record linkage, and data-quality jobs.
- **Smaller index size than alternatives**: For large batch jobs where disk I/O dominates, a smaller GiST index sometimes reduces overall job time vs using a heavier index or external engine.
- **Extensibility**: Custom GiST operator classes used by extensions (PostGIS) are inherently useful in analytics and offline processing.

#### When GiST is *especially* good for non-real-time (concrete scenarios)

1. **Cadastral / historical map analysis**

   - Use-case: nightly jobs that compute which land parcels intersect infrastructure changes across millions of geometry records.
   - Why GiST: spatial pruning speeds repeated spatial joins and aggregates.

2. **Bulk import with exclusion constraints**

   - Use-case: load millions of bookings but ensure no overlapping intervals per room.
   - Strategy: load into staging table, then `INSERT ... SELECT` into production where GiST-backed `EXCLUDE` enforces integrity (or rebuild index after streaming load).

3. **Ad-hoc large-scale spatial joins for reporting**

   - Use-case: weekly reports of assets inside regions over past year.
   - Why GiST: dramatically reduces candidate set for expensive ST\_Intersects checks.

4. **Offline fuzzy deduplication & record linkage**

   - Use-case: nightly dedupe of customer records using trigram similarity.
   - Why GiST: `gist_trgm_ops` supports similarity KNN to find candidate pairs quickly.

5. **Batch route/coverage optimization**

   - Use-case: precompute service coverage maps for next-day planning across city tiles.
   - Why GiST: index bounding-box overlap queries across many geometry objects reduces compute.

#### When you might *not* pick GiST (and better alternatives for batch)

- **Pure equality/range on scalar columns** → **B-tree** (faster lookups, ordering).
- **Massive multi-valued text/JSONB read-heavy analytics** → **GIN** (much faster for inverted lookups).
- **Huge append-only time-series analytics** → **BRIN** (tiny index size, ideal for correlated data).
- **Extremely write-heavy streaming ingest where any index kills throughput** → consider **drop+rebuild index** after batch ingest, or use staging tables.

#### Practical patterns for using GiST in non-real-time jobs

**A. Build concurrently after bulk load**

```sql
-- load data into staging without index for fast writes
CREATE TABLE geom_staging AS SELECT * FROM source LIMIT 0;
-- bulk copy into geom_staging...
-- build GiST on production table concurrently
CREATE INDEX CONCURRENTLY idx_prod_geom_gist ON prod_table USING GIST (geom);
```

**B. Staging + validated insert for exclusion constraints**

```sql
-- stage loads
CREATE TABLE bookings_stage AS SELECT * FROM incoming;
-- validate and insert, letting GiST exclusion catch overlaps
INSERT INTO bookings (room_id, period)
SELECT room_id, period FROM bookings_stage;
-- on conflict / failure: analyze and fix bad rows in stage
```

**C. Use materialized views for repeated heavy reports**

- Precompute aggregates using GiST-backed filters to speed daily reports; refresh materialized views off-peak.

**D. Rebuild index periodically for stability**

```sql
REINDEX INDEX CONCURRENTLY idx_big_geom_gist;
```

Useful after lots of updates/deletes from ETL.

#### Interview-level comparative decision matrix (real-time vs batch)

| Requirement                     |            Real-time |                  Batch/offline | Best index/approach                                       |
| ------------------------------- | -------------------: | -----------------------------: | --------------------------------------------------------- |
| KNN nearest neighbor            | ✅ low-latency needed | ✅ repeated queries benefit too | GiST (geometry) or specialized ANN libs                   |
| Overlap/containment checks      |                    ✅ |                 ✅ (mass joins) | GiST (spatial/range)                                      |
| Full-text read-heavy searches   |                    ✅ |                              ✅ | GIN usually better than GiST for read-heavy text          |
| Fuzzy dedupe overnight          |              ✖️ or ✅ |                        ✅ ideal | GiST (trgm) or GIN(trgm) depending on write/read          |
| Massive historical time windows |                   ✖️ |                              ✅ | BRIN for correlation; GiST if operator semantics required |

#### Interview talking points (ready-to-say)

- "GiST is chosen for its *operator semantics* (overlap/containment/KNN), not because the workload is real-time. That makes it equally useful for interactive dashboards, nightly analytics, ETL validation, and archival queries."
- "For heavy ingestion pipelines, build indexes after load (CONCURRENTLY) or use staging tables; GiST can be expensive to maintain during high write loads."
- "If the job is strictly inverted lookups on huge multi-valued text/JSON, GIN is usually superior — but GiST can be preferable when index size and update costs matter or when combining spatial/text operators."
- "EXCLUDE USING GIST is powerful for batch integrity checks — you can use it to enforce complex business rules during a controlled bulk load rather than trying to implement checks in application code."
- "For very large append-only datasets where queries are time-correlated, BRIN often wins for batch analytics — but GiST is still needed if your filters require geometry or general overlap semantics."

#### Quick examples for non-real-time tasks

**Spatial join for nightly report**

```sql
-- GiST speeds ST_Intersects when executed at scale
CREATE INDEX idx_zones_geom_gist ON zones USING GIST (geom);
CREATE INDEX idx_assets_geom_gist ON assets USING GIST (geom);

-- nightly report
INSERT INTO daily_zone_counts (zone_id, count)
SELECT z.id, count(a.*)
FROM zones z
JOIN assets a ON ST_Intersects(z.geom, a.geom)
GROUP BY z.id;
```

**Offline dedupe with trigram**

```sql
CREATE INDEX idx_customers_name_trgm_gist ON customers USING GIST (name gist_trgm_ops);

-- candidate pairs (batch)
SELECT c1.id, c2.id, similarity(c1.name, c2.name) AS sim
FROM customers c1
JOIN customers c2 ON c1.id < c2.id
WHERE c1.name % c2.name
ORDER BY sim DESC;
```

---

#### Cross-case decision points (GiST vs alternatives)

- **GiST** → best for spatial, range, overlap, custom operator needs, and when you want smaller index + better write behavior than GIN.
- **GIN** → best for multi-valued inverted indexes (JSONB, arrays, full-text read-heavy).
- **SP-GiST** → better for partitioned spaces, prefix/patricia-style lookups (large text prefixes, IP quadtrees).
- **B-Tree** → equality and range on scalar columns, ordering.

In interviews, state why GiST is chosen *for the operator semantics* (overlap, containment, KNN) not just because it's "spatial".

---

#### Performance, tuning, and pitfalls to mention

- **Recheck step (false positives):** GiST uses bounding predicates — index may return candidates that must be rechecked by exact operator; mention `IndexOnlyScan` limits.
- **Write amplification:** GiST can be more expensive than B-Tree per entry but often cheaper than GIN for updates — explain write/read tradeoffs.
- **Fillfactor & vacuum:** For lots of updates, use lower `fillfactor` and ensure regular `VACUUM`/`ANALYZE`.
- **GiST index size:** Typically smaller than GIN for some types; discuss storage vs lookup speed tradeoff.
- **Parallelism & planner behavior:** Planner chooses index based on cost estimates and statistics — show awareness that multi-predicate queries may not always pick GiST unless selective.
- **Operator class choice:** Use correct operator class (`gist_trgm_ops`, `inet_ops`, `tsvector_ops`) to enable GiST advantages.

---

#### Possible interview questions you should be ready to answer

1. Why would you choose GiST over GIN for full-text search?
2. Explain the GiST recheck — what happens after index candidate retrieval?
3. How would you enforce "no overlapping reservations" — show both application and DB approaches.
4. How does KNN work with GiST? What operators enable it?
5. When would SP-GiST be a better choice than GiST?
6. How do GiST operator classes interact with `EXCLUSION` constraints?
7. Describe the lifecycle of a GiST index entry during an `UPDATE`.
8. How do you tune GiST indexes for heavy update workloads?

---

## 3. SP-GiST Indexes (Space-Partitioned GiST)

### **When to Use:**

- Non-balanced tree structures
- Quad-trees, k-d trees, radix trees
- Phone numbers, IP addresses
- Text with prefix searching

### **Structure:**

SP-GiST uses space partitioning:

- Each internal node represents a space partition
- Better for data with natural clustering
- More flexible tree structures than GiST

### **Examples:**

```sql
-- IP addresses (quad-tree partitioning)
CREATE INDEX idx_ip_spgist ON access_log USING SPGIST (client_ip);

-- Text prefix searches (radix tree)
CREATE INDEX idx_phone_spgist ON users USING SPGIST (phone_number text_ops);

-- 2D points (quad-tree)
CREATE INDEX idx_coordinates_spgist ON locations USING SPGIST (coordinates);

-- Range queries
SELECT * FROM access_log WHERE client_ip << '192.168.0.0/16';
```

### **Built-in Operator Classes:**

- `inet_ops` - IP addresses
- `text_ops` - Text/varchar
- `point_ops` - 2D points
- `range_ops` - Range types

---

## 4. GIN Indexes (Generalized Inverted Index)

### **When to Use:**

- Multi-value columns (arrays, JSON, full-text)
- "Contains" queries (`@>`, `?`, `?&`, `?|`)
- Full-text search
- JSONB queries

### **Structure:**

```
GIN stores:
- Each unique component value as a key
- List of rows containing that value
- Optimized for queries like "which rows contain value X"
```

### **Examples:**

```sql
-- Array columns
CREATE INDEX idx_tags_gin ON articles USING GIN (tags);
SELECT * FROM articles WHERE tags @> ARRAY['postgresql', 'database'];

-- JSONB columns
CREATE INDEX idx_metadata_gin ON products USING GIN (metadata);
SELECT * FROM products WHERE metadata @> '{"color": "red"}';
SELECT * FROM products WHERE metadata ? 'warranty';

-- Full-text search
CREATE INDEX idx_content_gin ON documents USING GIN (to_tsvector('english', content));
SELECT * FROM documents WHERE to_tsvector('english', content) @@ to_tsquery('database & performance');

-- Composite types
CREATE INDEX idx_address_gin ON users USING GIN (address);
```

### **GIN Tips and Tricks:**

```sql
-- Faster updates with fastupdate
CREATE INDEX idx_tags_gin ON articles USING GIN (tags) WITH (fastupdate = on);

-- Reduce index size with gin_pending_list_limit
SET gin_pending_list_limit = '16MB';

-- Optimize maintenance_work_mem for GIN builds
SET maintenance_work_mem = '1GB';
```

Short answer — **yes, usually**. If you have `JSONB` columns and your workload is read-heavy (especially containing containment/exists/type queries), a **GIN** index is the go-to choice — but there are important caveats and alternatives you should mention in interviews.

Below is a compact, interview-ready explanation with examples, tradeoffs, and decision rules.

### When GIN on `jsonb` is a good idea

- Your queries use **containment** or **existence** semantics, e.g.:
  - `WHERE metadata @> '{"color":"red"}'`
  - `WHERE metadata ? 'warranty'` or `?&`, `?|`
    GIN is built as an inverted index and answers these fast.
- Workload is **read-heavy** (many lookups, relatively fewer updates).
- You need to index **multi-valued or nested** structures (arrays, keys at arbitrary paths) rather than a single scalar extracted value.

#### Quick examples

Default (general-purpose) GIN:

```sql
CREATE INDEX idx_products_metadata_gin ON products USING GIN (metadata);
-- query example
SELECT * FROM products WHERE metadata @> '{"color":"red"}';
SELECT * FROM products WHERE metadata ? 'warranty';
```

Smaller/faster for containment-only (`@>`) — `jsonb_path_ops` operator class:

```sql
-- only supports containment-style queries but is more compact / faster for them
CREATE INDEX idx_products_metadata_gin_path ON products USING GIN (metadata jsonb_path_ops);
```

If you only query one JSON key frequently (equality/range on that key), prefer a btree expression index:

```sql
CREATE INDEX idx_products_status ON products ((metadata->>'status'));
-- Query:
SELECT * FROM products WHERE metadata->>'status' = 'active';
```

#### Tradeoffs & gotchas (say these in an interview)

- **Write cost:** GIN indexes are heavier to update. If you have frequent writes/updates to the JSONB column, the index can slow inserts/updates (posting list maintenance).
- **Index size:** GIN can be large (many keys tokenized into postings). `jsonb_path_ops` is more compact but supports fewer operators.
- **Index-only scan behaviour:** GIN/inverted indexes may still require heap rechecks for visibility unless the visibility map allows index-only scans — check planner behavior.
- **Fastupdate / pending list:** GIN has a "pending list" optimization (`fastupdate`) to speed writes; tune `gin_pending_list_limit` and `maintenance_work_mem` if creating or rebuilding big GINs.
- **Partial & expression indexes:** If only a subset of rows is queried a lot, use partial GINs to reduce size and write cost:

  ```sql
  CREATE INDEX idx_products_metadata_gin_partial ON products USING GIN (metadata)
  WHERE metadata ? 'warranty';
  ```

- **Mixed workloads:** For heavy writes + occasional reads, consider staging (load without index → build index once), or use expression/btree indexes for hot keys instead of a full GIN.

#### Decision checklist (short)

1. Are your queries mainly `@>` / `?` / `?&` / `?|` → **Yes** → GIN (default or `jsonb_path_ops` for containment-only).
2. Are queries mostly equality on a **single JSON path** → **btree expression** on `(jsonb->>'key')`.
3. Is the table tiny? → Index overhead may not be worth it.
4. Very heavy writes? → Consider partial/index-after-load or narrower expression indexes.
5. Want multicolumn search that includes JSON + scalar columns? → Use appropriate multi-index strategies (partial GIN + B-tree on other columns or expression indexes) and test with `EXPLAIN`.

#### How to validate in practice

- Create the index `CONCURRENTLY` on production to avoid long locks:

  ```sql
  CREATE INDEX CONCURRENTLY idx_products_metadata_gin ON products USING GIN (metadata);
  ```

- Measure with `EXPLAIN (ANALYZE, BUFFERS)` and inspect `pg_stat_user_indexes` (`idx_scan`) and `pg_relation_size(indexrelid)` to validate benefit vs cost.

- Monitor `pg_stat_all_tables` and latency to ensure write slowdown is acceptable.

#### Interview talking points (concise)

- "Use GIN for `jsonb` when queries are containment/existence heavy and reads dominate. For equality on a single key, use a btree expression index instead — it’s much cheaper and more selective. For heavy ingestion, consider staging and creating the GIN index after load or using partial indexes. Also mention `jsonb_path_ops` (smaller/faster for `@>` only) vs the default operator class (broader operator support)."

---

## 5. BRIN Indexes (Block Range Index)

### **When to Use:**

- Very large tables (TB+) with natural ordering
- Time-series data
- Append-only tables
- Data warehouse scenarios

### **Structure:**

```
BRIN stores summary info for blocks:
Block 1-128: min=100, max=500
Block 129-256: min=480, max=900  
Block 257-384: min=850, max=1200

Tiny index size but requires sequential correlation
```

### **Examples:**

```sql
-- Time-series data
CREATE INDEX idx_metrics_time_brin ON metrics USING BRIN (timestamp);

-- Large append-only tables
CREATE INDEX idx_logs_date_brin ON application_logs USING BRIN (log_date);

-- Multi-column BRIN
CREATE INDEX idx_sensor_data_brin ON sensor_readings USING BRIN (timestamp, sensor_id);

-- Custom page range
CREATE INDEX idx_custom_brin ON large_table USING BRIN (id) WITH (pages_per_range = 64);
```

### **BRIN Maintenance:**

```sql
-- Summarize new pages
SELECT brin_summarize_new_values('idx_metrics_time_brin');

-- Check BRIN index efficiency
SELECT schemaname, tablename, attname, correlation 
FROM pg_stats 
WHERE schemaname = 'public' AND correlation > 0.8;
```

---

## 6. Hash Indexes

### **When to Use:**

- Only equality comparisons (`=`)
- High-selectivity columns
- When you never need range queries or sorting

### **Structure:**

```
Hash function maps values to buckets:
hash('john') → bucket 42
hash('jane') → bucket 17
hash('bob')  → bucket 101

Fast O(1) lookups but no ordering
```

### **Examples:**

```sql
-- Simple hash index
CREATE INDEX idx_user_hash_id ON users USING HASH (user_id);

-- Only useful for equality
SELECT * FROM users WHERE user_id = 12345;

-- NOT useful for:
-- SELECT * FROM users WHERE user_id > 1000; -- No range support
-- SELECT * FROM users ORDER BY user_id;     -- No ordering
```

### **Hash Index Limitations:**

- No range queries
- No sorting support
- Not WAL-logged in older PostgreSQL versions
- Generally B-tree is preferred unless specific use case

---

## Index Selection Strategy

### **Decision Matrix:**

| Query Type | Best Index | Second Choice |
|------------|------------|---------------|
| `=`, `<`, `>`, `BETWEEN` | B-tree | Hash (= only) |
| Geometric queries | GiST | SP-GiST |
| Array `@>`, `&&` | GIN | - |
| JSONB queries | GIN | - |
| Full-text search | GIN | GiST |
| Time-series (large) | BRIN | B-tree |
| IP address ranges | SP-GiST | GiST |
| Prefix matching | SP-GiST | B-tree |

### **Real-World Examples:**

```sql
-- E-commerce product search
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price DECIMAL,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP,
    location POINT
);

-- Different index strategies:
CREATE INDEX idx_products_btree ON products (price, created_at);           -- B-tree for ranges/sorting
CREATE INDEX idx_products_gin_tags ON products USING GIN (tags);          -- GIN for array queries  
CREATE INDEX idx_products_gin_json ON products USING GIN (metadata);      -- GIN for JSONB
CREATE INDEX idx_products_gist_loc ON products USING GIST (location);     -- GiST for geometric
CREATE INDEX idx_products_brin_time ON products USING BRIN (created_at);  -- BRIN if huge table

-- Query examples:
SELECT * FROM products WHERE price BETWEEN 100 AND 500;                   -- Uses B-tree
SELECT * FROM products WHERE tags @> ARRAY['electronics'];                -- Uses GIN
SELECT * FROM products WHERE metadata @> '{"brand": "Apple"}';            -- Uses GIN  
SELECT * FROM products WHERE location <-> point(0,0) < 1000;             -- Uses GiST
SELECT * FROM products WHERE created_at > '2023-01-01';                   -- Uses BRIN (if correlated)
```

---

## Advanced Index Techniques

### **Partial Indexes:**

```sql
-- Index only active users
CREATE INDEX idx_active_users ON users (email) WHERE status = 'active';

-- Index only recent orders
CREATE INDEX idx_recent_orders ON orders (customer_id) WHERE created_at > '2023-01-01';
```

### **Expression Indexes:**

```sql
-- Case-insensitive searches
CREATE INDEX idx_lower_email ON users (LOWER(email));

-- Function-based indexes
CREATE INDEX idx_email_domain ON users (split_part(email, '@', 2));

-- JSON path indexes
CREATE INDEX idx_user_age ON users ((metadata->>'age')::int);
```

### **Multi-Column Indexes:**

```sql
-- Order matters in B-tree!
CREATE INDEX idx_user_compound ON users (status, created_at, email);

-- Good for:
-- WHERE status = 'active'
-- WHERE status = 'active' AND created_at > '2023-01-01'  
-- WHERE status = 'active' AND created_at > '2023-01-01' AND email LIKE 'john%'

-- Not optimal for:
-- WHERE created_at > '2023-01-01'  -- Skips first column
-- WHERE email = 'john@example.com' -- Skips first two columns
```

---

## Performance Monitoring

### **Index Usage Statistics:**

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 AND schemaname = 'public';
```

### **Index Size Analysis:**

```sql
-- Index sizes
SELECT schemaname, tablename, indexname, 
       pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
ORDER BY pg_relation_size(indexrelid) DESC;

-- Table vs index sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
       pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size
FROM pg_stat_user_tables;
```

---

## Index Maintenance

### **REINDEX Operations:**

```sql
-- Rebuild single index
REINDEX INDEX idx_users_email;

-- Rebuild all indexes on table
REINDEX TABLE users;

-- Concurrent reindex (PostgreSQL 12+)
REINDEX INDEX CONCURRENTLY idx_users_email;
```

### **Index Bloat Detection:**

```sql
-- Estimate index bloat
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
       CASE WHEN pg_relation_size(indexrelid) = 0 THEN 0
            ELSE (pgstatindex(indexrelid)).avg_leaf_density 
       END as avg_leaf_density
FROM pg_stat_user_indexes
WHERE schemaname = 'public';
```

---

## Interview Questions

### **Common Index Questions:**

1. **"When would you choose GIN over GiST for full-text search?"**
   - GIN: Better for read-heavy workloads, faster queries, larger index
   - GiST: Better for write-heavy workloads, smaller index, slower queries

2. **"How do you optimize a query on a 10TB time-series table?"**
   - Use BRIN index if data has temporal correlation
   - Partition by time ranges
   - Consider column store extensions

3. **"Design indexes for a social media platform."**
   - User posts: B-tree on (user_id, created_at)
   - Hashtags: GIN on tags array
   - Location: GiST on coordinates  
   - Full-text: GIN on content

4. **"Why might a B-tree index not be used?"**
   - Query doesn't match index column order
   - Functions applied to columns without expression index
   - Type conversion issues
   - Cost-based optimizer chooses sequential scan

---

*This guide covers PostgreSQL's rich indexing ecosystem. Each index type solves specific problems - understanding when to use each one is key to database performance optimization.*
