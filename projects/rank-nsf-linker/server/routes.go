package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func fetchAllUniversitiesWithCoordinates() ([]byte, error) {
	db, err := GetDB()
	if err != nil {
		return nil, fmt.Errorf("cannot get DB: %w", err)
	}

	query := `
	    SELECT institution, longitude, latitude, city, region, country
		FROM universities;
	`
	var result []byte
	err = db.QueryRow(query).Scan(&result)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func fetchUniversitySummary(r *http.Request) ([]byte, error) {
	db, err := GetDB()
	if err != nil {
		return nil, fmt.Errorf("cannot get DB: %w", err)
	}

	// Extract the "country" name from the JSON request body
	var reqBody struct {
		Country string `json:"country"`
		Limit   int    `json:"limit"`
		Offset  int    `json:"offset"`
	}
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
		return nil, fmt.Errorf("failed to decode request body: %w", err)
	}
	country := reqBody.Country
	limit := reqBody.Limit
	offset := reqBody.Offset
	if country == "" {
		return nil, fmt.Errorf("country parameter is required")
	}

	// Now, we can query the database for the university with this country
	query := `SELECT * FROM university_summary_view usv WHERE usv.country = $1 LIMIT $2 OFFSET $3;`
	rows, err := db.Query(query, country, limit, offset)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}

	var results []map[string]any
	for rows.Next() {
		// Create a slice of interface to hold the column values
		values := make([]any, len(columns))
		valuePtrs := make([]any, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}

		mapResult := make(map[string]any)
		for i, col := range columns {
			val := values[i]
			b, ok := val.([]byte)
			if !ok {
				mapResult[col] = val
				continue
			}

			var jsonVal any
			if err := json.Unmarshal(b, &jsonVal); err == nil {
				mapResult[col] = jsonVal
				continue
			}

			mapResult[col] = string(b)
		}
		results = append(results, mapResult)
	}

	// Now, we need to get the stats object for this university
	jsonData, err := json.Marshal(results)
	if err != nil {
		return nil, err
	}
	return jsonData, nil
}

func getAllUniversitiesWithCoordinates(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	universities, err := fetchAllUniversitiesWithCoordinates()
	if err != nil {
		logger.Errorf("Failed to fetch universities: %v", err)
		http.Error(w, "Failed to fetch universities", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(universities)
}

func getUniversitySummary(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	summary, err := fetchUniversitySummary(r)
	if err != nil {
		logger.Errorf("Failed to fetch university summary: %v", err)
		http.Error(w, "Failed to fetch university summary", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(summary)
}
