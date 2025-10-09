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
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  directorate_abbr TEXT,
  directorate_name TEXT,
  division_abbr TEXT,
  division_name TEXT
);

CREATE TABLE IF NOT EXISTS program_officer (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  name TEXT,
  phone TEXT,
  email TEXT
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
  performing_institution TEXT REFERENCES universities (institution) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS program_element (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  code TEXT,
  name TEXT
);

CREATE TABLE IF NOT EXISTS program_reference (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  code TEXT,
  name TEXT
);

CREATE TABLE IF NOT EXISTS app_funding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  app_funding_code TEXT,
  app_funding_name TEXT,
  app_funding_symbol_id TEXT,
  fund_code TEXT,
  fund_name TEXT,
  fund_symbol_id TEXT
);

CREATE TABLE IF NOT EXISTS fiscal_year_funding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  fiscal_year INTEGER,
  funding_amount REAL
);

CREATE TABLE IF NOT EXISTS award_pi_rel (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
  award_id TEXT REFERENCES award (id) ON DELETE CASCADE,
  program_officer_id UUID REFERENCES program_officer (id),
  pi_role TEXT,
  pi_start_date TEXT,
  pi_end_date TEXT
);