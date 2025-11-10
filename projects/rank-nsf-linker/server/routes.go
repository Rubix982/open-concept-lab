package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func helloWorld(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message":"Hello, world!"}`))
}

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
	}
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
		return nil, fmt.Errorf("failed to decode request body: %w", err)
	}
	country := reqBody.Country
	if country == "" {
		return nil, fmt.Errorf("country parameter is required")
	}

	// Now, we can query the database for the university with this country

	query := `
		SELECT
			u.institution,
			u.longitude,
			u.latitude,
			u.city,
			u.region
		FROM universities u
		WHERE u.country = $1
		;
	`
	var institution, longitude, latitude, city, region string
	err = db.QueryRow(query, country).Scan(&institution, &longitude, &latitude, &city, &region)
	if err != nil {
		return nil, err
	}
	mapResult := make(map[string]interface{})
	mapResult["institution"] = institution
	mapResult["longitude"] = longitude
	mapResult["latitude"] = latitude
	mapResult["city"] = city
	mapResult["region"] = region
	mapResult["country"] = country
	results := []interface{}{}
	results = append(results, mapResult)

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
