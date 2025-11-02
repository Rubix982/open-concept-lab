package main

// Environment flag constants
const (
	POPULATE_DB_FLAG = "POPULATE_DB"
	APP_ENV_FLAG     = "APP_ENV"
)

type PipelineStatus string

// Pipeline Constants
const (
	PIPELINE_STATUS_IN_PROGRESS PipelineStatus = "in-progress"
	PIPELINE_STATUS_COMPLETED   PipelineStatus = "completed"
	PIPELINE_STATUS_FAILED      PipelineStatus = "failed"
)

type DataPopulationPipelines string

// Current Available Data Population Pipelines
const (
	PIPELINE_POPULATE_POSTGRES DataPopulationPipelines = "populate_postgres"
)

// Service Discovery Routes
const (
	ELASTICSEARCH_SERVICE_ROUTE = "http://elasticsearch:9200"
	LOGGING_SERVICE_ROUTE       = "http://logging-service:5257"
)
