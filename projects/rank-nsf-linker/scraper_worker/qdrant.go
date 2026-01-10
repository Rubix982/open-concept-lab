package main

import (
	"context"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gocolly/colly/v2"
	"github.com/google/uuid"
	"github.com/qdrant/go-client/qdrant"
	"github.com/sirupsen/logrus"
)

type HealthChecker struct {
	mu               sync.RWMutex
	lastCheck        time.Time
	isHealthy        bool
	checkInterval    time.Duration
	consecutiveFails uint32
}

type CircuitBreaker struct {
	state           atomic.Uint32 // 0=closed, 1=open, 2=half-open
	failureCount    atomic.Uint32
	lastFailure     atomic.Int64 // Unix timestamp
	threshold       uint32
	timeout         time.Duration
	halfOpenTimeout time.Duration
}

type QdrantClient struct {
	client         *qdrant.Client
	collection     string
	healthCheck    *HealthChecker
	circuitBreaker *CircuitBreaker
}

// QdrantSearchResult represents a single search result from Qdrant
type QdrantSearchResult struct {
	ID      string
	Score   float32
	Payload map[string]interface{}
}

const (
	StateClosed = iota
	StateOpen
	StateHalfOpen
)

// Search performs a vector similarity search in Qdrant
func (q *QdrantClient) Search(queryVector []float32, limit uint64) ([]*QdrantSearchResult, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Perform search
	searchResult, err := q.client.Query(ctx, &qdrant.QueryPoints{
		CollectionName: q.collection,
		Query:          qdrant.NewQuery(queryVector...),
		Limit:          &limit,
		WithPayload:    qdrant.NewWithPayload(true), // Include all payload fields
	})
	if err != nil {
		return nil, fmt.Errorf("search failed: %w", err)
	}

	// Convert results
	results := make([]*QdrantSearchResult, 0, len(searchResult))
	for _, point := range searchResult {
		// Extract ID
		var pointID string
		if point.Id.GetUuid() != "" {
			pointID = point.Id.GetUuid()
		} else if point.Id.GetNum() != 0 {
			pointID = fmt.Sprintf("%d", point.Id.GetNum())
		}

		// Extract payload
		payload := make(map[string]interface{})
		if point.Payload != nil {
			for key, value := range point.Payload {
				payload[key] = extractPayloadValue(value)
			}
		}

		results = append(results, &QdrantSearchResult{
			ID:      pointID,
			Score:   point.Score,
			Payload: payload,
		})
	}

	return results, nil
}

// HasEmbeddings checks if there are any vectors for a given professor
func (q *QdrantClient) HasEmbeddings(professorName string) (bool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Filter by professor_name
	filter := &qdrant.Filter{
		Must: []*qdrant.Condition{
			{
				ConditionOneOf: &qdrant.Condition_Field{
					Field: &qdrant.FieldCondition{
						Key: "professor_name",
						Match: &qdrant.Match{
							MatchValue: &qdrant.Match_Keyword{Keyword: professorName},
						},
					},
				},
			},
		},
	}

	countResult, err := q.client.Count(ctx, &qdrant.CountPoints{
		CollectionName: q.collection,
		Filter:         filter,
	})

	if err != nil {
		return false, fmt.Errorf("failed to count points: %w", err)
	}

	return countResult > 0, nil
}

// SearchWithFilter performs a filtered vector search
func (q *QdrantClient) SearchWithFilter(queryVector []float32, limit uint64, filter *qdrant.Filter) ([]*QdrantSearchResult, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	searchResult, err := q.client.Query(ctx, &qdrant.QueryPoints{
		CollectionName: q.collection,
		Query:          qdrant.NewQuery(queryVector...),
		Limit:          &limit,
		Filter:         filter,
		WithPayload:    qdrant.NewWithPayload(true),
	})
	if err != nil {
		return nil, fmt.Errorf("filtered search failed: %w", err)
	}

	// Convert results (same as above)
	results := make([]*QdrantSearchResult, 0, len(searchResult))
	for _, point := range searchResult {
		var pointID string
		if point.Id.GetUuid() != "" {
			pointID = point.Id.GetUuid()
		} else if point.Id.GetNum() != 0 {
			pointID = fmt.Sprintf("%d", point.Id.GetNum())
		}

		payload := make(map[string]interface{})
		if point.Payload != nil {
			for key, value := range point.Payload {
				payload[key] = extractPayloadValue(value)
			}
		}

		results = append(results, &QdrantSearchResult{
			ID:      pointID,
			Score:   point.Score,
			Payload: payload,
		})
	}

	return results, nil
}

// Helper to extract values from Qdrant's Value type
func extractPayloadValue(value *qdrant.Value) interface{} {
	switch v := value.Kind.(type) {
	case *qdrant.Value_StringValue:
		return v.StringValue
	case *qdrant.Value_IntegerValue:
		return v.IntegerValue
	case *qdrant.Value_DoubleValue:
		return v.DoubleValue
	case *qdrant.Value_BoolValue:
		return v.BoolValue
	case *qdrant.Value_ListValue:
		list := make([]interface{}, len(v.ListValue.Values))
		for i, item := range v.ListValue.Values {
			list[i] = extractPayloadValue(item)
		}
		return list
	case *qdrant.Value_StructValue:
		m := make(map[string]interface{})
		for key, val := range v.StructValue.Fields {
			m[key] = extractPayloadValue(val)
		}
		return m
	default:
		return nil
	}
}

func NewQdrantClient() (*QdrantClient, error) {
	qHost := os.Getenv(ENV_QDRANT_HOST)
	qPort := os.Getenv(ENV_QDRANT_PORT)
	if qHost == "" {
		qHost = "qdrant-local"
	}
	if qPort == "" {
		qPort = "6334" // Default GRPC port for Qdrant is 6334
	}

	port, err := strconv.Atoi(qPort)
	if err != nil {
		return nil, fmt.Errorf("invalid QDRANT_PORT: %w", err)
	}

	client, err := qdrant.NewClient(&qdrant.Config{
		Host: qHost,
		Port: port,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to qdrant: %w", err)
	}

	q := &QdrantClient{
		client:     client,
		collection: "faculty_research",
		healthCheck: &HealthChecker{
			checkInterval: 30 * time.Second,
			isHealthy:     true,
			lastCheck:     time.Now(),
		},
		circuitBreaker: &CircuitBreaker{
			threshold:       5, // Open circuit after 5 failures
			timeout:         30 * time.Second,
			halfOpenTimeout: 10 * time.Second,
		},
	}

	// Log initial state
	q.LogCollectionInfo()

	return q, nil
}

func (q *QdrantClient) EnsureCollection(collyCtx *colly.Context, vectorSize uint64) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Try to get collection info instead of CollectionExists (more compatible)
	_, err := q.client.GetCollectionInfo(ctx, q.collection)
	if err == nil {
		logger.Infof(collyCtx, "Collection %s already exists", q.collection)
		return nil
	}

	// If collection doesn't exist, create it
	logger.Infof(collyCtx, "Creating collection %s with vector size %d", q.collection, vectorSize)
	err = q.client.CreateCollection(ctx, &qdrant.CreateCollection{
		CollectionName: q.collection,
		VectorsConfig: qdrant.NewVectorsConfig(&qdrant.VectorParams{
			Size:     vectorSize,
			Distance: qdrant.Distance_Cosine,
		}),
	})

	if err != nil {
		return fmt.Errorf("failed to create collection: %w", err)
	}

	logger.Infof(collyCtx, "✓ Collection %s created successfully", q.collection)
	return nil
}

func (q *QdrantClient) Upsert(collyCtx *colly.Context, vector []float32, payload map[string]interface{}) error {
	// 1. Health check first
	if err := q.healthCheck.Check(collyCtx, q.client, q.collection); err != nil {
		// Log only ONCE per unhealthy period
		if q.healthCheck.consecutiveFails == 1 {
			logger.WithError(collyCtx, err).Error("🚨 Qdrant connection unhealthy - skipping upserts")
		}
		return fmt.Errorf("qdrant unavailable: %w", err)
	}

	// 2. Circuit breaker wrapper
	return q.circuitBreaker.Call(collyCtx, func() error {
		return q.upsertInternal(collyCtx, vector, payload)
	})
}

func (q *QdrantClient) upsertInternal(collyCtx *colly.Context, vector []float32, payload map[string]interface{}) error {
	id := uuid.New().String()
	logger.WithFields(collyCtx, logrus.Fields{
		"component":   "qdrant",
		"operation":   "upsert",
		"collection":  q.collection,
		"point_id":    id,
		"vector_dims": len(vector),
	}).Trace("Starting Qdrant upsert operation")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Prepare payload
	qPayload := make(map[string]any)
	payloadKeys := make([]string, 0, len(payload))

	for k, v := range payload {
		qPayload[k] = v
		payloadKeys = append(payloadKeys, k)
	}

	logger.WithFields(collyCtx, logrus.Fields{
		"payload_keys":  payloadKeys,
		"payload_count": len(payload),
	}).Debug("Payload prepared for upsert")

	// Validate vector
	if len(vector) == 0 {
		logger.Error(collyCtx, "Empty vector provided for upsert")
		return fmt.Errorf("vector cannot be empty")
	}

	// Log vector stats for debugging
	var (
		minVal float32 = vector[0]
		maxVal float32 = vector[0]
		sum    float32 = 0
	)
	for _, v := range vector {
		if v < minVal {
			minVal = v
		}
		if v > maxVal {
			maxVal = v
		}
		sum += v
	}
	mean := sum / float32(len(vector))

	logger.WithFields(collyCtx, logrus.Fields{
		"vector_min":  minVal,
		"vector_max":  maxVal,
		"vector_mean": mean,
	}).Trace("Vector statistics computed")

	// Build point struct
	point := &qdrant.PointStruct{
		Id: qdrant.NewIDUUID(id),
		Vectors: &qdrant.Vectors{
			VectorsOptions: &qdrant.Vectors_Vector{
				Vector: &qdrant.Vector{
					Data: vector,
				},
			},
		},
		Payload: qdrant.NewValueMap(qPayload),
	}

	logger.WithFields(collyCtx, logrus.Fields{
		"timeout": "10s",
	}).Debug("Executing Qdrant upsert request")

	upsertStart := time.Now()
	shouldWaitOnResponse := true
	response, err := q.client.Upsert(ctx, &qdrant.UpsertPoints{
		CollectionName: q.collection,
		Points:         []*qdrant.PointStruct{point},
		Wait:           &shouldWaitOnResponse,
	})
	upsertDuration := time.Since(upsertStart)

	if err != nil {
		// Check error type
		errorType := "unknown"
		switch {
		case ctx.Err() == context.DeadlineExceeded:
			errorType = "timeout"
		case strings.Contains(err.Error(), "connection"):
			errorType = "connection"
		case strings.Contains(err.Error(), "not found"):
			errorType = "collection_not_found"
		case strings.Contains(err.Error(), "dimension"):
			errorType = "dimension_mismatch"
		}

		logger.WithFields(collyCtx, logrus.Fields{
			"error":       err.Error(),
			"error_type":  errorType,
			"duration_ms": upsertDuration.Milliseconds(),
		}).Error("Qdrant upsert failed")

		return fmt.Errorf("qdrant upsert failed (%s): %w", errorType, err)
	}

	// Log success details
	logger.WithFields(collyCtx, logrus.Fields{
		"duration_ms":     upsertDuration.Milliseconds(),
		"response_status": response.Status.String(),
		"operation_id":    response.OperationId,
	}).Debug("Qdrant upsert successful")

	// Additional validation: verify point was inserted
	if response.String() == "" {
		logger.Warn(collyCtx, "Qdrant upsert returned nil result (unexpected)")
	}

	logger.WithFields(collyCtx, logrus.Fields{
		"point_id":    point.Id,
		"duration_ms": upsertDuration.Milliseconds(),
	}).Info("✓ Vector upserted to Qdrant")

	// VERIFY: Immediately check if point exists
	ctx2, cancel2 := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel2()

	parsedUUID, err := uuid.Parse(id)
	if err != nil {
		logger.WithError(collyCtx, err).Error("Failed to parse UUID for verification")
		return fmt.Errorf("uuid parse failed: %w", err)
	}
	verifyPoints, err := q.client.Get(ctx2, &qdrant.GetPoints{
		CollectionName: q.collection,
		Ids: []*qdrant.PointId{
			qdrant.NewIDUUID(parsedUUID.String()),
		},
	})

	if err != nil {
		logger.WithError(collyCtx, err).Error("Failed to verify point after upsert")
		return err
	}

	if len(verifyPoints) == 0 {
		logger.Error(collyCtx, "🚨 Point not found immediately after upsert!")
		return fmt.Errorf("upsert verification failed: point not persisted")
	}

	logger.WithFields(collyCtx, logrus.Fields{
		"point_id": id,
	}).Debug("✓ Point verified in Qdrant")

	return nil
}

func (q *QdrantClient) LogCollectionInfo() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	qdrantCtx := colly.NewContext()
	logger.WithFields(qdrantCtx, logrus.Fields{
		"component":  "qdrant",
		"operation":  "log_collection_info",
		"collection": q.collection,
	})
	info, err := q.client.GetCollectionClusterInfo(ctx, q.collection)
	if err != nil {
		logger.WithError(qdrantCtx, err).Warn("Failed to fetch Qdrant collection info")
		return
	}

	logger.WithFields(qdrantCtx, logrus.Fields{
		"collection":    q.collection,
		"vectors_count": info.LocalShards,
		"peer_id":       info.PeerId,
		"remote_shards": info.RemoteShards,
		"shard_count":   info.ShardCount,
	}).Info("Qdrant collection status")
}

// Health check with exponential backoff
func (hc *HealthChecker) Check(collyCtx *colly.Context, client *qdrant.Client, collection string) error {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	// Don't check too frequently
	if time.Since(hc.lastCheck) < hc.checkInterval {
		if !hc.isHealthy {
			return fmt.Errorf("qdrant unhealthy (cached)")
		}
		return nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Simple health check: try to get collection info
	_, err := client.Get(ctx, &qdrant.GetPoints{
		CollectionName: collection,
		Ids:            []*qdrant.PointId{}, // Empty query
	})

	hc.lastCheck = time.Now()

	if err != nil {
		hc.consecutiveFails++
		hc.isHealthy = false

		// Exponential backoff
		backoff := time.Duration(math.Min(
			float64(30*time.Minute),
			float64(hc.checkInterval)*math.Pow(2, float64(hc.consecutiveFails)),
		))
		hc.checkInterval = backoff

		logger.WithFields(collyCtx, logrus.Fields{
			"consecutive_fails": hc.consecutiveFails,
			"next_check_in":     backoff.String(),
			"error":             err.Error(),
		}).Warn("⚠️  Qdrant health check failed")

		return fmt.Errorf("qdrant unhealthy: %w", err)
	}

	// Reset on success
	if hc.consecutiveFails > 0 {
		logger.WithFields(collyCtx, logrus.Fields{
			"after_fails": hc.consecutiveFails,
		}).Info("✓ Qdrant recovered")
	}

	hc.consecutiveFails = 0
	hc.isHealthy = true
	hc.checkInterval = 30 * time.Second

	return nil
}

// Circuit breaker logic
func (cb *CircuitBreaker) Call(collyCtx *colly.Context, fn func() error) error {
	state := cb.state.Load()

	switch state {
	case StateOpen:
		// Check if timeout elapsed
		lastFail := time.Unix(cb.lastFailure.Load(), 0)
		if time.Since(lastFail) > cb.timeout {
			// Try half-open
			cb.state.Store(StateHalfOpen)
			logger.WithFields(collyCtx, logrus.Fields{
				"state": "OPEN → HALF-OPEN",
			}).Info("🔄 Circuit breaker")
		} else {
			return fmt.Errorf("circuit breaker open (retry after %s)",
				cb.timeout-time.Since(lastFail))
		}

	case StateHalfOpen:
		// In half-open, allow ONE attempt
		err := fn()
		if err == nil {
			cb.state.Store(StateClosed)
			cb.failureCount.Store(0)
			logger.Info(collyCtx, "✓ Circuit breaker: HALF-OPEN → CLOSED")
			return nil
		}

		// Failed in half-open, back to open
		cb.state.Store(StateOpen)
		cb.lastFailure.Store(time.Now().Unix())
		logger.Warn(collyCtx, "❌ Circuit breaker: HALF-OPEN → OPEN")
		return err
	}

	// StateClosed - normal operation
	err := fn()
	if err != nil {
		count := cb.failureCount.Add(1)
		cb.lastFailure.Store(time.Now().Unix())

		if count >= cb.threshold {
			cb.state.Store(StateOpen)
			logger.WithFields(collyCtx, logrus.Fields{
				"failures": count,
			}).Warn("⚠️  Circuit breaker: CLOSED → OPEN")
		}
		return err
	}

	// Success - reset counter
	if cb.failureCount.Load() > 0 {
		cb.failureCount.Store(0)
	}
	return nil
}

func (q *QdrantClient) Close() {
	q.client.Close()
}
