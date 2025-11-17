package main

import (
	"testing"
)

func TestNormalizeInstitutionName(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		// Basic punctuation and whitespace normalization
		{"  Univ of California, Los Angeles  ", "University Of California Los Angeles"},
		{"Univ. of Michigan", "University Of Michigan"},
		{"Univ Texas", "University Texas"},
		{"Univ. Texas", "University Texas"},
		{"Stanford University", "Stanford University"},
		{"Harvard & MIT", "Harvard and MIT"},
		{"Georgia Inst. of Tech.", "Georgia Inst of Tech"},
		{"California Institute of Technology", "California Institute of Technology"},
		{"Texas A and M University", "Texas A&M University"},
		{"texas a and m", "Texas A&M"},
		{"Texas A And M College Station", "Texas A&M College Station"},
		{"Univ of   Illinois", "University Of Illinois"},
		{"Univ. of   Illinois", "University Of Illinois"},
		{"Univ of California; Berkeley", "University Of California Berkeley"},
		{"Univ. of California: Berkeley", "University Of California Berkeley"},
		{"Univ of California (Berkeley)", "University Of California Berkeley"},
		{"Univ. of California/Berkeley", "University Of California Berkeley"},
		{"Univ of California-Los Angeles", "University Of California Los Angeles"},
		{"Univ. of California-Los Angeles", "University Of California Los Angeles"},
		{"Univ of California & Los Angeles", "University Of California and Los Angeles"},
		{"Univ. of California & Los Angeles", "University Of California and Los Angeles"},
		{"Univ of California, Los Angeles", "University Of California Los Angeles"},
		{"Univ. of California, Los Angeles", "University Of California Los Angeles"},
		{"Univ of California Los Angeles", "University Of California Los Angeles"},
		{"Univ. of California Los Angeles", "University Of California Los Angeles"},
		{"Univ of California Los Angeles ", "University Of California Los Angeles"},
		{"Univ. of California Los Angeles ", "University Of California Los Angeles"},
		{"Univ of California Los Angeles", "University Of California Los Angeles"},
		{"Univ. of California Los Angeles", "University Of California Los Angeles"},
		{"Univ of California Los Angeles", "University Of California Los Angeles"},
		{"Univ. of California Los Angeles", "University Of California Los Angeles"},
		// Edge cases
		{"", ""},
		{"   ", ""},
		{"&", "and"},
		{"Univ", "University"},
		{"Univ.", "University"},
	}

	for _, tt := range tests {
		got := normalizeInstitutionName(tt.input)
		if got != tt.expected {
			t.Errorf("normalizeInstitutionName(%q) = %q; want %q", tt.input, got, tt.expected)
		}
	}
}

func TestNormalizeInstitutionName2(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		// Basic punctuation and whitespace normalization
		{"University Of California, Davis", "University Of California Davis"},
	}

	for _, tt := range tests {
		got := normalizeInstitutionName(tt.input)
		if got != tt.expected {
			t.Errorf("normalizeInstitutionName(%q) = %q; want %q", tt.input, got, tt.expected)
		}
	}
}
