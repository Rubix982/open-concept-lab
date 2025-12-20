package main

import "time"

type ScrapedContent struct {
	ProfessorName string    `json:"professor_name"`
	URL           string    `json:"url"`
	ContentType   string    `json:"content_type"`
	Title         string    `json:"title"`
	Content       string    `json:"content"`
	ScrapedAt     time.Time `json:"scraped_at"`
}

type Embedding struct {
	Vector []float32 `json:"vector"`
}

type ProfessorProfile struct {
	Name        string
	Homepage    string
	Affiliation string
}
