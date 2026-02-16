-- ============================================================
-- IPEDS INSTITUTIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_institutions (
    unitid INTEGER PRIMARY KEY,
    institution_name TEXT NOT NULL,
    institution_alias TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    website TEXT,
    sector INTEGER,
    institutional_level INTEGER,
    control INTEGER,
    historically_black INTEGER,
    has_hospital INTEGER,
    has_medical_school INTEGER,
    tribal_college INTEGER,
    landgrant INTEGER,
    carnegie_classification TEXT,
    locale INTEGER,
    institution_size TEXT,
    metro_area TEXT,
    county_name TEXT,
    geographic_region INTEGER,
    latitude NUMERIC,
    longitude NUMERIC,
    system_type TEXT,
    system_name TEXT
);
-- ============================================================
-- IPEDS ENROLLMENT TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_enrollment (
    unitid INTEGER,
    YEAR INTEGER,
    total_enrollment INTEGER,
    enrollment_men INTEGER,
    enrollment_women INTEGER,
    undergraduate_total INTEGER,
    graduate_total INTEGER,
    american_indian_total INTEGER,
    asian_total INTEGER,
    black_total INTEGER,
    hispanic_total INTEGER,
    white_total INTEGER,
    two_or_more_races_total INTEGER,
    nonresident_alien_total INTEGER,
    PRIMARY KEY (unitid, YEAR),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- ============================================================
-- IPEDS STAFF TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_staff (
    unitid INTEGER,
    YEAR INTEGER,
    instructional_staff_total INTEGER,
    instructional_staff_men INTEGER,
    instructional_staff_women INTEGER,
    tenured_faculty INTEGER,
    tenure_track_faculty INTEGER,
    not_tenure_track_faculty INTEGER,
    professors INTEGER,
    associate_professors INTEGER,
    assistant_professors INTEGER,
    instructors INTEGER,
    american_indian_faculty INTEGER,
    asian_faculty INTEGER,
    black_faculty INTEGER,
    hispanic_faculty INTEGER,
    white_faculty INTEGER,
    two_or_more_races_faculty INTEGER,
    nonresident_alien_faculty INTEGER,
    PRIMARY KEY (unitid, YEAR),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- ============================================================
-- IPEDS FINANCE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_finance (
    unitid INTEGER,
    YEAR INTEGER,
    -- Assets & Liabilities (Section A)
    total_assets BIGINT,
    total_liabilities BIGINT,
    net_assets BIGINT,
    current_assets BIGINT,
    long_term_investments BIGINT,
    land_buildings_equipment_net BIGINT,
    property_plant_equipment BIGINT,
    accumulated_depreciation BIGINT,
    intangible_assets_net BIGINT,
    other_noncurrent_assets BIGINT,
    deferred_outflows BIGINT,
    current_liabilities BIGINT,
    long_term_debt_current BIGINT,
    other_current_liabilities BIGINT,
    noncurrent_liabilities BIGINT,
    long_term_debt_noncurrent BIGINT,
    other_noncurrent_liabilities BIGINT,
    deferred_inflows BIGINT,
    -- Scholarships (Section B)
    federal_grants_scholarships BIGINT,
    state_local_grants_scholarships BIGINT,
    institutional_grants_scholarships BIGINT,
    total_discounts_allowances BIGINT,
    total_scholarships_fellowships BIGINT,
    net_scholarships_fellowships BIGINT,
    allowances_tuition_fees BIGINT,
    -- Revenues (Section C)
    total_revenues BIGINT,
    total_operating_revenues BIGINT,
    total_nonoperating_revenues BIGINT,
    other_revenues_additions BIGINT,
    tuition_fees_gross BIGINT,
    tuition_fees_allowances BIGINT,
    tuition_fees_net BIGINT,
    federal_appropriations BIGINT,
    state_appropriations BIGINT,
    local_appropriations BIGINT,
    federal_grants_contracts BIGINT,
    federal_operating_grants BIGINT,
    federal_nonoperating_grants BIGINT,
    state_grants_contracts BIGINT,
    state_operating_grants BIGINT,
    state_nonoperating_grants BIGINT,
    local_grants_contracts BIGINT,
    local_operating_grants BIGINT,
    local_nonoperating_grants BIGINT,
    private_gifts_grants_contracts BIGINT,
    private_operating_grants BIGINT,
    private_nonoperating_grants BIGINT,
    investment_return BIGINT,
    investment_income_operating BIGINT,
    investment_income_nonoperating BIGINT,
    other_revenues BIGINT,
    sales_services_auxiliary BIGINT,
    sales_services_hospitals BIGINT,
    -- Expenses by Function (Section D)
    total_expenses BIGINT,
    total_operating_expenses BIGINT,
    total_nonoperating_expenses BIGINT,
    other_expenses_deductions BIGINT,
    instruction_total BIGINT,
    instruction_salaries BIGINT,
    instruction_benefits BIGINT,
    instruction_operations BIGINT,
    research_total BIGINT,
    research_salaries BIGINT,
    research_benefits BIGINT,
    research_operations BIGINT,
    public_service_total BIGINT,
    public_service_salaries BIGINT,
    public_service_benefits BIGINT,
    public_service_operations BIGINT,
    academic_support_total BIGINT,
    academic_support_salaries BIGINT,
    academic_support_benefits BIGINT,
    academic_support_operations BIGINT,
    student_services_total BIGINT,
    student_services_salaries BIGINT,
    student_services_benefits BIGINT,
    student_services_operations BIGINT,
    institutional_support_total BIGINT,
    institutional_support_salaries BIGINT,
    institutional_support_benefits BIGINT,
    institutional_support_operations BIGINT,
    auxiliary_enterprises_total BIGINT,
    auxiliary_salaries BIGINT,
    auxiliary_benefits BIGINT,
    auxiliary_operations BIGINT,
    hospital_services_total BIGINT,
    hospital_salaries BIGINT,
    hospital_benefits BIGINT,
    hospital_operations BIGINT,
    independent_operations_total BIGINT,
    independent_operations_salaries BIGINT,
    independent_operations_benefits BIGINT,
    independent_operations_operations BIGINT,
    other_core_expenses_total BIGINT,
    other_core_salaries BIGINT,
    other_core_benefits BIGINT,
    other_core_operations BIGINT,
    depreciation BIGINT,
    depreciation_buildings BIGINT,
    depreciation_equipment BIGINT,
    depreciation_other BIGINT,
    interest_expense BIGINT,
    interest_debt_financing BIGINT,
    other_natural_expenses BIGINT,
    other_natural_expenses_detail BIGINT,
    total_salaries_wages BIGINT,
    total_benefits BIGINT,
    operation_maintenance_plant BIGINT,
    operation_maintenance_salaries BIGINT,
    operation_maintenance_benefits BIGINT,
    operation_maintenance_operations BIGINT,
    net_grant_aid_students BIGINT,
    scholarships_fellowships_net BIGINT,
    discounts_allowances BIGINT,
    other_student_aid BIGINT,
    total_other_expenses BIGINT,
    other_expenses_salaries BIGINT,
    other_expenses_benefits BIGINT,
    other_expenses_operations BIGINT,
    total_net_other_gains_losses BIGINT,
    gains_losses_investments BIGINT,
    gains_losses_endowment BIGINT,
    other_nonoperating_gains_losses BIGINT,
    total_other_changes BIGINT,
    capital_appropriations BIGINT,
    capital_grants_gifts BIGINT,
    additions_permanent_endowments BIGINT,
    -- Expenses by Natural Classification (Section E)
    instruction_salaries_wages BIGINT,
    instruction_employee_benefits BIGINT,
    research_salaries_wages BIGINT,
    research_employee_benefits BIGINT,
    public_service_salaries_wages BIGINT,
    public_service_employee_benefits BIGINT,
    academic_support_salaries_wages BIGINT,
    academic_support_employee_benefits BIGINT,
    student_services_salaries_wages BIGINT,
    student_services_employee_benefits BIGINT,
    institutional_support_salaries_wages BIGINT,
    institutional_support_employee_benefits BIGINT,
    auxiliary_salaries_wages BIGINT,
    auxiliary_employee_benefits BIGINT,
    net_grant_aid_salaries BIGINT,
    hospital_salaries_wages BIGINT,
    hospital_employee_benefits BIGINT,
    independent_operations_salaries_wages BIGINT,
    independent_operations_employee_benefits BIGINT,
    other_expenses_salaries_wages BIGINT,
    other_expenses_employee_benefits BIGINT,
    depreciation_total BIGINT,
    interest_total BIGINT,
    operation_maintenance_total BIGINT,
    all_other_expenses BIGINT,
    total_salaries_wages_natural BIGINT,
    total_employee_benefits_natural BIGINT,
    total_all_other_natural BIGINT,
    -- Endowment (Section H)
    endowment_flag INTEGER,
    endowment_assets_boy BIGINT,
    endowment_assets_eoy BIGINT,
    total_endowment_additions BIGINT,
    endowment_gifts BIGINT,
    endowment_investment_gains BIGINT,
    endowment_withdrawals BIGINT,
    endowment_other_changes BIGINT,
    -- Pension (Section I)
    pension_expense BIGINT,
    opeb_expense BIGINT,
    pension_plan_fiduciary_net_position BIGINT,
    opeb_plan_fiduciary_net_position BIGINT,
    pension_net_liability BIGINT,
    opeb_net_liability BIGINT,
    other_postemployment_benefits BIGINT,
    PRIMARY KEY (unitid, YEAR),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- ============================================================
-- IPEDS COMPLETIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_completions (
    unitid INTEGER,
    YEAR INTEGER,
    total_degrees INTEGER,
    associates_degrees INTEGER,
    bachelors_degrees INTEGER,
    masters_degrees INTEGER,
    doctoral_degrees INTEGER,
    -- Award level breakdown (raw AWLEVEL codes)
    award_level_2 NUMERIC,
    -- < 1 year certificate
    award_level_3 NUMERIC,
    -- 1-2 year certificate
    award_level_4 NUMERIC,
    -- 2-4 year certificate
    award_level_5 NUMERIC,
    -- Associate's
    award_level_6 NUMERIC,
    -- 1-2 year post-bacc certificate
    award_level_7 NUMERIC,
    -- Master's
    award_level_8 NUMERIC,
    -- Post-master's certificate
    award_level_17 NUMERIC,
    -- Doctor's research/scholarship
    award_level_18 NUMERIC,
    -- Doctor's professional practice
    award_level_19 NUMERIC,
    -- Doctor's other
    award_level_20 NUMERIC,
    -- Post-doctoral certificate
    award_level_21 NUMERIC,
    -- Other/unspecified
    PRIMARY KEY (unitid, YEAR),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- ============================================================
-- IPEDS ADMISSIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ipeds_admissions (
    unitid INTEGER,
    YEAR INTEGER,
    applicants INTEGER,
    admitted INTEGER,
    enrolled INTEGER,
    sat_math_25th INTEGER,
    sat_math_75th INTEGER,
    act_25th_percentile INTEGER,
    act_75th_percentile INTEGER,
    acceptance_rate NUMERIC(5, 2),
    yield_rate NUMERIC(5, 2),
    PRIMARY KEY (unitid, YEAR),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
-- Institution lookups
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_institutions_name'
    ) THEN
        CREATE INDEX idx_institutions_name ON ipeds_institutions(institution_name);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_institutions_state'
    ) THEN
        CREATE INDEX idx_institutions_state ON ipeds_institutions(state);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_institutions_carnegie'
    ) THEN
        CREATE INDEX idx_institutions_carnegie ON ipeds_institutions(carnegie_classification);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_institutions_system'
    ) THEN
        CREATE INDEX idx_institutions_system ON ipeds_institutions(system_name);
    END IF;
END $$;
-- Research-related queries
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_finance_research'
    ) THEN
        CREATE INDEX idx_finance_research ON ipeds_finance(unitid, research_total);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_staff_faculty'
    ) THEN
        CREATE INDEX idx_staff_faculty ON ipeds_staff(unitid, instructional_staff_total);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_enrollment_total'
    ) THEN
        CREATE INDEX idx_enrollment_total ON ipeds_enrollment(unitid, total_enrollment);
    END IF;
END $$;
-- Time-based queries
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_finance_year'
    ) THEN
        CREATE INDEX idx_finance_year ON ipeds_finance(YEAR);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_enrollment_year'
    ) THEN
        CREATE INDEX idx_enrollment_year ON ipeds_enrollment(YEAR);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_staff_year'
    ) THEN
        CREATE INDEX idx_staff_year ON ipeds_staff(YEAR);
    END IF;
END $$;
-- ============================================================
-- USEFUL VIEWS
-- ============================================================
-- Research intensity view
CREATE OR REPLACE VIEW v_research_intensity AS
SELECT i.unitid,
    i.institution_name,
    i.state,
    i.carnegie_classification,
    e.total_enrollment,
    s.instructional_staff_total,
    f.research_total,
    f.instruction_total,
    CASE
        WHEN e.total_enrollment > 0 THEN f.research_total::NUMERIC / e.total_enrollment
        ELSE 0
    END AS research_per_student,
    CASE
        WHEN s.instructional_staff_total > 0 THEN f.research_total::NUMERIC / s.instructional_staff_total
        ELSE 0
    END AS research_per_faculty,
    CASE
        WHEN f.instruction_total > 0 THEN f.research_total::NUMERIC / f.instruction_total
        ELSE 0
    END AS research_instruction_ratio,
    f.year
FROM ipeds_institutions i
    LEFT JOIN ipeds_enrollment e ON i.unitid = e.unitid
    LEFT JOIN ipeds_staff s ON i.unitid = s.unitid
    AND e.year = s.year
    LEFT JOIN ipeds_finance f ON i.unitid = f.unitid
    AND e.year = f.year
WHERE f.research_total > 0;
-- Faculty composition view
CREATE OR REPLACE VIEW v_faculty_composition AS
SELECT i.unitid,
    i.institution_name,
    s.instructional_staff_total,
    s.tenured_faculty,
    s.tenure_track_faculty,
    s.not_tenure_track_faculty,
    CASE
        WHEN s.instructional_staff_total > 0 THEN (
            s.tenured_faculty::NUMERIC / s.instructional_staff_total * 100
        )::NUMERIC(5, 2)
        ELSE 0
    END AS tenured_percentage,
    s.professors,
    s.associate_professors,
    s.assistant_professors,
    s.year
FROM ipeds_institutions i
    JOIN ipeds_staff s ON i.unitid = s.unitid;
-- Financial health view
CREATE OR REPLACE VIEW v_financial_health AS
SELECT i.unitid,
    i.institution_name,
    f.total_assets,
    f.total_liabilities,
    f.net_assets,
    f.endowment_assets_eoy,
    f.total_revenues,
    f.total_expenses,
    (f.total_revenues - f.total_expenses) AS net_income,
    CASE
        WHEN f.total_liabilities > 0 THEN f.total_assets::NUMERIC / f.total_liabilities
        ELSE NULL
    END AS debt_to_asset_ratio,
    f.year
FROM ipeds_institutions i
    JOIN ipeds_finance f ON i.unitid = f.unitid;
-- Institutional Characteristics
CREATE TABLE IF NOT EXISTS ipeds_institutional_characteristics (
    unitid INTEGER PRIMARY KEY,
    open_admission INTEGER,
    credit_life_experience INTEGER,
    credit_exam INTEGER,
    credit_military INTEGER,
    credit_online INTEGER,
    student_learning_outcomes INTEGER,
    learning_assessment INTEGER,
    calendar_system INTEGER,
    years_college_required INTEGER,
    undergrad_application_fee INTEGER,
    grad_application_fee INTEGER,
    room_offered INTEGER,
    board_offered INTEGER,
    room_capacity INTEGER,
    board_capacity INTEGER,
    room_charge INTEGER,
    board_charge INTEGER,
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Tuition and Fees
CREATE TABLE IF NOT EXISTS ipeds_tuition_fees (
    unitid INTEGER,
    year INTEGER,
    tuition_in_district INTEGER,
    tuition_in_state INTEGER,
    tuition_out_of_state INTEGER,
    fees_in_district INTEGER,
    fees_in_state INTEGER,
    fees_out_of_state INTEGER,
    per_credit_in_district INTEGER,
    per_credit_in_state INTEGER,
    per_credit_out_of_state INTEGER,
    grad_tuition_in_state INTEGER,
    grad_tuition_out_of_state INTEGER,
    grad_fees_in_state INTEGER,
    grad_fees_out_of_state INTEGER,
    PRIMARY KEY (unitid, year),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Graduation Rates
CREATE TABLE IF NOT EXISTS ipeds_graduation_rates (
    unitid INTEGER,
    year INTEGER,
    cohort_type INTEGER,
    cohort_size INTEGER,
    completers_total INTEGER,
    completers_men INTEGER,
    completers_women INTEGER,
    completers_nonresident INTEGER,
    completers_hispanic INTEGER,
    completers_american_indian INTEGER,
    completers_asian INTEGER,
    completers_black INTEGER,
    completers_hawaiian INTEGER,
    completers_white INTEGER,
    completers_two_or_more INTEGER,
    completers_unknown INTEGER,
    PRIMARY KEY (unitid, year, cohort_type),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Graduation by Income Level
CREATE TABLE IF NOT EXISTS ipeds_graduation_pell (
    unitid INTEGER,
    year INTEGER,
    cohort_type INTEGER,
    pell_cohort_size INTEGER,
    pell_completers_total INTEGER,
    pell_completers_men INTEGER,
    pell_completers_women INTEGER,
    loan_cohort_size INTEGER,
    loan_completers_total INTEGER,
    loan_completers_men INTEGER,
    loan_completers_women INTEGER,
    PRIMARY KEY (unitid, year, cohort_type),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Faculty Salaries
CREATE TABLE IF NOT EXISTS ipeds_faculty_salaries (
    unitid INTEGER,
    year INTEGER,
    academic_rank INTEGER,
    gender INTEGER,
    faculty_count INTEGER,
    average_salary INTEGER,
    PRIMARY KEY (unitid, year, academic_rank, gender),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Financial Aid
CREATE TABLE IF NOT EXISTS ipeds_financial_aid (
    unitid INTEGER,
    year INTEGER,
    undergrads_total INTEGER,
    fulltime_firsttime_total INTEGER,
    federal_grant_recipients INTEGER,
    federal_grant_percent NUMERIC(5, 2),
    pell_recipients INTEGER,
    pell_percent NUMERIC(5, 2),
    state_local_grant_recipients INTEGER,
    state_local_grant_percent NUMERIC(5, 2),
    institutional_grant_recipients INTEGER,
    institutional_grant_percent NUMERIC(5, 2),
    loan_recipients INTEGER,
    loan_percent NUMERIC(5, 2),
    grant_aid_recipients INTEGER,
    grant_aid_percent NUMERIC(5, 2),
    average_grant_amount INTEGER,
    any_aid_recipients INTEGER,
    any_aid_percent NUMERIC(5, 2),
    PRIMARY KEY (unitid, year),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Outcome Measures
CREATE TABLE IF NOT EXISTS ipeds_outcome_measures (
    unitid INTEGER,
    year INTEGER,
    outcome_cohort_size INTEGER,
    completed_8yr_percent NUMERIC(5, 2),
    completed_8yr_men INTEGER,
    completed_8yr_women INTEGER,
    enrolled_8yr_percent NUMERIC(5, 2),
    enrolled_8yr_men INTEGER,
    enrolled_8yr_women INTEGER,
    neither_8yr_percent NUMERIC(5, 2),
    PRIMARY KEY (unitid, year),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Academic Libraries
CREATE TABLE IF NOT EXISTS ipeds_academic_libraries (
    unitid INTEGER,
    year INTEGER,
    books_physical INTEGER,
    books_electronic INTEGER,
    serials_digital INTEGER,
    serials_print INTEGER,
    databases INTEGER,
    video_materials INTEGER,
    audio_materials INTEGER,
    total_expenses BIGINT,
    staff_expenses BIGINT,
    collection_expenses BIGINT,
    operations_expenses BIGINT,
    librarian_fte NUMERIC,
    service_hours_per_year INTEGER,
    PRIMARY KEY (unitid, year),
    FOREIGN KEY (unitid) REFERENCES ipeds_institutions(unitid)
);
-- Indexes
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tuition_year'
    ) THEN
        CREATE INDEX idx_tuition_year ON ipeds_tuition_fees(year);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_grad_rates_year'
    ) THEN
        CREATE INDEX idx_grad_rates_year ON ipeds_graduation_rates(year);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_salaries_rank'
    ) THEN
        CREATE INDEX idx_salaries_rank ON ipeds_faculty_salaries(academic_rank, average_salary DESC);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_fin_aid_pell'
    ) THEN
        CREATE INDEX idx_fin_aid_pell ON ipeds_financial_aid(pell_percent DESC);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_libraries_exp'
    ) THEN
        CREATE INDEX idx_libraries_exp ON ipeds_academic_libraries(total_expenses DESC);
    END IF;
END $$;
-- ============================================================
-- COMMENTS
-- ============================================================
COMMENT ON TABLE ipeds_institutions IS 'IPEDS institutional characteristics and directory information';
COMMENT ON TABLE ipeds_enrollment IS 'IPEDS fall enrollment data by demographics';
COMMENT ON TABLE ipeds_staff IS 'IPEDS instructional staff and faculty data';
COMMENT ON TABLE ipeds_finance IS 'IPEDS financial data (GASB reporting)';
COMMENT ON TABLE ipeds_completions IS 'IPEDS degrees and certificates awarded';
COMMENT ON TABLE ipeds_admissions IS 'IPEDS undergraduate admissions data';
COMMENT ON COLUMN ipeds_finance.research_total IS 'Total research expenditures';
COMMENT ON COLUMN ipeds_finance.endowment_assets_eoy IS 'Endowment value at end of fiscal year';
COMMENT ON COLUMN ipeds_staff.tenured_faculty IS 'Number of tenured faculty members';
COMMENT ON COLUMN ipeds_institutions.carnegie_classification IS 'Carnegie Classification (e.g., R1, R2)';
