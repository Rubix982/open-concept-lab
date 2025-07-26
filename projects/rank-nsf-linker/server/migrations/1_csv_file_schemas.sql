CREATE TABLE
    IF NOT EXISTS countries (
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

CREATE TABLE
    IF NOT EXISTS country_info (institution TEXT, region TEXT, countryabbrv TEXT);

CREATE TABLE
    IF NOT EXISTS csrankings (
        name TEXT,
        affiliation TEXT,
        homepage TEXT,
        scholarid TEXT
    );

CREATE TABLE
    IF NOT EXISTS generated_author_info (
        name TEXT,
        dept TEXT,
        area TEXT,
        count DOUBLE,
        adjustedcount DOUBLE,
        year INTEGER
    );

CREATE TABLE
    IF NOT EXISTS geolocation (
        institution TEXT,
        latitude DOUBLE,
        longitude DOUBLE
    );