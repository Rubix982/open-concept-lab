package main

import (
	"fmt"

	colly "github.com/gocolly/colly/v2"
)

// Institution types stored in universities.institution_type.
// NSF awards bring in every awardee (companies, museums, societies), not only
// universities, so the map and the APIs filter on this column.
const (
	InstitutionTypeUniversity          = "university"
	InstitutionTypeUniversityAffiliate = "university_affiliate" // a university's grant-receiving arm: regents, research foundations
	InstitutionTypeBusiness            = "business"
	InstitutionTypeOrganization        = "organization" // museums, societies, hospitals, government labs
)

// Rules are evaluated top to bottom; the first match wins.
//  1. Anything CSRankings lists faculty for is a university.
//  2. University consortia are organizations; regents / trustees / foundations
//     of a single university are affiliates.
//  3. Recipients of SBIR/STTR (small-business programs) are businesses.
//  4. Names ending in a legal-entity suffix are businesses.
//  5. Names that read as an academic institution are universities.
//  6. Everything else is an organization.
const classifyInstitutionsSQL = `
UPDATE universities u SET institution_type = CASE
  WHEN u.institution IN (SELECT affiliation FROM professor_areas)
    THEN '` + InstitutionTypeUniversity + `'
  WHEN u.institution ~* '(associated universities|association of universities|universities research association|universities space research)'
    THEN '` + InstitutionTypeOrganization + `'
  WHEN u.institution ~* '(foundation|research corporation|research institute|regents of|board of regents|trustees of|board of trustees|sponsored programs|research council|experiment station|agrilife|auxiliary|center for research)'
   AND u.institution ~* '(universit|college|institute of technology|\mtech\M|\msuny\M|\mcuny\M|a&m|cal poly)'
    THEN '` + InstitutionTypeUniversityAffiliate + `'
  WHEN EXISTS (
    SELECT 1 FROM award a JOIN program_element pe ON pe.award_id = a.id
    WHERE a.institution = u.institution AND pe.name ~* '^(SBIR|STTR)')
    THEN '` + InstitutionTypeBusiness + `'
  WHEN u.institution ~* '\m(inc|incorporated|llc|l l c|corp|corporation|co|company|ltd|limited|pbc|plc|gmbh|lp|llp)\M\.?\s*$'
   AND u.institution !~* '(universit|college)'
    THEN '` + InstitutionTypeBusiness + `'
  WHEN u.institution ~* '(universit|college|institute|instituto|\minstitut\M|polytechn|school of|ecole|école|hochschule|technion|\meth\M|epfl|kaist|\miit\M|\msuny\M|\mcuny\M)'
    THEN '` + InstitutionTypeUniversity + `'
  ELSE '` + InstitutionTypeOrganization + `'
END;
`

func classifyInstitutions(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	if _, err := db.Exec(classifyInstitutionsSQL); err != nil {
		return fmt.Errorf("failed to classify institutions: %w", err)
	}

	rows, err := db.Query(`SELECT institution_type, COUNT(*) FROM universities GROUP BY 1 ORDER BY 2 DESC`)
	if err != nil {
		return fmt.Errorf("failed to count institution types: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var kind string
		var count int
		if err := rows.Scan(&kind, &count); err != nil {
			return err
		}
		logger.Infof(mainCtx, "🏷️  %s: %d", kind, count)
	}
	return rows.Err()
}
