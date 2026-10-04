package main

import "testing"

func TestScholarshipNameKey(t *testing.T) {
	same := [][2]string{
		{"DAAD Development-Related Postgraduate Courses (EPOS)", "Development-Related Postgraduate Courses (EPOS)"},
		{"DAAD Helmut-Schmidt-Programme (Public Policy and Good Governance)", "Helmut-Schmidt-Programme"},
		{"DAAD Doctoral Programmes in Germany", "Research Grants - Doctoral Programmes in Germany"},
	}
	for _, p := range same {
		if scholarshipNameKey(p[0]) != scholarshipNameKey(p[1]) {
			t.Errorf("%q and %q should match", p[0], p[1])
		}
	}
	different := [][2]string{
		{"DAAD Research Grants (short-term, in Germany)", "Research Grants in Germany"},
		{"DAAD Doctoral Programmes in Germany", "Research Grants - Bi-nationally Supervised Doctoral Degrees/Cotutelle"},
	}
	for _, p := range different {
		if scholarshipNameKey(p[0]) == scholarshipNameKey(p[1]) {
			t.Errorf("%q and %q should not match", p[0], p[1])
		}
	}
}
