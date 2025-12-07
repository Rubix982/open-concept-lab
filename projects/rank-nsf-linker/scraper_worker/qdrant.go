package scraperworker

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

func (q *QdrantClient) Upsert(id string, vector []float32, payload map[string]string) error {
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
