import questionary

# Project imports
from constants import *
from countries import (
    load_country_name_map,
    select_countries,
    filter_faculty_by_country,
)
from utils import download_csvs, export_results_to_csv, parse_csv, download_nsf_zip_files
from area import research_area_selection
from graphs import generate_university_map
from logger import logger


def main():
    download_csvs(questionary.confirm("Update CSrankings data?").ask())
    download_nsf_zip_files(questionary.confirm("Update NSF data?").ask())

    selected_areas = research_area_selection()
    if not selected_areas:
        logger.error("No research areas selected. Exiting.")
        return

    logger.info(f"Filtering by: {', '.join(selected_areas)}")
    faculty = parse_csv(selected_areas)
    code_to_name = load_country_name_map()

    selected_countries = select_countries(code_to_name)
    if selected_countries:
        logger.info(f"🌍 {len(selected_countries)} countries selected for filtering.")
        logger.info(f"Faculty before country filtering: {len(faculty)}")
        faculty = filter_faculty_by_country(faculty, selected_countries)
        logger.info(f"🌍 {len(faculty)} faculty after country filtering.")

    export_results_to_csv(faculty)
    generate_university_map(faculty)


if __name__ == "__main__":
    main()
