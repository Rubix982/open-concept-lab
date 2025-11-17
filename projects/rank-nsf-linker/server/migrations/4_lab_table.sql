CREATE TABLE IF NOT EXISTS labs (
	institution text NULL, -- Foreign key to refer to universities.institution -- should be ideally populated, but can be NULL for now
	lab text NOT NULL,
	street_address text NULL,
	city text NULL,
	phone text NULL,
	zip_code text NULL,
	country text NULL,
	region text NULL,
	countryabbrv text NULL,
	homepage text NULL,
	latitude float4 NULL,
	longitude float4 NULL,
	CONSTRAINT labs_pkey PRIMARY KEY (lab)
);

CREATE INDEX IF NOT EXISTS labs_lab_trgm_idx ON labs USING gin (lab gin_trgm_ops);
CREATE INDEX IF NOT EXISTS labs_institution_trgm_idx ON labs USING gin (institution gin_trgm_ops);
CREATE INDEX IF NOT EXISTS labs_latitude_idx ON labs (latitude);
CREATE INDEX IF NOT EXISTS labs_longitude_idx ON labs (longitude);
