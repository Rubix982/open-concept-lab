package main

import (
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv"
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

func main() {
	printBanner()

	if err := godotenv.Load(); err != nil {
		logger.Warnf("⚠️  No .env file found, continuing with system environment variables: %v", err)
	}

	if skipMigrations := os.Getenv(POPULATE_DB_FLAG); len(skipMigrations) == 0 {
		populatePostgres()
	}

	log.Println("Server running on 8080")
	http.ListenAndServe(":8080", GetRouter())
}
