import requests
import csv
import re
import zipfile
from typing import List


# Project imports
from constants import *
from models import Faculty, FacultyData
from logger import logger

CSV_URLS = {
    CS_RANKINGS_FILE: f"{CSRANKINGS_RAW_GITHUB}{CS_RANKINGS_FILENAME}",
    GEN_AUTHOR_FILE: f"{CSRANKINGS_RAW_GITHUB}{GEN_AUTHOR_FILENAME}",
    COUNTRIES_FILE: f"{CSRANKINGS_RAW_GITHUB}{COUNTRIES_FILENAME}",
    COUNTRY_INFO_FILE: f"{CSRANKINGS_RAW_GITHUB}{COUNTRY_INFO_FILENAME}",
    GEOLOCATION_FILE: f"{CSRANKINGS_RAW_GITHUB}{GEOLOCATION_FILENAME}",
}

NSF_YEARS = [2025, 2024, 2023, 2022, 2021, 2020, 2019]


def clean_name(name: str) -> str:
    return re.sub(r"\s*\[.*?\]$", "", name).strip()


def download_nsf_zip_files(force_download: bool = False):
    for year in NSF_YEARS:
        local_file = NSF_DATA_DIR / f"nsf_awards_{year}.zip"
        extract_dir = NSF_DATA_DIR / str(year)

        if local_file.exists() and not force_download:
            logger.info(f"[✓] {local_file.name} already exists. Skipping download.")
        else:
            logger.info(f"[*] Downloading {local_file.name} ...")
            response = requests.get(f"{NSF_AWARD_SEARCH_URL}{year}")
            if response.status_code != 200:
                logger.error(
                    f"[!] Failed to download {local_file.name}. Status code: {response.status_code}. Response: {response.text}"
                )
                continue

            local_file.write_bytes(response.content)
            logger.info(f"[✓] {local_file.name} downloaded.")

        # Unzip to year-specific directory
        if extract_dir.exists() and not force_download:
            logger.info(f"[✓] Already extracted to {extract_dir}")
            continue

        logger.info(f"[*] Extracting {local_file.name} to {extract_dir} ...")
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(local_file, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            logger.info(f"[✓] Extracted to {extract_dir}")
        except zipfile.BadZipFile:
            logger.error(f"[!] {local_file.name} is not a valid zip file.")


def download_csvs(force_download: bool = False):
    for local_file, url in CSV_URLS.items():
        if local_file.exists() and not force_download:
            logger.info(f"[✓] {local_file.name} already exists. Skipping download.")
            continue

        logger.info(f"[*] Downloading {local_file.name} ...")
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(
                f"[!] Failed to download {local_file.name}. Status code: {response.status_code}. Response: {response.text}"
            )
            continue

        local_file.write_bytes(response.content)
        logger.info(f"[✓] {local_file.name} downloaded.")


def export_results_to_csv(results: List[Faculty]):
    with MATCHED_FACULTY_FILE.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["Name", "Department", "Affiliation", "Homepage", "Matched Areas"]
        )

        for person in results:
            writer.writerow(
                [
                    person.name,
                    person.dept,
                    person.affiliation,
                    person.homepage,
                    ", ".join(person.matched_areas),
                ]
            )

    logger.info(
        f"📁 Results exported to [bold green]{MATCHED_FACULTY_FILE}[/bold green]"
    )


def parse_csv(area_keys: List[str]) -> List[Faculty]:
    logger.info("📄 Parsing generated-author-info.csv for selected areas...")

    # Create a quick lookup of selected subareas
    selected_subareas: set[str] = set(area_keys)

    faculty_map: dict[tuple[str, str], FacultyData] = {}
    homepage_map: dict[str, str] = {}

    # Read the CS rankings CSV file to get faculty names and homepages
    logger.info("🔍 Reading CS rankings file for faculty names and homepages...")

    with CS_RANKINGS_FILE.open(newline="", encoding="utf-8-sig") as rankings_csv:
        for row in csv.DictReader(rankings_csv):
            raw_name = row.get("name", "").strip()
            name = clean_name(raw_name)
            homepage_map[name] = row.get("homepage", "").strip()

    # Read the CSV file and filter based on selected subareas
    logger.info(
        f"🔍 Filtering faculty entries for {len(selected_subareas)} selected subareas..."
    )
    with GEN_AUTHOR_FILE.open(newline="", encoding="utf-8") as author_info_csv:
        reader = csv.DictReader(author_info_csv)

        for row in reader:
            area = row.get("area", "")
            if area not in selected_subareas:
                continue

            name = row.get("name", "").strip()
            affiliation = row.get(GEN_AUTHOR_DEPT_KEY, "").strip()

            if not name or not affiliation:
                continue  # skip malformed rows

            key = (name, affiliation)
            if key not in faculty_map:
                dept_val: str = row.get("dept", "") or ""
                if not dept_val:
                    logger.warning(
                        f"⚠️ Missing department for faculty {name} in {affiliation}. Using 'Unknown' as placeholder."
                    )
                    dept_val = "Unknown"

                homepage_map_val: str = homepage_map.get(name, "") or ""
                if not homepage_map_val:
                    logger.warning(
                        f"⚠️ Missing homepage for faculty {name} in {affiliation}. Using empty string as placeholder."
                    )
                    homepage_map[name] = homepage_map_val

                faculty_map[key] = FacultyData(
                    name=name,
                    affiliation=affiliation,
                    dept=dept_val,
                    homepage=homepage_map_val,
                    matched_areas=set(),
                )

            faculty_map[key]["matched_areas"].add(area)

    if not faculty_map:
        logger.warning("⚠️ No faculty members found matching the selected subareas.")
        return []

    logger.info(f"✅ Found {len(faculty_map)} matching faculty entries.")

    # Convert to Faculty instances
    faculty_list: List[Faculty] = [
        Faculty(
            name=data["name"],
            dept=data["dept"],
            affiliation=data["affiliation"],
            homepage=data["homepage"],
            matched_areas=sorted(data["matched_areas"]),
        )
        for data in faculty_map.values()
    ]

    return faculty_list
