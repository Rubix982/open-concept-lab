package main

// Directory and file path constants
const (
	// Directories
	DATA_DIR             = "data"
	BACKUP_DIR           = "backup"
	TARGET_DIR           = "target"
	SCRIPTS_DIR          = "scripts"
	NSF_DATA_DIR         = "nsfdata"
	GEOCODING_DIR        = "geocoding"
	MIGRATIONS_DIR       = "migrations"
	SCRAPE_CACHE_DIR     = "scraped_cache"
	RESEARCH_SERVICE_DIR = "research_service"

	// Specific Files
	UNI_AGNST_WEBURL      = "universities_against_homepages.csv"
	COUNTRIES_FILENAME    = "countries.csv"
	CSRANKINGS_FILENAME   = "csrankings.csv"
	GEN_AUTHOR_FILENAME   = "generated-author-info.csv"
	GEOLOCATION_FILENAME  = "geolocation.csv"
	COUNTRY_INFO_FILENAME = "country-info.csv"
	EMBEDDER_SCRIPT       = "embedder.py"

	// URLs
	CSRANKINGS_RAW_GITHUB = "https://raw.githubusercontent.com/emeryberger/CSrankings/master/"
	NSFURLPrefix          = "https://www.nsf.gov/awardsearch/download?All=true&isJson=true&DownloadFileName="

	// Data Fetching Configuration
	NSFAwardsStartYear = 2025
	NSFAwardsEndYear   = 2025
)

var CSVURLs = []string{
	CSRANKINGS_FILENAME,
	GEN_AUTHOR_FILENAME,
	COUNTRIES_FILENAME,
	COUNTRY_INFO_FILENAME,
	GEOLOCATION_FILENAME,
}

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

// Environment Variable Names
const (
	ENV_POSTGRES_USER     = "POSTGRES_USER"
	ENV_POSTGRES_PASSWORD = "POSTGRES_PASSWORD"
	ENV_POSTGRES_DB_NAME  = "POSTGRES_DB_NAME"
	ENV_POSTGRES_HOST     = "POSTGRES_HOST"
	ENV_POSTGRES_PORT     = "POSTGRES_PORT"
	ENV_QDRANT_HOST       = "QDRANT_HOST"
	ENV_QDRANT_PORT       = "QDRANT_PORT"
)
