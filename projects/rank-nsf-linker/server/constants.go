package main

// Directory and file path constants
const (
	DATA_DIR       = "data"
	BACKUP_DIR     = "backup"
	TARGET_DIR     = "target"
	SCRIPTS_DIR    = "scripts"
	NSF_DATA_DIR   = "nsfdata"
	GEOCODING_DIR  = "geocoding"
	MIGRATIONS_DIR = "migrations"

	UNI_AGNST_WEBURL      = "universities_against_homepages.csv"
	COUNTRIES_FILENAME    = "countries.csv"
	CSRANKINGS_FILENAME   = "csrankings.csv"
	GEN_AUTHOR_FILENAME   = "generated-author-info.csv"
	GEOLOCATION_FILENAME  = "geolocation.csv"
	COUNTRY_INFO_FILENAME = "country-info.csv"

	CSRANKINGS_RAW_GITHUB = "https://raw.githubusercontent.com/emeryberger/CSrankings/master/"
	NSFURLPrefix          = "https://www.nsf.gov/awardsearch/download?All=true&isJson=true&DownloadFileName="

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
