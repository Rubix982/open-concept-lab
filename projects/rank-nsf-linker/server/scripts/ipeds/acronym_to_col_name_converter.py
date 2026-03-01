# IPEDS Completions Column → SQL-friendly name decoder

from typing import List

SPECIAL_FLAGS = {
    "UNITID": "institution_id",
    "COHRTSTU": "cohort_students",
    "F1GASBAL": "financial_gasb_balance_sheet_applicable",
    "F2PELL": "pell_grant_reporter",
    "FORM_F": "finance_form_type",
    "FTEMP15": "full_time_employees_15_or_more",
    "FYBEG": "fiscal_year_begin_month",
    "FYEND": "fiscal_year_end_month",
    "FYRPYEAR": "fiscal_year_reporting_year",
    "F_ATHLTC": "athletics_reported",
    "GPFS": "generally_accepted_accounting_principles",
    "GRDISURL": "graduation_rate_disclosure_url",
    "HASGRURL": "has_graduation_rate_url",
    "LONGPGM": "longest_program_weeks",
    "NTRLDSTR": "natural_disaster_flag",
    "SA_EXCL": "student_aid_exclusion_flag",
    # IDX — survey index/record exists
    "IDX_C": "idx_completions",
    "IDX_E12": "idx_enrollment_12month",
    "IDX_EF": "idx_enrollment_fall",
    "IDX_F": "idx_finance",
    "IDX_GR": "idx_graduation_rates",
    "IDX_GR2": "idx_graduation_rates_200pct",
    "IDX_HR": "idx_human_resources",
    "IDX_SFA": "idx_student_financial_aid",
    # IMP — imputation applied
    "IMP_C": "imputed_completions",
    "IMP_E12": "imputed_enrollment_12month",
    "IMP_EF": "imputed_enrollment_fall",
    "IMP_F": "imputed_finance",
    "IMP_GR": "imputed_graduation_rates",
    "IMP_GR2": "imputed_graduation_rates_200pct",
    "IMP_HR": "imputed_human_resources",
    "IMP_IC": "imputed_institutional_characteristics",
    "IMP_SFA": "imputed_student_financial_aid",
    # LOCK — data locked
    "LOCK_C": "locked_completions",
    "LOCK_E12": "locked_enrollment_12month",
    "LOCK_EF": "locked_enrollment_fall",
    "LOCK_F": "locked_finance",
    "LOCK_GR": "locked_graduation_rates",
    "LOCK_GR2": "locked_graduation_rates_200pct",
    "LOCK_HR": "locked_human_resources",
    "LOCK_IC": "locked_institutional_characteristics",
    "LOCK_SFA": "locked_student_financial_aid",
    # REV — revised data
    "REV_C": "revised_completions",
    "REV_E12": "revised_enrollment_12month",
    "REV_EF": "revised_enrollment_fall",
    "REV_F": "revised_finance",
    "REV_GR": "revised_graduation_rates",
    "REV_GR2": "revised_graduation_rates_200pct",
    "REV_HR": "revised_human_resources",
    "REV_IC": "revised_institutional_characteristics",
    "REV_SFA": "revised_student_financial_aid",
    # PRCH — prior year change
    "PRCH_C": "prior_yr_change_completions",
    "PRCH_E12": "prior_yr_change_enrollment_12month",
    "PRCH_EF": "prior_yr_change_enrollment_fall",
    "PRCH_F": "prior_yr_change_finance",
    "PRCH_GR": "prior_yr_change_graduation_rates",
    "PRCH_GR2": "prior_yr_change_graduation_rates_200pct",
    "PRCH_HR": "prior_yr_change_human_resources",
    "PRCH_SFA": "prior_yr_change_student_financial_aid",
    # STAT — submission status
    "STAT_C": "status_completions",
    "STAT_E12": "status_enrollment_12month",
    "STAT_EAP": "status_employees_assigned_position",
    "STAT_EF": "status_enrollment_fall",
    "STAT_F": "status_finance",
    "STAT_GR": "status_graduation_rates",
    "STAT_GR2": "status_graduation_rates_200pct",
    "STAT_HR": "status_human_resources",
    "STAT_IC": "status_institutional_characteristics",
    "STAT_S": "status_fall_staff",
    "STAT_SA": "status_student_aid",
    "STAT_SFA": "status_student_financial_aid",
    # PC*_F — percent change flags
    "PCC_F": "pct_change_completions",
    "PCE12_F": "pct_change_enrollment_12month",
    "PCEF_F": "pct_change_enrollment_fall",
    "PCF_F": "pct_change_finance",
    "PCF_F_RV": "pct_change_finance_revised",
    "PCGR_F": "pct_change_graduation_rates",
    "PCHR_F": "pct_change_human_resources",
    "PCSFA_F": "pct_change_student_financial_aid",
    # RE — response/edit flags
    "RE_C": "response_edit_completions",
    "RE_E12": "response_edit_enrollment_12month",
    "RE_GR": "response_edit_graduation_rates",
    # PT*_EF — part-time enrollment flags
    "PTA99_EF": "parttime_attendance_99_enrollment_fall",
    "PTACIPEF": "parttime_attendance_cip_enrollment_fall",
    "PTB_EF": "parttime_flag_b_enrollment_fall",
    "PTC_EF": "parttime_flag_c_enrollment_fall",
    "PTD_EF": "parttime_flag_d_enrollment_fall",
}

SPECIAL_EF_FALL = {
    "EFALEVEL": "enrollment_level",  # level of student (undergrad/grad/etc.)
    "SECTION": "attendance_status",  # full-time / part-time section
}

SPECIAL_EF_RESIDENCE = {
    "EFRES01": "enrollment_in_state",
    "EFRES02": "enrollment_out_of_state",
    "XEFRES01": "flag_enrollment_in_state",
    "XEFRES02": "flag_enrollment_out_of_state",
}

SPECIAL_EF_FULL = {
    # Cohort / entering students
    "GRCOHRT": "cohort_ftft_degree_seeking_undergrad",  # full-time first-time GRS cohort
    "PGRCOHRT": "cohort_as_pct_of_entering_class",  # GRS cohort % of entering class
    "UGENTERN": "total_entering_undergrad_students",  # total entering undergrad, fall
    # Full-time retention cohort (prior year)
    "RRFTCT": "cohort_fulltime_prior_fall",  # full-time prior fall cohort
    "RRFTEX": "cohort_fulltime_prior_fall_exclusions",  # exclusions from FT cohort
    "RRFTCTA": "cohort_fulltime_prior_fall_adjusted",  # adjusted FT cohort
    # Part-time retention cohort (prior year)
    "RRPTCT": "cohort_parttime_prior_fall",
    "RRPTEX": "cohort_parttime_prior_fall_exclusions",
    "RRPTCTA": "cohort_parttime_prior_fall_adjusted",
    # Retained students (enrolled current fall from prior cohort)
    "RET_NMF": "retained_from_fulltime_cohort",  # FT cohort students still enrolled
    "RET_NMP": "retained_from_parttime_cohort",  # PT cohort students still enrolled
    # Retention rates
    "RET_PCF": "retention_rate_fulltime",  # full-time retention rate (%)
    "RET_PCP": "retention_rate_parttime",  # part-time retention rate (%)
    # Student-to-faculty ratio
    "STUFACR": "student_to_faculty_ratio",
    # Imputation flags
    "XGRCOHRT": "flag_cohort_ftft_degree_seeking_undergrad",
    "XPGRCOHR": "flag_cohort_as_pct_of_entering_class",
    "XUGENTER": "flag_total_entering_undergrad_students",
    "XRRFTCT": "flag_cohort_fulltime_prior_fall",
    "XRRFTEX": "flag_cohort_fulltime_prior_fall_exclusions",
    "XRRFTCTA": "flag_cohort_fulltime_prior_fall_adjusted",
    "XRRPTCT": "flag_cohort_parttime_prior_fall",
    "XRRPTEX": "flag_cohort_parttime_prior_fall_exclusions",
    "XRRPTCTA": "flag_cohort_parttime_prior_fall_adjusted",
    "XRET_NMF": "flag_retained_from_fulltime_cohort",
    "XRET_NMP": "flag_retained_from_parttime_cohort",
    "XRET_PCF": "flag_retention_rate_fulltime",
    "XRET_PCP": "flag_retention_rate_parttime",
    "XSTUFACR": "flag_student_to_faculty_ratio",
}

SPECIAL_EFAGE = {
    # Record identifiers
    "EFBAGE": "age_category_code",  # categorical: age bracket code
    "LSTUDY": "level_of_study",  # undergrad / grad / first-professional
    "LINE": "survey_line_number",  # original line number on survey form
    # Age bracket enrollment counts (EFAGE01–09)
    # Each represents a specific age group, gender/attendance breakdown
    # Pattern: EFAGE{nn} = count for age group nn
    # 01 = Under 18, 02 = 18-19, 03 = 20-21, 04 = 22-24,
    # 05 = 25-29,   06 = 30-34, 07 = 35-39, 08 = 40-49,
    # 09 = 50-64,   (10 = 65+ if present)
    "EFAGE01": "enrollment_age_under_18",
    "EFAGE02": "enrollment_age_18_19",
    "EFAGE03": "enrollment_age_20_21",
    "EFAGE04": "enrollment_age_22_24",
    "EFAGE05": "enrollment_age_25_29",
    "EFAGE06": "enrollment_age_30_34",
    "EFAGE07": "enrollment_age_35_39",
    "EFAGE08": "enrollment_age_40_49",
    "EFAGE09": "enrollment_age_50_64",
    # Imputation flags for each
    "XEFAGE01": "flag_enrollment_age_under_18",
    "XEFAGE02": "flag_enrollment_age_18_19",
    "XEFAGE03": "flag_enrollment_age_20_21",
    "XEFAGE04": "flag_enrollment_age_22_24",
    "XEFAGE05": "flag_enrollment_age_25_29",
    "XEFAGE06": "flag_enrollment_age_30_34",
    "XEFAGE07": "flag_enrollment_age_35_39",
    "XEFAGE08": "flag_enrollment_age_40_49",
    "XEFAGE09": "flag_enrollment_age_50_64",
}

SPECIAL_EAP = {
    "EAPRECTP": "primary_function",
    "FTPT": "full_part_time_status",
    "FUNCTCD": "primary_function_occupational_activity",
    "FSTAT": "faculty_status",
    "EAPTYP": "employees_excluding_medical_school",
    "XEAPTYP": "flag_employees_excluding_medical_school",
    "EAPMED": "medical_school_employees",
    "XEAPMED": "flag_medical_school_employees",
    "EAPTOT": "total_employees",
    "XEAPTOT": "flag_total_employees",
}

SPECIAL = {
    "UNITID": "institution_id",
    "CIPCODE": "cip_code",
    "MAJORNUM": "major_num",
    "AWLEVEL": "award_level",
}

SPECIAL.update(SPECIAL_EAP)
SPECIAL.update(SPECIAL_EFAGE)
SPECIAL.update(SPECIAL_EF_FULL)
SPECIAL.update(SPECIAL_EF_RESIDENCE)
SPECIAL.update(SPECIAL_EF_FALL)
SPECIAL.update(SPECIAL_FLAGS)


RACE_PREFIX_EF = {
    "EFNRAL": "enrollment_nonresident_alien",
    "EFHISP": "enrollment_hispanic",
    "EFAIAN": "enrollment_american_indian_alaska_native",
    "EFASIA": "enrollment_asian",
    "EFBKAA": "enrollment_black_african_american",
    "EFNHPI": "enrollment_native_hawaiian_pacific_islander",
    "EFWHIT": "enrollment_white",
    "EF2MOR": "enrollment_two_or_more_races",
    "EFUNKN": "enrollment_race_unknown",
    "EFTOTL": "enrollment_total",
}

RACE_PREFIX = {
    "CNRAL": "nonresident_alien",
    "CHISP": "hispanic",
    "CAIAN": "american_indian_alaska_native",
    "CASIA": "asian",
    "CBKAA": "black_african_american",
    "CNHPI": "native_hawaiian_pacific_islander",
    "CWHIT": "white",
    "C2MOR": "two_or_more_races",
    "CUNKN": "race_unknown",
    "CTOTAL": "total",
    # Derived (old+new combined — used in IPEDS publications)
    "DVCAI": "derived_american_indian_alaska_native",
    "DVCAP": "derived_asian_pacific_islander",
    "DVCBK": "derived_black_african_american",
    "DVCHS": "derived_hispanic",
    "DVCWH": "derived_white",
    # Old race categories (pre-2010)
    "CRACE03": "old_race_american_indian_alaska_native",
    "CRACE04": "old_race_asian_pacific_islander",
    "CRACE05": "old_race_asian_pacific_islander_alt",
    "CRACE06": "old_race_black_non_hispanic",
    "CRACE07": "old_race_american_indian_alaska_native_alt",
    "CRACE08": "old_race_white_non_hispanic",
    "CRACE09": "old_race_hispanic",
    "CRACE10": "old_race_unknown",
    "CRACE11": "old_race_nonresident_alien",
    "CRACE12": "old_race_total",
    "CRACE18": "new_race_american_indian_alaska_native",
    "CRACE19": "new_race_asian",
    "CRACE20": "new_race_black_african_american",
    "CRACE21": "new_race_native_hawaiian_pacific_islander",
    "CRACE22": "new_race_white",
}

RACE_PREFIX.update(RACE_PREFIX_EF)

GENDER_SUFFIX = {
    "M": "male",
    "W": "female",
    "T": "total",
}

FIXED_RACE_CODES = {
    "CRACE03",
    "CRACE04",
    "CRACE05",
    "CRACE06",
    "CRACE07",
    "CRACE08",
    "CRACE09",
    "CRACE10",
    "CRACE11",
    "CRACE12",
    "CRACE18",
    "CRACE19",
    "CRACE20",
    "CRACE21",
    "CRACE22",
}


def decode(col: str) -> str:
    col = col.upper().strip()

    if col in SPECIAL:
        return SPECIAL[col]

    is_flag = col.startswith("X")
    base = col[1:] if is_flag else col

    if base in FIXED_RACE_CODES:
        label = RACE_PREFIX[base]
        return f"flag_{label}" if is_flag else label

    if len(base) < 2:
        return f"unknown_{col.lower()}"

    gender_char = base[-1]
    race_key = base[:-1]

    gender = GENDER_SUFFIX.get(gender_char)
    race = RACE_PREFIX.get(race_key)

    if not gender or not race:
        return f"unknown_{col.lower()}"

    # CTOTAL special case: avoid "total_total"
    if race_key in ("CTOTAL", "EFTOTL"):
        base = "total" if race_key == "CTOTAL" else "enrollment_total"
        label = base if gender == "total" else f"{base}_{gender}"
    else:
        label = f"{race}_{gender}"

    return f"flag_{label}" if is_flag else label


if __name__ == "__main__":
    all_cols: List[string] = [
        # 2010 / completions parquest
        "AWLEVEL",
        "C2MORM",
        "C2MORT",
        "C2MORW",
        "CAIANM",
        "CAIANT",
        "CAIANW",
        "CASIAM",
        "CASIAT",
        "CASIAW",
        "CBKAAM",
        "CBKAAT",
        "CBKAAW",
        "CHISPM",
        "CHISPT",
        "CHISPW",
        "CIPCODE",
        "CNHPIM",
        "CNHPIT",
        "CNHPIW",
        "CNRALM",
        "CNRALT",
        "CNRALW",
        "CRACE03",
        "CRACE04",
        "CRACE05",
        "CRACE06",
        "CRACE07",
        "CRACE08",
        "CRACE09",
        "CRACE10",
        "CRACE11",
        "CRACE12",
        "CRACE18",
        "CRACE19",
        "CRACE20",
        "CRACE21",
        "CRACE22",
        "CTOTALM",
        "CTOTALT",
        "CTOTALW",
        "CUNKNM",
        "CUNKNT",
        "CUNKNW",
        "CWHITM",
        "CWHITT",
        "CWHITW",
        "DVCAIM",
        "DVCAIT",
        "DVCAIW",
        "DVCAPM",
        "DVCAPT",
        "DVCAPW",
        "DVCBKM",
        "DVCBKT",
        "DVCBKW",
        "DVCHSM",
        "DVCHST",
        "DVCHSW",
        "DVCWHM",
        "DVCWHT",
        "DVCWHW",
        "MAJORNUM",
        "UNITID",
        "XC2MORM",
        "XC2MORT",
        "XC2MORW",
        "XCAIANM",
        "XCAIANT",
        "XCAIANW",
        "XCASIAM",
        "XCASIAT",
        "XCASIAW",
        "XCBKAAM",
        "XCBKAAT",
        "XCBKAAW",
        "XCHISPM",
        "XCHISPT",
        "XCHISPW",
        "XCNHPIM",
        "XCNHPIT",
        "XCNHPIW",
        "XCNRALM",
        "XCNRALT",
        "XCNRALW",
        "XCRACE03",
        "XCRACE04",
        "XCRACE05",
        "XCRACE06",
        "XCRACE07",
        "XCRACE08",
        "XCRACE09",
        "XCRACE10",
        "XCRACE11",
        "XCRACE12",
        "XCRACE18",
        "XCRACE19",
        "XCRACE20",
        "XCRACE21",
        "XCRACE22",
        "XCTOTALM",
        "XCTOTALT",
        "XCTOTALW",
        "XCUNKNM",
        "XCUNKNT",
        "XCUNKNW",
        "XCWHITM",
        "XCWHITT",
        "XCWHITW",
        "XDVCAIM",
        "XDVCAIT",
        "XDVCAIW",
        "XDVCAPM",
        "XDVCAPT",
        "XDVCAPW",
        "XDVCBKM",
        "XDVCBKT",
        "XDVCBKW",
        "XDVCHSM",
        "XDVCHST",
        "XDVCHSW",
        "XDVCWHM",
        "XDVCWHT",
        "XDVCWHW",
        # 2010 / education abroad parquet
        "UNITID",
        "EAPRECTP",
        "FTPT",
        "FUNCTCD",
        "FSTAT",
        "XEAPTYP",
        "EAPTYP",
        "XEAPMED",
        "EAPMED",
        "XEAPTOT",
        "EAPTOT",
        # 2010 / enrollment fall age parquet
        "UNITID",
        "EFBAGE",
        "LINE",
        "LSTUDY",
        "XEFAGE01",
        "EFAGE01",
        "XEFAGE02",
        "EFAGE02",
        "XEFAGE03",
        "EFAGE03",
        "XEFAGE04",
        "EFAGE04",
        "XEFAGE05",
        "EFAGE05",
        "XEFAGE06",
        "EFAGE06",
        "XEFAGE07",
        "EFAGE07",
        "XEFAGE08",
        "EFAGE08",
        "XEFAGE09",
        "EFAGE09",
        # 2010 / enrollment fall full parquet
        "GRCOHRT",
        "PGRCOHRT",
        "RET_NMF",
        "RET_NMP",
        "RET_PCF",
        "RET_PCP",
        "RRFTCT",
        "RRFTCTA",
        "RRFTEX",
        "RRPTCT",
        "RRPTCTA",
        "RRPTEX",
        "STUFACR",
        "UGENTERN",
        "UNITID",
        "XGRCOHRT",
        "XPGRCOHR",
        "XRET_NMF",
        "XRET_NMP",
        "XRET_PCF",
        "XRET_PCP",
        "XRRFTCT",
        "XRRFTCTA",
        "XRRFTEX",
        "XRRPTCT",
        "XRRPTCTA",
        "XRRPTEX",
        "XSTUFACR",
        "XUGENTER",
        # 2010 / entollment fall residence parquet
        "UNITID",
        "EFCSTATE",
        "LINE",
        "XEFRES01",
        "EFRES01",
        "XEFRES02",
        "EFRES02",
        # 2010 / enrollment fall parquet
        "EF2MORM",
        "EF2MORT",
        "EF2MORW",
        "EFAIANM",
        "EFAIANT",
        "EFAIANW",
        "EFALEVEL",
        "EFASIAM",
        "EFASIAT",
        "EFASIAW",
        "EFBKAAM",
        "EFBKAAT",
        "EFBKAAW",
        "EFHISPM",
        "EFHISPT",
        "EFHISPW",
        "EFNHPIM",
        "EFNHPIT",
        "EFNHPIW",
        "EFNRALM",
        "EFNRALT",
        "EFNRALW",
        "EFTOTLM",
        "EFTOTLT",
        "EFTOTLW",
        "EFUNKNM",
        "EFUNKNT",
        "EFUNKNW",
        "EFWHITM",
        "EFWHITT",
        "EFWHITW",
        "LINE",
        "LSTUDY",
        "SECTION",
        "UNITID",
        "XEF2MORM",
        "XEF2MORT",
        "XEF2MORW",
        "XEFAIANM",
        "XEFAIANT",
        "XEFAIANW",
        "XEFASIAM",
        "XEFASIAT",
        "XEFASIAW",
        "XEFBKAAM",
        "XEFBKAAT",
        "XEFBKAAW",
        "XEFHISPM",
        "XEFHISPT",
        "XEFHISPW",
        "XEFNHPIM",
        "XEFNHPIT",
        "XEFNHPIW",
        "XEFNRALM",
        "XEFNRALT",
        "XEFNRALW",
        "XEFTOTLM",
        "XEFTOTLT",
        "XEFTOTLW",
        "XEFUNKNM",
        "XEFUNKNT",
        "XEFUNKNW",
        "XEFWHITM",
        "XEFWHITT",
        "XEFWHITW",
        # 2010 / flags parquet
        "COHRTSTU",
        "F1GASBAL",
        "F2PELL",
        "FORM_F",
        "FTEMP15",
        "FYBEG",
        "FYEND",
        "FYRPYEAR",
        "F_ATHLTC",
        "GPFS",
        "GRDISURL",
        "HASGRURL",
        "IDX_C",
        "IDX_E12",
        "IDX_EF",
        "IDX_F",
        "IDX_GR",
        "IDX_GR2",
        "IDX_HR",
        "IDX_SFA",
        "IMP_C",
        "IMP_E12",
        "IMP_EF",
        "IMP_F",
        "IMP_GR",
        "IMP_GR2",
        "IMP_HR",
        "IMP_IC",
        "IMP_SFA",
        "LOCK_C",
        "LOCK_E12",
        "LOCK_EF",
        "LOCK_F",
        "LOCK_GR",
        "LOCK_GR2",
        "LOCK_HR",
        "LOCK_IC",
        "LOCK_SFA",
        "LONGPGM",
        "NTRLDSTR",
        "PCC_F",
        "PCE12_F",
        "PCEF_F",
        "PCF_F",
        "PCF_F_RV",
        "PCGR_F",
        "PCHR_F",
        "PCSFA_F",
        "PRCH_C",
        "PRCH_E12",
        "PRCH_EF",
        "PRCH_F",
        "PRCH_GR",
        "PRCH_GR2",
        "PRCH_HR",
        "PRCH_SFA",
        "PTA99_EF",
        "PTACIPEF",
        "PTB_EF",
        "PTC_EF",
        "PTD_EF",
        "REV_C",
        "REV_E12",
        "REV_EF",
        "REV_F",
        "REV_GR",
        "REV_GR2",
        "REV_HR",
        "REV_IC",
        "REV_SFA",
        "RE_C",
        "RE_E12",
        "RE_GR",
        "SA_EXCL",
        "STAT_C",
        "STAT_E12",
        "STAT_EAP",
        "STAT_EF",
        "STAT_F",
        "STAT_GR",
        "STAT_GR2",
        "STAT_HR",
        "STAT_IC",
        "STAT_S",
        "STAT_SA",
        "STAT_SFA",
        "UNITID",
    ]

    print(f"{'Original':<12} -> SQL Name")
    print("-" * 55)
    for c in all_cols:
        print(f"{c:<12} -> {decode(c)}")
