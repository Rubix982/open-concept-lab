CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS countries (
  name TEXT,
  alpha_2 TEXT,
  alpha_3 TEXT,
  country_code INTEGER,
  iso_3166_2 TEXT,
  region TEXT,
  sub_region TEXT,
  intermediate_region TEXT,
  region_code INTEGER,
  sub_region_code INTEGER,
  intermediate_region_code INTEGER
);

CREATE TABLE IF NOT EXISTS universities (
  institution TEXT PRIMARY KEY,
  street_address TEXT,
  city TEXT,
  phone TEXT,
  zip_code TEXT,
  country TEXT,
  region TEXT,
  countryabbrv TEXT,
  homepage TEXT,
  latitude REAL,
  longitude REAL
);

CREATE TABLE IF NOT EXISTS professors (
  name TEXT PRIMARY KEY,
  affiliation TEXT,
  homepage TEXT,
  scholar_id TEXT,
  nsf_id TEXT
);

CREATE TABLE IF NOT EXISTS generated_author_info (
  name TEXT,
  dept TEXT,
  area TEXT,
  count REAL,
  adjustedcount REAL,
  year INTEGER
);

CREATE TABLE IF NOT EXISTS directorate_division (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  directorate_abbr TEXT NOT NULL,
  directorate_name TEXT,
  division_abbr TEXT NOT NULL,
  division_name TEXT,
  CONSTRAINT unique_directorate_division UNIQUE (directorate_abbr, division_abbr)
);

CREATE TABLE IF NOT EXISTS program_officer (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  CONSTRAINT unique_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS award (
  id TEXT PRIMARY KEY,
  year INTEGER,
  award_agency_id TEXT,
  transaction_type TEXT,
  award_instrument_text TEXT,
  award_title_text TEXT,
  cfda_number TEXT,
  org_code TEXT,
  program_officer_id UUID REFERENCES program_officer (id) ON DELETE SET NULL,
  award_effective_date TEXT,
  award_expiry_date TEXT,
  total_international_award_amount INTEGER,
  award_amount INTEGER,
  earliest_amendment_date TEXT,
  most_recent_amendment_date TEXT,
  abstract TEXT,
  arra_award REAL,
  directorate_division_id UUID REFERENCES directorate_division (id) ON DELETE SET NULL,
  award_agency_code TEXT,
  fund_agency_code TEXT,
  institution TEXT REFERENCES universities (institution) ON DELETE SET NULL,
  performing_institution TEXT REFERENCES universities (institution) ON DELETE SET NULL,
  html_content TEXT,
  raw_content TEXT
);

CREATE TABLE IF NOT EXISTS program_element (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  name TEXT,
  CONSTRAINT program_element_unique_code UNIQUE (award_id, code)
);

CREATE TABLE IF NOT EXISTS program_reference (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  name TEXT,
  CONSTRAINT program_reference_unique_code UNIQUE (award_id, code)
);

CREATE TABLE IF NOT EXISTS application_funding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  name TEXT,
  symbol_id TEXT,
  funding_code TEXT,
  funding_name TEXT,
  funding_symbol_id TEXT,
  CONSTRAINT application_funding_unique_code UNIQUE (award_id, code)
);

CREATE TABLE IF NOT EXISTS fiscal_year_funding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  fiscal_year INTEGER,
  funding_amount REAL,
  CONSTRAINT fiscal_year_funding_unique_fiscal_year UNIQUE (award_id, fiscal_year)
);

CREATE TABLE IF NOT EXISTS award_pi_rel (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  investigator_id TEXT REFERENCES professors (name) ON DELETE SET NULL,
  pi_role TEXT,
  pi_start_date TEXT,
  pi_end_date TEXT,
  CONSTRAINT award_pi_rel_unique_award_id_investigator_id UNIQUE (award_id, investigator_id)
);