package main

import "net/http"

func helloWorld(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message":"Hello, world!"}`))
}

func fetchAllUniversitiesWithCoordinates() ([]byte, error) {
	db, err := getPostgresConnection()
	if err != nil {
		return nil, err
	}

	query := `
	SELECT json_agg(row_to_json(t))
	FROM (
		SELECT institution, city, country, latitude, longitude
		FROM universities
		WHERE latitude IS NOT NULL AND longitude IS NOT NULL
	) t;
	`
	var result []byte
	err = db.QueryRow(query).Scan(&result)
	if err != nil {
		return nil, err
	}
	return result, nil
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
