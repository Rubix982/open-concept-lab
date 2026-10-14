-- The institution a grant is held at, for funders that name no researcher (DFG via OpenAlex: the
-- awarded institution only). For the others it stays empty: their people rows carry the institution.
ALTER TABLE funder_grants ADD COLUMN IF NOT EXISTS institution text;
