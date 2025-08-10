CREATE TABLE
    IF NOT EXISTS award (
        award_id TEXT PRIMARY KEY,
        agency_id TEXT,
        transaction_type TEXT,
        award_instrument TEXT,
        title TEXT,
        abstract TEXT,
        cfda_number TEXT,
        org_code TEXT,
        po_phone TEXT,
        po_email TEXT,
        po_signing_officer TEXT,
        start_date DATE,
        end_date DATE,
        total_intended_amount REAL,
        actual_award_amount REAL,
        min_amendment_date DATE,
        max_amendment_date DATE,
        arra_amount REAL,
        directorate_abbr TEXT,
        directorate_name TEXT,
        division_abbr TEXT,
        division_name TEXT,
        awarding_agency_code TEXT,
        funding_agency_code TEXT
    );

CREATE TABLE
    IF NOT EXISTS principal_investigator (
        award_id TEXT REFERENCES award (award_id),
        nsf_id TEXT,
        full_name TEXT,
        first_name TEXT,
        last_name TEXT,
        middle_initial TEXT,
        suffix TEXT,
        email TEXT,
        role TEXT,
        start_date DATE,
        end_date DATE
    );

CREATE TABLE
    IF NOT EXISTS institution (
        institution_id TEXT PRIMARY KEY,
        name TEXT,
        address_line_1 TEXT,
        address_line_2 TEXT,
        city TEXT,
        state_code TEXT,
        state_name TEXT,
        zip_code TEXT,
        country TEXT,
        phone_number TEXT,
        legal_business_name TEXT,
        congressional_district TEXT,
        state_congressional_district TEXT,
        parent_uei TEXT,
        uei TEXT
    );

CREATE TABLE
    IF NOT EXISTS performing_institution (
        award_id TEXT REFERENCES award (award_id),
        name TEXT,
        city TEXT,
        state_code TEXT,
        state_name TEXT,
        zip_code TEXT,
        country_code TEXT,
        country_name TEXT,
        congressional_district TEXT,
        state_congressional_district TEXT,
        country_flag TEXT
    );

CREATE TABLE
    IF NOT EXISTS program_element (
        award_id TEXT REFERENCES award (award_id),
        program_element_code TEXT,
        program_element_name TEXT
    );

CREATE TABLE
    IF NOT EXISTS application_funding (
        award_id TEXT REFERENCES award (award_id),
        application_code TEXT,
        application_name TEXT,
        application_symbol_id TEXT,
        funding_code TEXT,
        funding_name TEXT,
        funding_symbol_id TEXT
    );

CREATE TABLE
    IF NOT EXISTS funding_obligation (
        award_id TEXT REFERENCES award (award_id),
        fiscal_year INTEGER,
        amount_obligated REAL
    );

CREATE TABLE
    IF NOT EXISTS project_outcomes (
        award_id TEXT REFERENCES award (award_id),
        html_content TEXT,
        raw_text TEXT
    );

CREATE TABLE
    IF NOT EXISTS research_area (
        area_id TEXT PRIMARY KEY,
        name TEXT,
        keywords TEXT,
        csrankings_flag BOOLEAN,
        nsf_flag BOOLEAN
    );

CREATE TABLE
    IF NOT EXISTS investigator (
        name TEXT,
        email TEXT,
        is_professor BOOLEAN
    );

CREATE TABLE
    IF NOT EXISTS award_author_link (
        award_id TEXT REFERENCES award (award_id),
        contributor_name TEXT,
        role TEXT
    );
