package main

import (
	"regexp"
	"strings"
)

// normalizeInstitutionName standardizes university names for better matching.
func normalizeInstitutionName(name string) string {
	name = strings.TrimSpace(name)

	// Replace connectors/punctuation with spaces but keep words intact
	re := regexp.MustCompile(`[.,;:/()'\-]+`)
	name = re.ReplaceAllString(name, " ")

	// Normalize "&" to "and" only if surrounded by spaces
	re = regexp.MustCompile(`\s*&\s*`)
	name = re.ReplaceAllString(name, " and ")

	// Collapse multiple spaces
	re = regexp.MustCompile(`\s+`)
	name = re.ReplaceAllString(name, " ")

	// Trim whitespace
	name = strings.TrimSpace(name)

	// If the name starts with "Univ of ", replace it with "University Of "
	if strings.HasPrefix(strings.ToLower(name), "univ of ") {
		name = "University Of " + strings.TrimSpace(name[8:])
	} else if strings.HasPrefix(strings.ToLower(name), "univ. of ") {
		name = "University Of " + strings.TrimSpace(name[9:])
	} else if strings.HasPrefix(strings.ToLower(name), "univ ") {
		name = "University " + strings.TrimSpace(name[5:])
	} else if strings.HasPrefix(strings.ToLower(name), "univ. ") {
		name = "University " + strings.TrimSpace(name[6:])
	}

	return name
}
