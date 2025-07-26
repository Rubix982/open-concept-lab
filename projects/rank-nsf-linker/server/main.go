package main

import (
	"log"
	"net/http"

	"github.com/go-chi/chi"
)

func printBanner() {
	banner := `

██████╗  █████╗ ███╗   ██╗██╗  ██╗    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ 
██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝    ██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗
██████╔╝███████║██╔██╗ ██║█████╔╝     ██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══██║██║╚██╗██║██╔═██╗     ██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║██║  ██║██║ ╚████║██║  ██╗    ███████╗██║██║ ╚████║██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                   
`
	logger.Infof("%s", banner)
}

func helloWorld(w http.ResponseWriter, r *http.Request) {
	logger.Infof("Hello, world!")
}

func main() {
	printBanner()

	if downloadCsvErr := downloadCSVs(false); downloadCsvErr != nil {
		logger.Errorf("failed to download csvs: %v", downloadCsvErr)
		return
	}

	if downloadNsfDataErr := downloadNSFData(false); downloadNsfDataErr != nil {
		logger.Errorf("failed to download NSF data: %v", downloadNsfDataErr)
		return
	}

	if runMigrationsErr := runMigrations(); runMigrationsErr != nil {
		logger.Errorf("failed to execute migrations: %v", runMigrationsErr)
		return
	}

	if initDuckDbErr := populatePostgresFromCSVs(); initDuckDbErr != nil {
		logger.Errorf("failed to initialise duck db: %v", initDuckDbErr)
		return
	}

	r := chi.NewRouter()
	r.Get("/api/hello", helloWorld)
	log.Println("Server running on http://localhost:8193")
	http.ListenAndServe(":8193", r)
}
