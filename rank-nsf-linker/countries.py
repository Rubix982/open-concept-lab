import csv
import questionary
from logger import logger

from typing import Dict, List

# Project imports
from models import Faculty
from constants import (
    COUNTRIES_FILE,
    COUNTRY_INFO_FILE,
    BACKUP_COUNTRY_INFO_FILE,
    COUNTRY_INFO_INSTITUTION_KEY,
    COUNTRY_INFO_REGION_KEY,
    COUNTRY_INFO_COUNTRY_ABBRV_KEY,
    UTF_SIG_ENCODING,
)

def write_country_info_backup(
    not_found_country_codes: set[str],
    region: str,
    country_code: str,
) -> None:
    """Writes the country info to a backup file."""
    if not BACKUP_COUNTRY_INFO_FILE.exists():
        # If it doesn't exist, create the backup directory
        with BACKUP_COUNTRY_INFO_FILE.open("w", encoding=UTF_SIG_ENCODING) as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    COUNTRY_INFO_INSTITUTION_KEY,
                    COUNTRY_INFO_REGION_KEY,
                    COUNTRY_INFO_COUNTRY_ABBRV_KEY,
                ]
            )

    with BACKUP_COUNTRY_INFO_FILE.open("a", encoding=UTF_SIG_ENCODING) as f:
        writer = csv.writer(f)
        for uni in not_found_country_codes:
            writer.writerow([uni, region, country_code])


def load_university_country_map() -> Dict[str, str]:
    uni_to_country: Dict[str, str] = {}
    with COUNTRY_INFO_FILE.open(encoding=UTF_SIG_ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uni: str = row[COUNTRY_INFO_INSTITUTION_KEY].strip().lower()
            country_code: str = row[COUNTRY_INFO_COUNTRY_ABBRV_KEY].strip().lower()
            uni_to_country[uni] = country_code

    return uni_to_country


def load_backup_country_info_map() -> Dict[str, str]:
    uni_to_country: Dict[str, str] = {}

    if not BACKUP_COUNTRY_INFO_FILE.exists():
        logger.debug("⚠️ Backup country info file does not exist.")
        return uni_to_country

    with BACKUP_COUNTRY_INFO_FILE.open(encoding=UTF_SIG_ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uni: str = row[COUNTRY_INFO_INSTITUTION_KEY].strip().lower()
            country_code: str = row[COUNTRY_INFO_COUNTRY_ABBRV_KEY].strip().lower()
            uni_to_country[uni] = country_code

    return uni_to_country


def load_country_name_map() -> Dict[str, str]:
    code_to_name: Dict[str, str] = {}
    with COUNTRIES_FILE.open(mode="r", encoding=UTF_SIG_ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            alpha2 = row["alpha_2"].strip().lower()
            code_to_name[alpha2] = name

    return code_to_name


def select_countries(code_to_name: dict[str, str]) -> set[str]:
    country_lookup = {name: code for code, name in code_to_name.items()}

    selected_countries: set[str] = set()

    logger.info(
        "🌍 Start typing country names to select (e.g., United States, Germany)."
    )
    logger.info("👉 Press Enter without input to finish selection.\n")

    while True:
        country = questionary.autocomplete(
            "Type a country to add (Enter to finish):",
            choices=sorted(country_lookup.keys()),
            validate=lambda val: val in country_lookup or val == "",  # type: ignore
            ignore_case=True,
            default="",
        ).ask()

        if not country:
            break

        selected_countries.add(country_lookup[country])
        logger.info(f"✅ Added: {country}")

    return selected_countries


def filter_faculty_by_country(
    faculty: List[Faculty],
    selected_countries: set[str],
) -> List[Faculty]:
    if not selected_countries:
        return faculty

    uni_country_map: Dict[str, str] = load_university_country_map()
    backup_country_map: Dict[str, str] = load_backup_country_info_map()

    # Merge the two maps, giving priority to the main country info file
    uni_country_map.update(backup_country_map)
    if not uni_country_map:
        logger.info(
            "⚠️ No university-country mapping found. Please check the country info files."
        )
        return faculty

    filtered: list[Faculty] = []
    not_found_country_codes: set[str] = set()
    for f in faculty:
        uni_key = f.affiliation.strip().lower()
        if not uni_key:
            logger.info("⚠️ No affiliation found, skipping.")
            continue

        # Normalize university key by removing common suffixes
        country_code = uni_country_map.get(uni_key)
        if not country_code:
            logger.info(f"⚠️ No country code found for university: {uni_key}")
            not_found_country_codes.add(uni_key.title())
            continue

        if country_code in selected_countries:
            filtered.append(f)

    # Uncomment the following line to see add to the backup file universities not found
    # write_country_info_backup(not_found_country_codes, "northamerica", "us")

    return filtered
