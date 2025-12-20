package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/qdrant/go-client/qdrant"
)

type QdrantClient struct {
	client     *qdrant.Client
	collection string
}

// QdrantSearchResult represents a single search result from Qdrant
type QdrantSearchResult struct {
	ID      string
	Score   float32
	Payload map[string]interface{}
}

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

	return &QdrantClient{
		client:     client,
		collection: "faculty_research",
	}, nil
}

func (q *QdrantClient) EnsureCollection(vectorSize uint64) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Check if exists
	exists, err := q.client.CollectionExists(ctx, q.collection)
	if err != nil {
		return fmt.Errorf("failed to check collection existence: %w", err)
	}
	if exists {
		logger.Infof("Collection %s already exists", q.collection)
		return nil
	}

	// Create
	logger.Infof("Creating collection %s with vector size %d", q.collection, vectorSize)
	err = q.client.CreateCollection(ctx, &qdrant.CreateCollection{
		CollectionName: q.collection,
		VectorsConfig: qdrant.NewVectorsConfig(&qdrant.VectorParams{
			Size:     vectorSize,
			Distance: qdrant.Distance_Cosine,
		}),
	})
	return err
}

func (q *QdrantClient) Upsert(id string, vector []float32, payload map[string]interface{}) error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Ensure ID is UUID
	if id == "" {
		id = uuid.New().String()
	}

	// Prepare payload
	qPayload := make(map[string]any)
	for k, v := range payload {
		qPayload[k] = v
	}

	_, err := q.client.Upsert(ctx, &qdrant.UpsertPoints{
		CollectionName: q.collection,
		Points: []*qdrant.PointStruct{
			{
				Id:      qdrant.NewIDUUID(id),
				Vectors: qdrant.NewVectors(vector...),
				Payload: qdrant.NewValueMap(qPayload),
			},
		},
	})

	return err
}

func (q *QdrantClient) Close() {
	q.client.Close()
}
