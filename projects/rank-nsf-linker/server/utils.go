package main

import (
	"regexp"
	"strings"
)

// normalizeInstitutionName standardizes university names for better matching.
func normalizeInstitutionName(name string) string {
	name = strings.TrimSpace(name)

	// Replace connectors/punctuation with spaces but keep words intact
	re := regexp.MustCompile(`[.,;:/()']+`)
	name = re.ReplaceAllString(name, " ")

	// Add spaces around hyphens between words (e.g., "A-B" -> "A - B")
	re = regexp.MustCompile(`(\w)-(\w)`)
	name = re.ReplaceAllString(name, "$1 - $2")

	// Collapse multiple spaces
	re = regexp.MustCompile(`\s+`)
	name = re.ReplaceAllString(name, " ")

	// Trim whitespace
	name = strings.TrimSpace(name)

	// If the name starts with "Univ of ", replace it with "University Of "
	if strings.HasPrefix(strings.ToLower(name), "univ of ") {
		name = "University Of " + strings.TrimSpace(name[8:])
	}
	if strings.HasPrefix(strings.ToLower(name), "univ. of ") {
		name = "University Of " + strings.TrimSpace(name[9:])
	}
	if strings.HasPrefix(strings.ToLower(name), "univ ") {
		name = "University " + strings.TrimSpace(name[5:])
	}
	if strings.HasPrefix(strings.ToLower(name), "univ. ") {
		name = "University " + strings.TrimSpace(name[6:])
	}
	if strings.HasPrefix(strings.ToLower(name), "texas a and m") {
		// Special case for Texas A&M (case-insensitive)
		// Preserve any trailing text after "Texas A And M"
		name = "Texas A&M"
		if len(name) > len("Texas A And M") {
			suffix := strings.TrimSpace(name[len("Texas A And M"):])
			if suffix != "" {
				name += " " + suffix
			}
		}
	}

	return name
}
