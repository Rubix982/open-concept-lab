package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/google/uuid"
	pb "github.com/qdrant/go-client/qdrant"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type QdrantClient struct {
	client     pb.PointsClient
	collClient pb.CollectionsClient // Add CollectionsClient to manage collections
	conn       *grpc.ClientConn
	collection string
}

func NewQdrantClient() (*QdrantClient, error) {
	qHost := os.Getenv(ENV_QDRANT_HOST)
	qPort := os.Getenv(ENV_QDRANT_PORT)
	if qHost == "" {
		qHost = "qdrant-local"
	}
	if qPort == "" {
		qPort = "6333"
	}

	addr := fmt.Sprintf("%s:%s", qHost, qPort)
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to qdrant: %w", err)
	}

	return &QdrantClient{
		client:     pb.NewPointsClient(conn),
		collClient: pb.NewCollectionsClient(conn), // Initialize CollectionsClient
		conn:       conn,
		collection: "faculty_research",
	}, nil
}

func (q *QdrantClient) EnsureCollection(vectorSize uint64) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Check if exists
	_, err := q.collClient.Get(ctx, &pb.GetCollectionInfoRequest{
		CollectionName: q.collection,
	})
	if err == nil {
		logger.Infof("Collection %s already exists", q.collection)
		return nil
	}

	// Create
	logger.Infof("Creating collection %s with vector size %d", q.collection, vectorSize)
	_, err = q.collClient.Create(ctx, &pb.CreateCollection{
		CollectionName: q.collection,
		VectorsConfig: &pb.VectorsConfig{
			Config: &pb.VectorsConfig_Params{
				Params: &pb.VectorParams{
					Size:     vectorSize,
					Distance: pb.Distance_Cosine,
				},
			},
		},
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

	// Prepare payload (convert to Value)
	qPayload := make(map[string]*pb.Value)
	for k, v := range payload {
		qPayload[k] = &pb.Value{Kind: &pb.Value_StringValue{StringValue: v}}
	}

	point := &pb.PointStruct{
		Id: &pb.PointId{
			PointIdOptions: &pb.PointId_Uuid{Uuid: id},
		},
		Vectors: &pb.Vectors{
			VectorsOptions: &pb.Vectors_Vector{
				Vector: &pb.Vector{Data: vector},
			},
		},
		Payload: qPayload,
	}

	_, err := q.client.Upsert(ctx, &pb.UpsertPoints{
		CollectionName: q.collection,
		Points:         []*pb.PointStruct{point},
	})

	return err
}

func (q *QdrantClient) Close() {
	q.conn.Close()
}
