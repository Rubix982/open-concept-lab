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

	return strings.TrimSpace(name)
}
