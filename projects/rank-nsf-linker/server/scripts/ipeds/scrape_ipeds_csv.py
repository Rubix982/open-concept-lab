#!/usr/bin/env python3
"""
IPEDS Data Fetcher
Downloads and parses IPEDS data files for a given year
"""

import requests
import pandas as pd
import io
import zipfile
from typing import Dict, Any


def fetch_ipeds_data(year: int = 2023) -> Dict[str, pd.DataFrame]:
    """
    Download IPEDS data files and return as DataFrames
    Year format: 2023 means 2022-23 academic year
    """

    base_url = "https://nces.ed.gov/ipeds/datacenter/data"
    wayback_url = f"https://web.archive.org/web/20240822183521/{base_url}"

    # IPEDS file codes for different surveys
    files = {
        "institutions": f"HD{year}",
        "enrollment": f"EF{year}A",
        "staff": f"S{year}_IS",
        "finance": f"F{year}_F2",
        "completions": f"C{year}_A",
        "admissions": f"ADM{year}",
        "financial_aid": f"SFA{year}",
    }

    dataframes = {}

    for key, file_code in files.items():
        sources = [f"{wayback_url}/{file_code}.zip"]

        loaded = False

        for source_url in sources:
            try:
                print(f"Downloading {key} from {source_url}...")

                response = requests.get(source_url, timeout=30)
                response.raise_for_status()

                # Extract CSV from zip
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # List all files in the zip
                    file_list = z.namelist()
                    print(f"  Files in archive: {file_list}")

                    # Find the CSV file (might have different naming)
                    csv_files = [f for f in file_list if f.lower().endswith(".csv")]

                    if not csv_files:
                        print(f"  ✗ No CSV file found in archive")
                        continue

                    # Use the first CSV file found
                    csv_name = csv_files[0]
                    print(f"  Reading: {csv_name}")

                    with z.open(csv_name) as csv_file:
                        df = pd.read_csv(csv_file, encoding="latin1")
                        dataframes[key] = df
                        print(f"✓ Loaded {len(df)} rows for {key}")
                        loaded = True
                        break

            except requests.exceptions.RequestException as e:
                print(f"✗ Failed from {source_url}: {e}")
                continue

            except (zipfile.BadZipFile, KeyError) as e:
                print(f"✗ Invalid zip file from {source_url}: {e}")
                continue

        if not loaded:
            print(f"✗ All sources failed for {key}")
            dataframes[key] = None

    return dataframes


def transform_institutions(df: pd.DataFrame) -> pd.DataFrame:
    """Transform HD (Directory) data to match schema"""
    print(f"List of columns in institutions: {df.columns.values}")
    return df[
        [
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
    ].rename(
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
    print(f"Unique SISCAT values: {df['SISCAT'].unique()}")
    print(f"Unique FACSTAT values: {df['FACSTAT'].unique()}")
    print(f"Unique ARANK values: {df['ARANK'].unique()}")

    # SISCAT codes (staff category):
    # 2310 = Instructional staff total
    # 2320 = Research staff
    # 2330 = Public service staff
    # etc.

    # FACSTAT codes (faculty status):
    # 10 = All faculty and staff
    # 20 = Tenured
    # 30 = On tenure track
    # 40 = Not on tenure track
    # 50 = Without faculty status

    # ARANK codes (academic rank):
    # 10 = All ranks
    # 20 = Professors
    # 30 = Associate professors
    # 40 = Assistant professors
    # 50 = Instructors
    # 60 = Lecturers
    # 70 = No academic rank

    # Get total instructional staff (all ranks, all faculty status)
    instructional_total = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 10) & (df["ARANK"] == 10)
    ][["UNITID", "HRTOTLT", "HRTOTLM", "HRTOTLW"]].copy()

    # Get tenured faculty
    tenured = df[(df["SISCAT"] == 2310) & (df["FACSTAT"] == 20) & (df["ARANK"] == 10)][
        ["UNITID", "HRTOTLT"]
    ].copy()

    # Get tenure-track faculty
    tenure_track = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 30) & (df["ARANK"] == 10)
    ][["UNITID", "HRTOTLT"]].copy()

    # Get research staff (if available)
    research = (
        df[(df["SISCAT"] == 2320) & (df["FACSTAT"] == 10) & (df["ARANK"] == 10)][
            ["UNITID", "HRTOTLT"]
        ].copy()
        if 2320 in df["SISCAT"].values
        else None
    )

    # Build result
    result = instructional_total.rename(
        columns={
            "UNITID": "unitid",
            "HRTOTLT": "instructional_staff_total",
            "HRTOTLM": "instructional_staff_men",
            "HRTOTLW": "instructional_staff_women",
        }
    )

    # Add tenure info
    if not tenured.empty:
        tenured = tenured.rename(
            columns={"UNITID": "unitid", "HRTOTLT": "tenured_faculty"}
        )
        result = result.merge(tenured, on="unitid", how="left")

    if not tenure_track.empty:
        tenure_track = tenure_track.rename(
            columns={"UNITID": "unitid", "HRTOTLT": "tenure_track_faculty"}
        )
        result = result.merge(tenure_track, on="unitid", how="left")

    if research is not None and not research.empty:
        research = research.rename(
            columns={"UNITID": "unitid", "HRTOTLT": "research_staff"}
        )
        result = result.merge(research, on="unitid", how="left")

    # Add faculty by rank
    professors = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 10) & (df["ARANK"] == 20)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "professors"}
    )

    associate_profs = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 10) & (df["ARANK"] == 30)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "associate_professors"}
    )

    assistant_profs = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 10) & (df["ARANK"] == 40)
    ][["UNITID", "HRTOTLT"]].rename(
        columns={"UNITID": "unitid", "HRTOTLT": "assistant_professors"}
    )

    result = result.merge(professors, on="unitid", how="left")
    result = result.merge(associate_profs, on="unitid", how="left")
    result = result.merge(assistant_profs, on="unitid", how="left")

    # Add demographics for instructional staff
    demographics = df[
        (df["SISCAT"] == 2310) & (df["FACSTAT"] == 10) & (df["ARANK"] == 10)
    ][
        [
            "UNITID",
            "HRAIANT",  # American Indian
            "HRASIAT",  # Asian
            "HRBKAAT",  # Black
            "HRHISPT",  # Hispanic
            "HRWHITT",  # White
            "HR2MORT",  # Two or more races
            "HRNRALT",  # Non-resident alien
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

    result = result.merge(demographics, on="unitid", how="left")
    result["year"] = year

    return result


def transform_finance(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform F_F2 (Finance) data to match schema"""
    return (
        df[
            [
                "UNITID",
                "F2D01",  # Total revenues
                "F2C011",  # Tuition revenue
                "F2E051",  # Federal grants
                "F2E061",  # State grants
                "F2E071",  # Private grants
                "F2H01",  # Endowment income
                "F2D02",  # Total expenses
                "F2E011",  # Instruction expenses
                "F2E021",  # Research expenses
                "F2E031",  # Public service expenses
                "F2E041",  # Academic support
                "F2H02",  # Endowment assets EOY
            ]
        ]
        .assign(year=year)
        .rename(
            columns={
                "UNITID": "unitid",
                "F2D01": "total_revenues",
                "F2C011": "tuition_revenue",
                "F2E051": "federal_grants",
                "F2E061": "state_grants",
                "F2E071": "private_grants",
                "F2H01": "endowment_income",
                "F2D02": "total_expenses",
                "F2E011": "instruction_expenses",
                "F2E021": "research_expenses",
                "F2E031": "public_service_expenses",
                "F2E041": "academic_support_expenses",
                "F2H02": "endowment_assets_eoy",
            }
        )
    )


def transform_completions(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Transform C_A (Completions) data to match schema"""
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
    return (
        df[
            [
                "UNITID",
                "APPLCN",  # applicants
                "ADMSSN",  # admitted
                "ENRLT",  # enrolled
                "SATMT25",  # SAT Math 25th percentile
                "SATMT75",  # SAT Math 75th percentile
                "ACTCM25",  # ACT Composite 25th
                "ACTCM75",  # ACT Composite 75th
            ]
        ]
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
    data = fetch_ipeds_data(year)

    print("\nTransforming data...")

    if data["institutions"] is not None:
        institutions = transform_institutions(data["institutions"])
        institutions.to_csv("ipeds_institutions.csv", index=False)
        print(f"✓ Saved {len(institutions)} institutions")

    if data["enrollment"] is not None:
        enrollment = transform_enrollment(data["enrollment"], year)
        enrollment.to_csv("ipeds_enrollment.csv", index=False)
        print(f"✓ Saved {len(enrollment)} enrollment records")

    if data["staff"] is not None:
        staff = transform_staff(data["staff"], year)
        staff.to_csv("ipeds_staff.csv", index=False)
        print(f"✓ Saved {len(staff)} staff records")

    if data["finance"] is not None:
        finance = transform_finance(data["finance"], year)
        finance.to_csv("ipeds_finance.csv", index=False)
        print(f"✓ Saved {len(finance)} finance records")

    if data["completions"] is not None:
        completions = transform_completions(data["completions"], year)
        completions.to_csv("ipeds_completions.csv", index=False)
        print(f"✓ Saved {len(completions)} completion records")

    if data["admissions"] is not None:
        admissions = transform_admissions(data["admissions"], year)
        admissions.to_csv("ipeds_admissions.csv", index=False)
        print(f"✓ Saved {len(admissions)} admission records")

    print("\n✓ All data exported to CSV files")
    print(
        "Import to Postgres with: psql -d yourdb -c \"\\COPY ipeds_institutions FROM 'ipeds_institutions.csv' CSV HEADER\""
    )


if __name__ == "__main__":
    main()
