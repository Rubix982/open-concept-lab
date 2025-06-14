from pathlib import Path

# Constants for the file downloads, outputs, artifacts
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR = ROOT_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)
TARGET_DIR = ROOT_DIR / "target"
TARGET_DIR.mkdir(exist_ok=True)
NSF_DATA_DIR = DATA_DIR / "nsfdata"
NSF_DATA_DIR.mkdir(exist_ok=True)

CS_RANKINGS_FILENAME = "csrankings.csv"
GEN_AUTHOR_FILENAME = "generated-author-info.csv"
COUNTRIES_FILENAME = "countries.csv"
COUNTRY_INFO_FILENAME = "country-info.csv"
GEOLOCATION_FILENAME = "geolocation.csv"

CS_RANKINGS_FILE = DATA_DIR / CS_RANKINGS_FILENAME
GEN_AUTHOR_FILE = DATA_DIR / GEN_AUTHOR_FILENAME
COUNTRIES_FILE = DATA_DIR / COUNTRIES_FILENAME
COUNTRY_INFO_FILE = DATA_DIR / COUNTRY_INFO_FILENAME
GEOLOCATION_FILE = DATA_DIR / GEOLOCATION_FILENAME

# Backup Files
BACKUP_COUNTRY_INFO_FILE = BACKUP_DIR / COUNTRY_INFO_FILENAME
BACKUP_GEOLOCATION_FILE = BACKUP_DIR / GEOLOCATION_FILENAME

# Generated Author Info Header Keys
GEN_AUTHOR_DEPT_KEY = "dept"

# Country Info Header Keys
COUNTRY_INFO_INSTITUTION_KEY = "institution"
COUNTRY_INFO_REGION_KEY = "region"
COUNTRY_INFO_COUNTRY_ABBRV_KEY = "countryabbrv"

# Countries Header Keys
COUNTRIES_NAME_KEY = "name"

# Writing Keys
UTF_SIG_ENCODING = "utf-8-sig"

# URLs for downloading data
CSRANKINGS_RAW_GITHUB = (
    "https://raw.githubusercontent.com/emeryberger/CSrankings/gh-pages/"
)
NSF_AWARD_SEARCH_URL = (
    "https://www.nsf.gov/awardsearch/download?All=true&isJson=true&DownloadFileName="
)

# Artifacts Generated
MATCHED_FACULTY_FILE = TARGET_DIR / "matched_faculty.csv"
UNIVERSITY_MAP_FILE = TARGET_DIR / "university_map.html"
