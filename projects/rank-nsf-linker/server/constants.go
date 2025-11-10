package main

// Environment flag constants
const (
	POPULATE_DB_FLAG = "POPULATE_DB"
	APP_ENV_FLAG     = "APP_ENV"
)

type PipelineStatus string
type DataPopulationPipelines string

// Pipeline Constants -- PIPELINE_POPULATE_POSTGRES
const (
	PIPELINE_STATUS_IN_PROGRESS PipelineStatus = "in-progress"
	PIPELINE_STATUS_COMPLETED   PipelineStatus = "completed"
	PIPELINE_STATUS_FAILED      PipelineStatus = "failed"
)

// Data Population Pipeline Constants
const (
	POPULATION_STATUS_SUCCEEDED PipelineStatus = "succeeded"
)

// Current Available Data Population Pipelines
const (
	PIPELINE_POPULATE_POSTGRES   DataPopulationPipelines = "populate_postgres"
	POPULATION_SUCCEEDED_MESSAGE DataPopulationPipelines = "population_succeeded"
)

// Service Discovery Routes
const (
	ELASTICSEARCH_SERVICE_ROUTE = "http://elasticsearch:9200"
	LOGGING_SERVICE_ROUTE       = "http://logging-service:5257"
)

// Postgres Constants
const (
	POSTGRES_DRIVER = "postgres"
)
