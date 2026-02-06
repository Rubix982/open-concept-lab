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
    transformed_year = int(str(year).replace("0", "2", -1))
    files = {
        "institutions": f"HD{year}",
        "enrollment": f"EF{year}A",
        "staff": f"S{year}_IS",
        "finance": [
            f"F{transformed_year}_F2",
            f"F{transformed_year}_F1A",
            f"F{transformed_year}",
        ],
        "completions": f"C{year}_A",
        "admissions": f"ADM{year}",
        "financial_aid": [
            f"SFAV{transformed_year}",
            f"SFA{transformed_year}_P1",
            f"SFA{transformed_year}_P2",
        ],
    }

    dataframes = {}

    for key, file_codes in files.items():
        # Handle both single file code and list of file codes
        if isinstance(file_codes, str):
            file_codes = [file_codes]

        loaded = False

        for file_code in file_codes:
            sources = [f"{wayback_url}/{file_code}.zip"]

            for source_url in sources:
                try:
                    print(f"Downloading {key} from {source_url}...")

                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()

                    # Extract CSV from zip
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        file_list = z.namelist()
                        print(f"  Files in archive: {file_list}")

                        csv_files = [f for f in file_list if f.lower().endswith(".csv")]

                        if not csv_files:
                            print(f"  ✗ No CSV file found in archive")
                            continue

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

            if loaded:
                break  # Stop trying other file codes if we found one

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
