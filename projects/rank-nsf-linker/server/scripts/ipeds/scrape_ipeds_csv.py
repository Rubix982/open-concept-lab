#!/usr/bin/env python3
"""
IPEDS Data Fetcher
Downloads and parses IPEDS data files for a given year
"""

import requests
import pandas as pd
import io
import zipfile
import re
import tempfile
import json
from typing import Dict, Any
import concurrent.futures as cf
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple, List


def fetch_ipeds_data(
    year: int = 2023,
    max_workers: int = 20,
    cache_dir: str = "ipeds_cache",
    dict_dir: str = "ipeds_dict",
    download_dictionaries: bool = True,
) -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, Dict[str, str]]]:
    """
    Download IPEDS data files and return as DataFrames.
    Year format: 2023 means 2022-23 academic year.
    """

    base_url = "https://nces.ed.gov/ipeds/datacenter/data"
    wayback_url = f"https://web.archive.org/web/20240822183521/{base_url}"

    # Transform year for finance files (2023 -> 2223)
    transformed_year = int(str(year).replace("0", "2", -1))

    files = {
        # ========== CORE INSTITUTIONAL DATA ==========
        "institutions": f"HD{year}",
        "institutional_characteristics": f"IC{year}",
        "institutional_characteristics_ay": f"IC{year}_AY",
        "institutional_characteristics_py": f"IC{year}_PY",
        "institutional_mission": f"IC{year}Mission",
        "institutional_campuses": f"IC{year}_PCCAMPUSES",
        # ========== ENROLLMENT DATA ==========
        "enrollment_fall": f"EF{year}A",
        "enrollment_fall_age": f"EF{year}B",
        "enrollment_fall_residence": f"EF{year}C",
        "enrollment_fall_distance": f"EF{year}A_DIST",
        "enrollment_fall_full": f"EF{year}D",
        "enrollment_12month": f"EF{year}",
        "enrollment_12month_dist": f"EFFY{year}_DIST",
        "enrollment_high_school": f"EFFY{year}_HS",
        # ========== COMPLETIONS/DEGREES ==========
        "completions": f"C{year}_A",
        "completions_cip": f"C{year}_B",
        "completions_distance": f"C{year}_C",
        "completions_dep": f"C{year}DEP",
        # ========== STAFF/FACULTY DATA ==========
        "staff_instructional": f"S{year}_IS",
        "staff_non_instructional": f"S{year}_NH",
        "staff_new_hires": f"S{year}_SIS",
        "staff_occupational": f"S{year}_OC",
        "salaries_instructional": f"SAL{year}_IS",
        "salaries_non_instructional": f"SAL{year}_NIS",
        # ========== FINANCIAL DATA ==========
        "finance_public": [
            f"F{transformed_year}_F2",
            f"F{transformed_year}",
        ],
        "finance_private": f"F{transformed_year}_F1A",
        "finance_private_forprofit": f"F{transformed_year}_F3",
        # ========== STUDENT FINANCIAL AID ==========
        "financial_aid_summary": f"SFAV{transformed_year}",
        "financial_aid_part1": f"SFA{transformed_year}_P1",
        "financial_aid_part2": f"SFA{transformed_year}_P2",
        # ========== ADMISSIONS ==========
        "admissions": f"ADM{year}",
        # ========== GRADUATION RATES ==========
        "graduation_rates": f"GR{year}",
        "graduation_rates_200": f"GR200_{str(year)[-2:]}",
        "graduation_rates_l2": f"GR{year}_L2",
        "graduation_rates_pell": f"GR{year}_PELL_SSL",
        "graduation_rates_gender": f"GR{year}_GENDER",
        # ========== OUTCOME MEASURES ==========
        "outcome_measures": f"OM{year}",
        # ========== ACADEMIC LIBRARIES ==========
        "academic_libraries": f"AL{year}",
        # ========== ADDITIONAL PROGRAMS ==========
        "education_abroad": f"EAP{year}",
        "institutional_archive": f"EFIA{year}",
        # ========== FLAGS & CUSTOM DATA ==========
        "flags": f"FLAGS{year}",
        "custom_peer_groups": f"CUSTOMCGIDS{year}",
        # ========== DERIVED VARIABLES ==========
        "derived_admissions": f"DRVADM{year}",
        "derived_enrollment": f"DRVEF{year}",
        "derived_enrollment_12month": f"DRVEF12{year}",
        "derived_finance": f"DRVF{year}",
        "derived_graduation": f"DRVGR{year}",
        "derived_hr": f"DRVHR{year}",
        "derived_institutional": f"DRVIC{year}",
        "derived_outcomes": f"DRVOM{year}",
        "derived_value_added": f"DRVAL{year}",
        "derived_value_cohorts": f"DRVC{year}",
    }

    # Logging with thread names
    logger = logging.getLogger("ipeds_download")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    dataframes: Dict[str, Optional[pd.DataFrame]] = {}
    lock = threading.Lock()
    column_maps: Dict[str, Dict[str, str]] = {}
    column_maps_lock = threading.Lock()
    cache_path = Path(cache_dir) / str(year)
    cache_path.mkdir(parents=True, exist_ok=True)
    dict_path = Path(dict_dir) / str(year)
    dict_path.mkdir(parents=True, exist_ok=True)
    dict_cache: Dict[str, Dict[str, str]] = {}
    dict_cache_lock = threading.Lock()

    def cache_file_for(key: str) -> Path:
        return cache_path / f"{key}.parquet"

    def cache_meta_file_for(key: str) -> Path:
        return cache_path / f"{key}.meta.json"

    def load_from_cache(key: str) -> Optional[pd.DataFrame]:
        path = cache_file_for(key)
        if path.exists():
            logger.info(f"[{key}] Loaded from cache {path}")
            df = pd.read_parquet(path)
            if download_dictionaries:
                meta_path = cache_meta_file_for(key)
                file_code = None
                if meta_path.exists() and key not in column_maps:
                    try:
                        meta = json.loads(meta_path.read_text())
                        file_code = meta.get("file_code")
                    except (json.JSONDecodeError, OSError) as exc:
                        logger.warning(f"[{key}] Failed to read cache meta: {exc}")
                if file_code is None:
                    file_codes = files.get(key)
                    if isinstance(file_codes, list) and file_codes:
                        file_code = file_codes[0]
                    elif isinstance(file_codes, str):
                        file_code = file_codes
                if file_code and key not in column_maps:
                    mapping = load_dictionary_mapping(file_code)
                    if mapping:
                        filtered = {col: mapping.get(col, "") for col in df.columns}
                        with column_maps_lock:
                            column_maps[key] = filtered
            return df
        return None

    def save_to_cache(key: str, df: pd.DataFrame) -> None:
        path = cache_file_for(key)
        df.to_parquet(path, index=False)
        logger.info(f"[{key}] Saved to cache {path}")

    def save_cache_meta(key: str, file_code: str) -> None:
        meta_path = cache_meta_file_for(key)
        try:
            meta_path.write_text(json.dumps({"file_code": file_code}))
        except OSError as exc:
            logger.warning(f"[{key}] Failed to write cache meta: {exc}")

    def build_sources(file_code: str) -> List[str]:
        return [
            f"{base_url}/{file_code}.zip",
            f"{wayback_url}/{file_code}.zip",
        ]

    def build_dictionary_sources(file_code: str) -> List[str]:
        return [
            f"{base_url}/{file_code}_Dict.zip",
            f"{base_url}/{file_code}_dict.zip",
            f"{wayback_url}/{file_code}_Dict.zip",
            f"{wayback_url}/{file_code}_dict.zip",
        ]

    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Strip UTF-8 BOM and normalize known corrupted column name.
        df = df.rename(columns=lambda col: col.lstrip("\ufeff"))
        if "ï»¿UNITID" in df.columns:
            df = df.rename(columns={"ï»¿UNITID": "UNITID"})
        return df

    def extract_var_label_pairs(df: pd.DataFrame) -> Dict[str, str]:
        def norm(value: Any) -> str:
            return re.sub(r"[^a-z0-9]+", "", str(value).lower())

        def pick_columns(columns: List[str]) -> Tuple[Optional[str], Optional[str]]:
            normalized = [norm(col) for col in columns]
            name_candidates = {
                "varname",
                "variable",
                "var",
                "fieldname",
                "field",
                "item",
            }
            label_candidates = {
                "label",
                "varlabel",
                "description",
                "title",
                "definition",
            }
            name_col = None
            label_col = None
            for col, key in zip(columns, normalized):
                if key in name_candidates or ("var" in key and "name" in key):
                    name_col = col
                    break
            for col, key in zip(columns, normalized):
                if key in label_candidates or "label" in key or "description" in key:
                    label_col = col
                    break
            return name_col, label_col

        columns = [str(col) for col in df.columns]
        name_col, label_col = pick_columns(columns)

        if name_col is None or label_col is None:
            if not df.empty:
                header = [str(v) for v in df.iloc[0].values]
                header_name, header_label = pick_columns(header)
                if header_name is not None and header_label is not None:
                    df = df.iloc[1:].copy()
                    df.columns = header
                    columns = [str(col) for col in df.columns]
                    name_col, label_col = pick_columns(columns)

        if name_col is None or label_col is None:
            return {}

        mapping: Dict[str, str] = {}
        for _, row in df.iterrows():
            name = str(row.get(name_col, "")).strip()
            label = str(row.get(label_col, "")).strip()
            if not name or name.lower() in {"nan", "none"}:
                continue
            if name not in mapping or not mapping[name]:
                mapping[name] = label
        return mapping

    def load_dictionary_mapping(file_code: str) -> Dict[str, str]:
        with dict_cache_lock:
            if file_code in dict_cache:
                return dict_cache[file_code]

        if not download_dictionaries:
            return {}

        dict_zip_path = dict_path / f"{file_code}_Dict.zip"
        if not dict_zip_path.exists():
            for source_url in build_dictionary_sources(file_code):
                try:
                    logger.info(f"[{file_code}] Downloading dictionary {source_url}")
                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()
                    dict_zip_path.write_bytes(response.content)
                    break
                except requests.exceptions.RequestException as exc:
                    logger.warning(
                        f"[{file_code}] Dictionary download failed {source_url}: {exc}"
                    )

        if not dict_zip_path.exists():
            with dict_cache_lock:
                dict_cache[file_code] = {}
            return {}

        mapping: Dict[str, str] = {}
        try:
            with zipfile.ZipFile(dict_zip_path) as zf:
                members = [
                    m
                    for m in zf.namelist()
                    if m.lower().endswith((".xls", ".xlsx", ".html", ".htm"))
                ]
                if not members:
                    raise ValueError("No dictionary files found in zip.")
                with tempfile.TemporaryDirectory() as tmpdir:
                    zf.extractall(tmpdir, members)
                    for member in members:
                        path = Path(tmpdir) / member
                        if not path.exists():
                            continue
                        try:
                            if path.suffix.lower() in {".xls", ".xlsx"}:
                                sheets = pd.read_excel(path, sheet_name=None)
                                for sheet_df in sheets.values():
                                    mapping.update(extract_var_label_pairs(sheet_df))
                            else:
                                tables = pd.read_html(path)
                                for table in tables:
                                    mapping.update(extract_var_label_pairs(table))
                        except ImportError as exc:
                            logger.warning(
                                f"[{file_code}] Dictionary parse missing dependency: {exc}"
                            )
                        except ValueError:
                            continue
        except Exception as exc:
            logger.warning(f"[{file_code}] Dictionary parse failed: {exc}")

        with dict_cache_lock:
            dict_cache[file_code] = mapping
        return mapping

    def download_one(
        key: str, file_codes: List[str]
    ) -> Tuple[str, Optional[pd.DataFrame]]:
        cached = load_from_cache(key)
        if cached is not None:
            return key, cached

        for file_code in file_codes:
            sources = build_sources(file_code)

            for source_url in sources:
                try:
                    logger.info(f"[{key}] Downloading from {source_url}")
                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()

                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        file_list = z.namelist()
                        csv_files = [f for f in file_list if f.lower().endswith(".csv")]
                        if not csv_files:
                            logger.warning(f"[{key}] No CSV in archive {source_url}")
                            continue

                        csv_name = csv_files[0]
                        logger.info(f"[{key}] Reading {csv_name}")
                        with z.open(csv_name) as csv_file:
                            df = pd.read_csv(csv_file, encoding="latin1")
                            df = normalize_columns(df)
                            save_to_cache(key, df)
                            save_cache_meta(key, file_code)
                            logger.info(f"[{key}] Loaded {len(df)} rows")
                            if download_dictionaries:
                                mapping = load_dictionary_mapping(file_code)
                                if mapping:
                                    filtered = {
                                        col: mapping.get(col, "") for col in df.columns
                                    }
                                    with column_maps_lock:
                                        column_maps[key] = filtered
                            return key, df

                except requests.exceptions.RequestException as e:
                    logger.warning(f"[{key}] Request failed {source_url}: {e}")
                except (zipfile.BadZipFile, KeyError) as e:
                    logger.warning(f"[{key}] Invalid zip from {source_url}: {e}")

        logger.error(f"[{key}] All sources failed")
        return key, None

    # Prepare tasks
    tasks: List[Tuple[str, List[str]]] = []
    for key, file_codes in files.items():
        if isinstance(file_codes, str):
            file_list = [file_codes]
        else:
            file_list = list(file_codes)
        tasks.append((key, file_list))

    # Run in parallel
    with cf.ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="ipeds"
    ) as pool:
        future_map = {
            pool.submit(download_one, key, file_codes): key for key, file_codes in tasks
        }

        for fut in cf.as_completed(future_map):
            key, df = fut.result()
            with lock:
                dataframes[key] = df

    return dataframes, column_maps


def transform_institutions(df: pd.DataFrame) -> pd.DataFrame:
    """Transform HD (Directory) data to match schema"""
    print(f"List of columns in institutions: {df.columns.values}")
    columns = [
        "UNITID",
        "INSTNM",  # institution_name
        "IALIAS",  # institution alias
        "ADDR",  # address
        "CITY",
        "STABBR",  # state
        "ZIP",
        "WEBADDR",  # website
        "SECTOR",
        "ICLEVEL",  # institutional level
        "CONTROL",
        "HBCU",  # historically_black
        "HOSPITAL",  # has hospital
        "MEDICAL",  # has medical school
        "TRIBAL",  # tribal_college
        "LANDGRNT",  # landgrant
        "CCBASIC",  # carnegie_classification (or use C21BASIC)
        "LOCALE",
        "INSTSIZE",  # institution size
        "CBSA",  # metro area code
        "COUNTYNM",  # county name
        "OBEREG",  # geographic region
        "LATITUDE",
        "LONGITUD",  # longitude
        "F1SYSTYP",  # system type
        "F1SYSNAM",  # system name
    ]
    df = ensure_columns(df, columns, "HD")
    return df[columns].rename(
        columns={
            "UNITID": "unitid",
            "INSTNM": "institution_name",
            "IALIAS": "institution_alias",
            "ADDR": "address",
            "CITY": "city",
            "STABBR": "state",
            "ZIP": "zip",
            "WEBADDR": "website",
            "SECTOR": "sector",
            "ICLEVEL": "institutional_level",
            "CONTROL": "control",
            "HBCU": "historically_black",
            "HOSPITAL": "has_hospital",
            "MEDICAL": "has_medical_school",
            "TRIBAL": "tribal_college",
            "LANDGRNT": "landgrant",
            "CCBASIC": "carnegie_classification",
            "LOCALE": "locale",
            "INSTSIZE": "institution_size",
            "CBSA": "metro_area",
            "COUNTYNM": "county_name",
            "OBEREG": "geographic_region",
            "LATITUDE": "latitude",
            "LONGITUD": "longitude",
            "F1SYSTYP": "system_type",
            "F1SYSNAM": "system_name",
        }
    )


def transform_enrollment(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform EF (Enrollment) data to match schema"""
    print(f"List of columns in enrollments: {df.columns.values}")
    columns = [
        "UNITID",
        "EFALEVEL",
        "EFTOTLT",
        "EFTOTLM",
        "EFTOTLW",
        "EFAIANT",
        "EFASIAT",
        "EFBKAAT",
        "EFHISPT",
        "EFWHITT",
        "EF2MORT",
        "EFNRALT",
    ]
    df = ensure_columns(df, columns, "EF")
    print(f"Unique EFALEVEL values: {df['EFALEVEL'].unique()}")

    # EFALEVEL codes:
    # 1 = All students total
    # 2 = Undergraduate total
    # 4 = Graduate total

    # Get totals for each level
    all_students = df[df["EFALEVEL"] == 1][
        ["UNITID", "EFTOTLT", "EFTOTLM", "EFTOTLW"]
    ].copy()
    undergrad = df[df["EFALEVEL"] == 2][["UNITID", "EFTOTLT"]].copy()
    graduate = df[df["EFALEVEL"] == 4][["UNITID", "EFTOTLT"]].copy()

    # Merge into single record per institution
    result = all_students.rename(
        columns={
            "UNITID": "unitid",
            "EFTOTLT": "total_enrollment",
            "EFTOTLM": "enrollment_men",
            "EFTOTLW": "enrollment_women",
        }
    )

    # Add undergrad/grad totals
    if not undergrad.empty:
        undergrad = undergrad.rename(
            columns={"UNITID": "unitid", "EFTOTLT": "undergraduate_total"}
        )
        result = result.merge(undergrad, on="unitid", how="left")

    if not graduate.empty:
        graduate = graduate.rename(
            columns={"UNITID": "unitid", "EFTOTLT": "graduate_total"}
        )
        result = result.merge(graduate, on="unitid", how="left")

    # Add demographic breakdowns from level 1 (all students)
    demographics = df[df["EFALEVEL"] == 1][
        [
            "UNITID",
            "EFAIANT",  # American Indian/Alaska Native
            "EFASIAT",  # Asian
            "EFBKAAT",  # Black/African American
            "EFHISPT",  # Hispanic
            "EFWHITT",  # White
            "EF2MORT",  # Two or more races
            "EFNRALT",  # Non-resident alien
        ]
    ].rename(
        columns={
            "UNITID": "unitid",
            "EFAIANT": "american_indian_total",
            "EFASIAT": "asian_total",
            "EFBKAAT": "black_total",
            "EFHISPT": "hispanic_total",
            "EFWHITT": "white_total",
            "EF2MORT": "two_or_more_races_total",
            "EFNRALT": "nonresident_alien_total",
        }
    )

    result = result.merge(demographics, on="unitid", how="left")
    result["year"] = year

    return result


def transform_staff(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform S_IS (Instructional Staff) data to match schema"""
    print(f"List of available columns in staff: {df.columns.values}")
    columns = [
        "UNITID",
        "SISCAT",
        "FACSTAT",
        "ARANK",
        "HRTOTLT",
        "HRTOTLM",
        "HRTOTLW",
        "HRAIANT",
        "HRASIAT",
        "HRBKAAT",
        "HRHISPT",
        "HRWHITT",
        "HR2MORT",
        "HRNRALT",
    ]
    df = ensure_columns(df, columns, "S_IS")
    print(f"Unique SISCAT values: {df['SISCAT'].unique()}")
    print(f"Unique FACSTAT values: {df['FACSTAT'].unique()}")
    print(f"Unique ARANK values: {df['ARANK'].unique()}")

    print(f"\nSample rows:")
    print(df[["UNITID", "SISCAT", "FACSTAT", "ARANK", "HRTOTLT"]].head(30))

    # SISCAT interpretation from sample:
    # 1 = Grand total (all staff)
    # 100-106 = Primarily instruction (by FACSTAT)
    # 200-206 = Instruction with research/service (by FACSTAT)
    # 300-306 = Primarily research (by FACSTAT)
    # 400-456 = Other categories

    # FACSTAT interpretation from sample:
    # 0 = Total for that SISCAT category
    # 10 = All faculty/staff in category
    # 20 = Tenured
    # 30 = On tenure track
    # 40 = Not on tenure track
    # 42 = Not on tenure track - multi-year
    # 43 = Not on tenure track - annual
    # 50 = Without faculty status

    # ARANK from sample:
    # 0 = All ranks
    # 1 = Professors
    # 2 = Associate professors
    # 3 = Assistant professors
    # 4 = Instructors
    # 5 = Lecturers
    # 6 = No academic rank

    # Get total instructional staff: SISCAT=100, FACSTAT=10, ARANK=0
    instructional = df[
        (df["SISCAT"] == 100) & (df["FACSTAT"] == 10) & (df["ARANK"] == 0)
    ][["UNITID", "HRTOTLT", "HRTOTLM", "HRTOTLW"]].copy()

    if instructional.empty:
        print("Warning: No instructional staff data found")
        return pd.DataFrame()

    result = instructional.rename(
        columns={
            "UNITID": "unitid",
            "HRTOTLT": "instructional_staff_total",
            "HRTOTLM": "instructional_staff_men",
            "HRTOTLW": "instructional_staff_women",
        }
    )

    # Get tenured faculty: SISCAT=200, FACSTAT=20, ARANK=0
    tenured = df[(df["SISCAT"] == 200) & (df["FACSTAT"] == 20) & (df["ARANK"] == 0)][
        ["UNITID", "HRTOTLT"]
    ].rename(columns={"UNITID": "unitid", "HRTOTLT": "tenured_faculty"})

    if not tenured.empty:
        result = result.merge(tenured, on="unitid", how="left")

    # Get tenure-track: SISCAT=300, FACSTAT=30, ARANK=0
    tenure_track = df[
        (df["SISCAT"] == 300) & (df["FACSTAT"] == 30) & (df["ARANK"] == 0)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "tenure_track_faculty"}
    )

    if not tenure_track.empty:
        result = result.merge(tenure_track, on="unitid", how="left")

    # Get not-on-tenure-track: SISCAT=400, FACSTAT=40, ARANK=0
    not_tenure_track = df[
        (df["SISCAT"] == 400) & (df["FACSTAT"] == 40) & (df["ARANK"] == 0)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "not_tenure_track_faculty"}
    )

    if not not_tenure_track.empty:
        result = result.merge(not_tenure_track, on="unitid", how="left")

    # Faculty by rank from SISCAT=100 (all instructional), varying ARANK
    professors = df[(df["SISCAT"] == 101) & (df["FACSTAT"] == 10) & (df["ARANK"] == 1)][
        ["UNITID", "HRTOTLT"]
    ].rename(columns={"UNITID": "unitid", "HRTOTLT": "professors"})

    associate_profs = df[
        (df["SISCAT"] == 102) & (df["FACSTAT"] == 10) & (df["ARANK"] == 2)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "associate_professors"}
    )

    assistant_profs = df[
        (df["SISCAT"] == 103) & (df["FACSTAT"] == 10) & (df["ARANK"] == 3)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "assistant_professors"}
    )

    instructors = df[
        (df["SISCAT"] == 104) & (df["FACSTAT"] == 10) & (df["ARANK"] == 4)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "instructors"}
    )

    if not professors.empty:
        result = result.merge(professors, on="unitid", how="left")
    if not associate_profs.empty:
        result = result.merge(associate_profs, on="unitid", how="left")
    if not assistant_profs.empty:
        result = result.merge(assistant_profs, on="unitid", how="left")
    if not instructors.empty:
        result = result.merge(instructors, on="unitid", how="left")

    # Demographics from SISCAT=100, FACSTAT=10, ARANK=0
    demographics = df[
        (df["SISCAT"] == 100) & (df["FACSTAT"] == 10) & (df["ARANK"] == 0)
    ][
        [
            "UNITID",
            "HRAIANT",
            "HRASIAT",
            "HRBKAAT",
            "HRHISPT",
            "HRWHITT",
            "HR2MORT",
            "HRNRALT",
        ]
    ].rename(
        columns={
            "UNITID": "unitid",
            "HRAIANT": "american_indian_faculty",
            "HRASIAT": "asian_faculty",
            "HRBKAAT": "black_faculty",
            "HRHISPT": "hispanic_faculty",
            "HRWHITT": "white_faculty",
            "HR2MORT": "two_or_more_races_faculty",
            "HRNRALT": "nonresident_alien_faculty",
        }
    )

    if not demographics.empty:
        result = result.merge(demographics, on="unitid", how="left")

    result["year"] = year

    return result


def transform_finance(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform F_F2 (Finance) data - Extract ALL useful columns"""
    print(f"List of columns in the finance table: {df.columns.values}")

    # Get all non-X columns (X prefix = imputation flags, skip those)
    finance_columns = [col for col in df.columns if not col.startswith("X")]

    return (
        df[finance_columns]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                # ========== SECTION A: ASSETS & LIABILITIES ==========
                "F2A01": "total_assets",
                "F2A19": "total_liabilities",
                "F2A20": "net_assets",
                "F2A02": "current_assets",
                "F2A03": "long_term_investments",
                "F2A03A": "land_buildings_equipment_net",
                "F2A04": "property_plant_equipment",
                "F2A05": "accumulated_depreciation",
                "F2A05A": "intangible_assets_net",
                "F2A05B": "other_noncurrent_assets",
                "F2A06": "deferred_outflows",
                "F2A11": "current_liabilities",
                "F2A12": "long_term_debt_current",
                "F2A13": "other_current_liabilities",
                "F2A15": "noncurrent_liabilities",
                "F2A16": "long_term_debt_noncurrent",
                "F2A17": "other_noncurrent_liabilities",
                "F2A18": "deferred_inflows",
                # ========== SECTION B: SCHOLARSHIPS ==========
                "F2B01": "federal_grants_scholarships",
                "F2B02": "state_local_grants_scholarships",
                "F2B03": "institutional_grants_scholarships",
                "F2B04": "total_discounts_allowances",
                "F2B05": "total_scholarships_fellowships",
                "F2B06": "net_scholarships_fellowships",
                "F2B07": "allowances_tuition_fees",
                # ========== SECTION C: REVENUES ==========
                "F2C01": "total_revenues",
                "F2C02": "total_operating_revenues",
                "F2C03": "total_nonoperating_revenues",
                "F2C04": "other_revenues_additions",
                "F2C05": "tuition_fees_gross",
                "F2C06": "tuition_fees_allowances",
                "F2C07": "tuition_fees_net",
                "F2C08": "federal_appropriations",
                "F2C09": "state_appropriations",
                "F2C10": "local_appropriations",
                # Revenue details
                "F2C12": "federal_grants_contracts",
                "F2C121": "federal_operating_grants",
                "F2C122": "federal_nonoperating_grants",
                "F2C13": "state_grants_contracts",
                "F2C131": "state_operating_grants",
                "F2C132": "state_nonoperating_grants",
                "F2C14": "local_grants_contracts",
                "F2C141": "local_operating_grants",
                "F2C142": "local_nonoperating_grants",
                "F2C15": "private_gifts_grants_contracts",
                "F2C151": "private_operating_grants",
                "F2C152": "private_nonoperating_grants",
                "F2C16": "investment_return",
                "F2C161": "investment_income_operating",
                "F2C162": "investment_income_nonoperating",
                "F2C17": "other_revenues",
                "F2C171": "sales_services_auxiliary",
                "F2C172": "sales_services_hospitals",
                # ========== SECTION D: FUNCTIONAL EXPENSES ==========
                "F2D01": "total_expenses",
                "F2D012": "total_operating_expenses",
                "F2D013": "total_nonoperating_expenses",
                "F2D014": "other_expenses_deductions",
                "F2D02": "instruction_total",
                "F2D022": "instruction_salaries",
                "F2D023": "instruction_benefits",
                "F2D024": "instruction_operations",
                "F2D03": "research_total",
                "F2D032": "research_salaries",
                "F2D033": "research_benefits",
                "F2D034": "research_operations",
                "F2D04": "public_service_total",
                "F2D042": "public_service_salaries",
                "F2D043": "public_service_benefits",
                "F2D044": "public_service_operations",
                "F2D05": "academic_support_total",
                "F2D052": "academic_support_salaries",
                "F2D053": "academic_support_benefits",
                "F2D054": "academic_support_operations",
                "F2D06": "student_services_total",
                "F2D062": "student_services_salaries",
                "F2D063": "student_services_benefits",
                "F2D064": "student_services_operations",
                "F2D07": "institutional_support_total",
                "F2D072": "institutional_support_salaries",
                "F2D073": "institutional_support_benefits",
                "F2D074": "institutional_support_operations",
                "F2D08": "auxiliary_enterprises_total",
                "F2D082": "auxiliary_salaries",
                "F2D083": "auxiliary_benefits",
                "F2D084": "auxiliary_operations",
                "F2D08A": "hospital_services_total",
                "F2D082A": "hospital_salaries",
                "F2D083A": "hospital_benefits",
                "F2D084A": "hospital_operations",
                "F2D08B": "independent_operations_total",
                "F2D082B": "independent_operations_salaries",
                "F2D083B": "independent_operations_benefits",
                "F2D084B": "independent_operations_operations",
                "F2D09": "other_core_expenses_total",
                "F2D092": "other_core_salaries",
                "F2D093": "other_core_benefits",
                "F2D094": "other_core_operations",
                # Non-core expenses
                "F2D10": "depreciation",
                "F2D102": "depreciation_buildings",
                "F2D103": "depreciation_equipment",
                "F2D104": "depreciation_other",
                "F2D11": "interest_expense",
                "F2D112": "interest_debt_financing",
                "F2D12": "other_natural_expenses",
                "F2D122": "other_natural_expenses_detail",
                # Specific function details
                "F2D13": "total_salaries_wages",
                "F2D132": "total_benefits",
                "F2D14": "operation_maintenance_plant",
                "F2D142": "operation_maintenance_salaries",
                "F2D143": "operation_maintenance_benefits",
                "F2D144": "operation_maintenance_operations",
                "F2D15": "net_grant_aid_students",
                "F2D152": "scholarships_fellowships_net",
                "F2D153": "discounts_allowances",
                "F2D154": "other_student_aid",
                "F2D16": "total_other_expenses",
                "F2D162": "other_expenses_salaries",
                "F2D163": "other_expenses_benefits",
                "F2D164": "other_expenses_operations",
                "F2D17": "total_net_other_gains_losses",
                "F2D172": "gains_losses_investments",
                "F2D173": "gains_losses_endowment",
                "F2D174": "other_nonoperating_gains_losses",
                "F2D18": "total_other_changes",
                "F2D182": "capital_appropriations",
                "F2D183": "capital_grants_gifts",
                "F2D184": "additions_permanent_endowments",
                # ========== SECTION E: NATURAL CLASSIFICATION ==========
                "F2E011": "instruction_salaries_wages",
                "F2E012": "instruction_employee_benefits",
                "F2E021": "research_salaries_wages",
                "F2E022": "research_employee_benefits",
                "F2E031": "public_service_salaries_wages",
                "F2E032": "public_service_employee_benefits",
                "F2E041": "academic_support_salaries_wages",
                "F2E042": "academic_support_employee_benefits",
                "F2E051": "student_services_salaries_wages",
                "F2E052": "student_services_employee_benefits",
                "F2E061": "institutional_support_salaries_wages",
                "F2E062": "institutional_support_employee_benefits",
                "F2E071": "auxiliary_salaries_wages",
                "F2E072": "auxiliary_employee_benefits",
                "F2E081": "net_grant_aid_salaries",
                "F2E091": "hospital_salaries_wages",
                "F2E092": "hospital_employee_benefits",
                "F2E101": "independent_operations_salaries_wages",
                "F2E102": "independent_operations_employee_benefits",
                "F2E121": "other_expenses_salaries_wages",
                "F2E122": "other_expenses_employee_benefits",
                # Total natural expenses
                "F2E131": "depreciation_total",
                "F2E132": "interest_total",
                "F2E133": "operation_maintenance_total",
                "F2E134": "all_other_expenses",
                "F2E135": "total_salaries_wages_natural",
                "F2E136": "total_employee_benefits_natural",
                "F2E137": "total_all_other_natural",
                # ========== SECTION H: ENDOWMENT ==========
                "F2FHA": "endowment_flag",
                "F2H01": "endowment_assets_boy",
                "F2H02": "endowment_assets_eoy",
                "F2H03": "total_endowment_additions",
                "F2H03A": "endowment_gifts",
                "F2H03B": "endowment_investment_gains",
                "F2H03C": "endowment_withdrawals",
                "F2H03D": "endowment_other_changes",
                # ========== SECTION I: PENSION ==========
                "F2I01": "pension_expense",
                "F2I02": "opeb_expense",
                "F2I03": "pension_plan_fiduciary_net_position",
                "F2I04": "opeb_plan_fiduciary_net_position",
                "F2I05": "pension_net_liability",
                "F2I06": "opeb_net_liability",
                "F2I07": "other_postemployment_benefits",
            }
        )
    )


def transform_completions(df: pd.DataFrame, year: int) -> pd.DataFrame:
    print(f"List of columns in the completion table: {df.columns.values}")
    """Transform C_A (Completions) data to match schema"""
    df = ensure_columns(df, ["UNITID", "AWLEVEL"], "C_A")
    # Aggregate by degree level
    grouped = df.groupby(["UNITID", "AWLEVEL"]).size().reset_index(name="count")

    pivoted = grouped.pivot(index="UNITID", columns="AWLEVEL", values="count").fillna(0)

    return (
        pivoted.assign(
            year=year,
            total_degrees=pivoted.sum(axis=1),
            associates_degrees=pivoted.get(3, 0),  # Associate's degree
            bachelors_degrees=pivoted.get(5, 0),  # Bachelor's degree
            masters_degrees=pivoted.get(7, 0),  # Master's degree
            doctoral_degrees=pivoted.get(17, 0)
            + pivoted.get(19, 0),  # Research + Professional doctorate
        )
        .reset_index()
        .rename(columns={"UNITID": "unitid"})
    )


def transform_admissions(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform ADM (Admissions) data to match schema"""
    columns = [
        "UNITID",
        "APPLCN",  # applicants
        "ADMSSN",  # admitted
        "ENRLT",  # enrolled
        "SATMT25",  # SAT Math 25th percentile
        "SATMT75",  # SAT Math 75th percentile
        "ACTCM25",  # ACT Composite 25th
        "ACTCM75",  # ACT Composite 75th
    ]
    df = ensure_columns(df, columns, "ADM")
    return (
        df[columns]
        .assign(
            year=year,
            acceptance_rate=lambda x: (x["ADMSSN"] / x["APPLCN"] * 100).round(2),
            yield_rate=lambda x: (x["ENRLT"] / x["ADMSSN"] * 100).round(2),
        )
        .rename(
            columns={
                "UNITID": "unitid",
                "APPLCN": "applicants",
                "ADMSSN": "admitted",
                "ENRLT": "enrolled",
                "ACTCM25": "act_25th_percentile",
                "ACTCM75": "act_75th_percentile",
            }
        )
    )


def main():
    year = 2023  # 2022-23 academic year

    print("Fetching IPEDS data...")
    data, column_maps = fetch_ipeds_data(year)

    print("\nTransforming data...")

    def passthrough(df: pd.DataFrame) -> pd.DataFrame:
        if "year" in df.columns:
            return df
        return df.assign(year=year)

    transforms: Dict[str, Tuple[Any, str]] = {
        "institutions": (lambda d: transform_institutions(d), "ipeds_institutions.csv"),
        "enrollment_fall": (
            lambda d: transform_enrollment(d, year),
            "ipeds_enrollment.csv",
        ),
        "staff_instructional": (
            lambda d: transform_staff(d, year),
            "ipeds_staff.csv",
        ),
        "finance_public": (
            lambda d: transform_finance(d, year),
            "ipeds_finance.csv",
        ),
        "completions": (
            lambda d: transform_completions(d, year),
            "ipeds_completions.csv",
        ),
        "admissions": (
            lambda d: transform_admissions(d, year),
            "ipeds_admissions.csv",
        ),
        "institutional_characteristics": (
            lambda d: transform_institutional_characteristics(d),
            "ipeds_institutional_characteristics.csv",
        ),
        "institutional_characteristics_ay": (
            lambda d: transform_tuition(d, year),
            "ipeds_tuition_fees.csv",
        ),
        "graduation_rates": (
            lambda d: transform_graduation_rates(d, year),
            "ipeds_graduation_rates.csv",
        ),
        "graduation_rates_pell": (
            lambda d: transform_graduation_pell(d, year),
            "ipeds_graduation_pell.csv",
        ),
        "salaries_instructional": (
            lambda d: transform_salaries(d, year),
            "ipeds_faculty_salaries.csv",
        ),
        "financial_aid_summary": (
            lambda d: transform_financial_aid(d, year),
            "ipeds_financial_aid.csv",
        ),
        "outcome_measures": (
            lambda d: transform_outcome_measures(d, year),
            "ipeds_outcome_measures.csv",
        ),
        "academic_libraries": (
            lambda d: transform_libraries(d, year),
            "ipeds_academic_libraries.csv",
        ),
    }

    for key, df in data.items():
        if df is None:
            continue
        if key in transforms:
            transform_fn, filename = transforms[key]
            transformed = transform_fn(df)
        else:
            filename = f"ipeds_{key}.csv"
            transformed = passthrough(df)
        transformed.to_csv(filename, index=False)
        print(f"✓ Saved {len(transformed)} records to {filename}")
        if key not in transforms:
            mapping = column_maps.get(key)
            if mapping:
                lines = ["column\tlabel"]
                lines.extend(f"{col}\t{label}" for col, label in mapping.items())
                column_path = f"ipeds_{key}_columns.txt"
                Path(column_path).write_text("\n".join(lines))
                print(f"✓ Saved column map to {column_path}")

    print("\n✓ All data exported to CSV files")
    print("Import to Postgres with:")
    print("  psql -d nsf_scraper -f import_ipeds.sql")


# ========== TRANSFORMATION FUNCTIONS ==========


def ensure_columns(df: pd.DataFrame, columns: List[str], label: str) -> pd.DataFrame:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        print(f"{label} missing columns: {missing}")
        for col in missing:
            df[col] = pd.NA
    return df


def transform_institutional_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    """Transform IC (Institutional Characteristics) data"""
    print(f"Columns in IC: {df.columns.values[:20]}...")  # First 20 columns
    columns = [
        "UNITID",
        "OPENADMP",  # Open admission policy
        "CREDITS1",  # Credit for life experience
        "CREDITS2",  # Credit by examination
        "CREDITS3",  # Credit for military training
        "CREDITS4",  # Credit for online courses
        "SLO5",  # Student learning outcomes
        "SLO7",  # Assessment of student learning
        "CALSYS",  # Calendar system
        "YRSCOLL",  # Years of college required
        "APPLFEEU",  # Undergrad application fee
        "APPLFEEG",  # Graduate application fee
        "ROOM",  # Room capacity
        "BOARD",  # Board capacity
        "ROOMCAP",  # Room capacity number
        "BOARDCAP",  # Board capacity number
        "ROOMAMT",  # Room charge
        "BOARDAMT",  # Board charge
    ]
    df = ensure_columns(df, columns, "IC")

    return df[columns].rename(
        columns={
            "UNITID": "unitid",
            "OPENADMP": "open_admission",
            "CREDITS1": "credit_life_experience",
            "CREDITS2": "credit_exam",
            "CREDITS3": "credit_military",
            "CREDITS4": "credit_online",
            "SLO5": "student_learning_outcomes",
            "SLO7": "learning_assessment",
            "CALSYS": "calendar_system",
            "YRSCOLL": "years_college_required",
            "APPLFEEU": "undergrad_application_fee",
            "APPLFEEG": "grad_application_fee",
            "ROOM": "room_offered",
            "BOARD": "board_offered",
            "ROOMCAP": "room_capacity",
            "BOARDCAP": "board_capacity",
            "ROOMAMT": "room_charge",
            "BOARDAMT": "board_charge",
        }
    )


def transform_tuition(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform IC_AY (Tuition and Fees) data"""
    print(f"Columns in tuition: {df.columns.values[:20]}...")

    return (
        ensure_columns(
            df,
            [
                "UNITID",
                "TUITION1",  # Published in-district tuition
                "TUITION2",  # Published in-state tuition
                "TUITION3",  # Published out-of-state tuition
                "FEE1",  # Required fees in-district
                "FEE2",  # Required fees in-state
                "FEE3",  # Required fees out-of-state
                "HRCHG1",  # Per credit hour charge in-district
                "HRCHG2",  # Per credit hour in-state
                "HRCHG3",  # Per credit hour out-of-state
                "TUITION5",  # Graduate in-state
                "TUITION6",  # Graduate out-of-state
                "FEE5",  # Graduate required fees in-state
                "FEE6",  # Graduate required fees out-of-state
            ],
            "IC_AY",
        )[
            [
                "UNITID",
                "TUITION1",
                "TUITION2",
                "TUITION3",
                "FEE1",
                "FEE2",
                "FEE3",
                "HRCHG1",
                "HRCHG2",
                "HRCHG3",
                "TUITION5",
                "TUITION6",
                "FEE5",
                "FEE6",
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "TUITION1": "tuition_in_district",
                "TUITION2": "tuition_in_state",
                "TUITION3": "tuition_out_of_state",
                "FEE1": "fees_in_district",
                "FEE2": "fees_in_state",
                "FEE3": "fees_out_of_state",
                "HRCHG1": "per_credit_in_district",
                "HRCHG2": "per_credit_in_state",
                "HRCHG3": "per_credit_out_of_state",
                "TUITION5": "grad_tuition_in_state",
                "TUITION6": "grad_tuition_out_of_state",
                "FEE5": "grad_fees_in_state",
                "FEE6": "grad_fees_out_of_state",
            }
        )
    )


def transform_graduation_rates(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform GR (Graduation Rates) data"""
    print(f"Columns in graduation: {df.columns.values[:20]}...")

    columns = [
        "UNITID",
        "GRTYPE",  # Cohort type
        "GRCOHRT",  # Adjusted cohort
        "GRTOTLT",  # Grand total completers
        "GRTOTLM",  # Grand total men
        "GRTOTLW",  # Grand total women
        "GRRACE15",  # Nonresident alien completers
        "GRRACE16",  # Hispanic/Latino completers
        "GRRACE17",  # American Indian completers
        "GRRACE18",  # Asian completers
        "GRRACE19",  # Black completers
        "GRRACE20",  # Native Hawaiian completers
        "GRRACE21",  # White completers
        "GRRACE22",  # Two or more races completers
        "GRRACE23",  # Race unknown completers
    ]
    df = ensure_columns(df, columns, "GR")

    return (
        df[columns]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "GRTYPE": "cohort_type",
                "GRCOHRT": "cohort_size",
                "GRTOTLT": "completers_total",
                "GRTOTLM": "completers_men",
                "GRTOTLW": "completers_women",
                "GRRACE15": "completers_nonresident",
                "GRRACE16": "completers_hispanic",
                "GRRACE17": "completers_american_indian",
                "GRRACE18": "completers_asian",
                "GRRACE19": "completers_black",
                "GRRACE20": "completers_hawaiian",
                "GRRACE21": "completers_white",
                "GRRACE22": "completers_two_or_more",
                "GRRACE23": "completers_unknown",
            }
        )
    )


def transform_graduation_pell(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform GR_PELL_SSL (Graduation by Pell/Loan status)"""
    print(f"Columns in grad pell: {df.columns.values[:20]}...")

    columns = [
        "UNITID",
        "PGRTYPE",  # Type
        "PGCOHRT",  # Adjusted cohort (Pell)
        "PGTOTLT",  # Pell recipients completed
        "PGTOTLM",  # Pell men
        "PGTOTLW",  # Pell women
        "SGCOHRT",  # Subsidized loan cohort
        "SGTOTLT",  # Subsidized loan completed
        "SGTOTLM",  # Subsidized loan men
        "SGTOTLW",  # Subsidized loan women
    ]
    df = ensure_columns(df, columns, "GR_PELL_SSL")

    return (
        df[columns]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "PGRTYPE": "cohort_type",
                "PGCOHRT": "pell_cohort_size",
                "PGTOTLT": "pell_completers_total",
                "PGTOTLM": "pell_completers_men",
                "PGTOTLW": "pell_completers_women",
                "SGCOHRT": "loan_cohort_size",
                "SGTOTLT": "loan_completers_total",
                "SGTOTLM": "loan_completers_men",
                "SGTOTLW": "loan_completers_women",
            }
        )
    )


def transform_salaries(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform SAL_IS (Faculty Salaries)"""
    print(f"Columns in salaries: {df.columns.values[:20]}...")

    return (
        ensure_columns(
            df,
            [
                "UNITID",
                "ARANK",  # Academic rank
                "SALTOTL",  # Number on salary
                "SALARY",  # Average salary
                "SALGEND",  # Gender
            ],
            "SAL_IS",
        )[
            [
                "UNITID",
                "ARANK",
                "SALTOTL",
                "SALARY",
                "SALGEND",
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "ARANK": "academic_rank",
                "SALTOTL": "faculty_count",
                "SALARY": "average_salary",
                "SALGEND": "gender",
            }
        )
    )


def transform_financial_aid(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform SFAV (Student Financial Aid)"""
    print(f"Columns in financial aid: {df.columns.values[:20]}...")

    return (
        ensure_columns(
            df,
            [
                "UNITID",
                "SCUGRAD",  # Undergrads receiving aid
                "SCUGFFN",  # Full-time first-time receiving aid
                "SCFA1N",  # Number receiving federal grant aid
                "SCFA1P",  # Percent receiving federal grant aid
                "SCFA2N",  # Number receiving Pell grants
                "SCFA2P",  # Percent receiving Pell
                "SCFA11N",  # Number receiving state/local grants
                "SCFA11P",  # Percent receiving state/local
                "SCFA12N",  # Number receiving institutional grants
                "SCFA12P",  # Percent receiving institutional
                "SCFA13N",  # Number receiving federal loans
                "SCFA13P",  # Percent receiving loans
                "UAGRNTN",  # Number receiving grant aid
                "UAGRNTP",  # Percent receiving grants
                "UAGRNTA",  # Average grant aid amount
                "ANYAIDN",  # Number receiving any aid
                "ANYAIDP",  # Percent receiving any aid
            ],
            "SFAV",
        )[
            [
                "UNITID",
                "SCUGRAD",
                "SCUGFFN",
                "SCFA1N",
                "SCFA1P",
                "SCFA2N",
                "SCFA2P",
                "SCFA11N",
                "SCFA11P",
                "SCFA12N",
                "SCFA12P",
                "SCFA13N",
                "SCFA13P",
                "UAGRNTN",
                "UAGRNTP",
                "UAGRNTA",
                "ANYAIDN",
                "ANYAIDP",
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "SCUGRAD": "undergrads_total",
                "SCUGFFN": "fulltime_firsttime_total",
                "SCFA1N": "federal_grant_recipients",
                "SCFA1P": "federal_grant_percent",
                "SCFA2N": "pell_recipients",
                "SCFA2P": "pell_percent",
                "SCFA11N": "state_local_grant_recipients",
                "SCFA11P": "state_local_grant_percent",
                "SCFA12N": "institutional_grant_recipients",
                "SCFA12P": "institutional_grant_percent",
                "SCFA13N": "loan_recipients",
                "SCFA13P": "loan_percent",
                "UAGRNTN": "grant_aid_recipients",
                "UAGRNTP": "grant_aid_percent",
                "UAGRNTA": "average_grant_amount",
                "ANYAIDN": "any_aid_recipients",
                "ANYAIDP": "any_aid_percent",
            }
        )
    )


def transform_outcome_measures(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform OM (Outcome Measures) - 8 year outcomes"""
    print(f"Columns in outcomes: {df.columns.values[:20]}...")

    return (
        ensure_columns(
            df,
            [
                "UNITID",
                "OMCHRT",  # Adjusted cohort
                "OMAWDP8",  # Award within 8 years percent
                "OMAWDM8",  # Award men 8 years
                "OMAWDW8",  # Award women 8 years
                "OMENRP8",  # Still enrolled at 8 years percent
                "OMENRM8",  # Men enrolled 8 years
                "OMENRW8",  # Women enrolled 8 years
                "OMNRTP8",  # Neither completed nor enrolled
            ],
            "OM",
        )[
            [
                "UNITID",
                "OMCHRT",
                "OMAWDP8",
                "OMAWDM8",
                "OMAWDW8",
                "OMENRP8",
                "OMENRM8",
                "OMENRW8",
                "OMNRTP8",
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "OMCHRT": "outcome_cohort_size",
                "OMAWDP8": "completed_8yr_percent",
                "OMAWDM8": "completed_8yr_men",
                "OMAWDW8": "completed_8yr_women",
                "OMENRP8": "enrolled_8yr_percent",
                "OMENRM8": "enrolled_8yr_men",
                "OMENRW8": "enrolled_8yr_women",
                "OMNRTP8": "neither_8yr_percent",
            }
        )
    )


def transform_libraries(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform AL (Academic Libraries)"""
    print(f"Columns in libraries: {df.columns.values[:20]}...")

    return (
        ensure_columns(
            df,
            [
                "UNITID",
                "LSTBOOK",  # Books, physical
                "LEBOOKS",  # E-books
                "LSERDL",  # Serials, digital
                "LSERPR",  # Serials, print
                "LDBASES",  # Databases
                "LVIDEO",  # Video materials
                "LAUDIO",  # Audio materials
                "LTOTEXP",  # Total library expenses
                "LSTEXP",  # Staff expenses
                "LCOLEXP",  # Collection expenses
                "LOPEXP",  # Operations expenses
                "LSTFFTE",  # FTE librarians
                "LIBTOTH",  # Service hours per year
            ],
            "AL",
        )[
            [
                "UNITID",
                "LSTBOOK",
                "LEBOOKS",
                "LSERDL",
                "LSERPR",
                "LDBASES",
                "LVIDEO",
                "LAUDIO",
                "LTOTEXP",
                "LSTEXP",
                "LCOLEXP",
                "LOPEXP",
                "LSTFFTE",
                "LIBTOTH",
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "LSTBOOK": "books_physical",
                "LEBOOKS": "books_electronic",
                "LSERDL": "serials_digital",
                "LSERPR": "serials_print",
                "LDBASES": "databases",
                "LVIDEO": "video_materials",
                "LAUDIO": "audio_materials",
                "LTOTEXP": "total_expenses",
                "LSTEXP": "staff_expenses",
                "LCOLEXP": "collection_expenses",
                "LOPEXP": "operations_expenses",
                "LSTFFTE": "librarian_fte",
                "LIBTOTH": "service_hours_per_year",
            }
        )
    )


if __name__ == "__main__":
    main()
