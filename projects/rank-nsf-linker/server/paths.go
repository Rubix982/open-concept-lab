package main

import (
	"archive/zip"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"
	"path/filepath"
)

var (
	RootDir, _    = filepath.Abs(filepath.Join(filepath.Dir(os.Args[0]), ".."))
	DataDir       = getRootDirPath("")
	BackupDir     = getRootDirPath("backup")
	TargetDir     = getRootDirPath("target")
	NSFDataDir    = path.Join(getDataFilePath(""), "nsfdata")
	MigrationsDir = "migrations"

	CSRANKINGS_FILENAME   = "csrankings.csv"
	GEN_AUTHOR_FILENAME   = "generated-author-info.csv"
	COUNTRIES_FILENAME    = "countries.csv"
	COUNTRY_INFO_FILENAME = "country-info.csv"
	GEOLOCATION_FILENAME  = "geolocation.csv"

	CSRankingsFile  = getDataFilePath(CSRANKINGS_FILENAME)
	GenAuthorFile   = getDataFilePath(GEN_AUTHOR_FILENAME)
	CountriesFile   = getDataFilePath(COUNTRIES_FILENAME)
	CountryInfoFile = getDataFilePath(COUNTRY_INFO_FILENAME)
	GeolocationFile = getDataFilePath(GEOLOCATION_FILENAME)

	BackupCountryInfo = getDataFilePath(COUNTRY_INFO_FILENAME)
	BackupGeolocation = getDataFilePath(GEOLOCATION_FILENAME)

	CSRANKINGS_RAW_GITHUB = "https://raw.githubusercontent.com/emeryberger/CSrankings/master/"
	NSFURLPrefix          = "https://www.nsf.gov/awardsearch/download?All=true&isJson=true&DownloadFileName="

	NSFAwardsStartYear = 2010
	NSFAwardsEndYear   = 2025
)

var CSVURLs = map[string]string{
	CSRankingsFile:  CSRANKINGS_RAW_GITHUB + CSRANKINGS_FILENAME,
	GenAuthorFile:   CSRANKINGS_RAW_GITHUB + GEN_AUTHOR_FILENAME,
	CountriesFile:   CSRANKINGS_RAW_GITHUB + COUNTRIES_FILENAME,
	CountryInfoFile: CSRANKINGS_RAW_GITHUB + COUNTRY_INFO_FILENAME,
	GeolocationFile: CSRANKINGS_RAW_GITHUB + GEOLOCATION_FILENAME,
}

func getRootDirPath(rootSubDir string) string {
	if appEnv := os.Getenv("APP_ENV"); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", rootSubDir)
	}

	// Get current working directory (should be `nsf-rank-linker/server`)
	wd, err := os.Getwd()
	if err != nil {
		logger.Errorf("failed to get working directory: %v", err)
		return filepath.Join("..", rootSubDir) // fallback
	}

	return filepath.Join(filepath.Dir(wd), rootSubDir)
}

func getDataFilePath(fileName string) string {
	if appEnv := os.Getenv("APP_ENV"); len(appEnv) > 0 {
		return "/app/data"
	}

	// Get current working directory (should be `nsf-rank-linker/server`)
	wd, err := os.Getwd()
	if err != nil {
		logger.Errorf("failed to get working directory: %v", err)
		return filepath.Join("..", "data", fileName) // fallback
	}

	// Go up to root (../)
	rootDir := filepath.Dir(wd)

	// Join path to data file
	return filepath.Join(rootDir, "data", fileName)
}

func getMigrationsFilePath() string {
	if appEnv := os.Getenv("APP_ENV"); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", MigrationsDir)
	}

	return MigrationsDir
}

func downloadCSVs(force bool) error {
	// Ensure all the directories exist
	for _, dir := range []string{DataDir, BackupDir, TargetDir, NSFDataDir} {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			return fmt.Errorf("failed to create directory %s: %v", dir, err)
		}
	}

	for localPath, url := range CSVURLs {
		fileName := filepath.Base(localPath)
		if _, err := os.Stat(localPath); err == nil && !force {
			logger.Infof("[✓] %s already exists. Skipping download.\n", fileName)
			continue
		}

		logger.Infof("[*] Downloading %s ...\n", fileName)
		resp, err := http.Get(url)
		if err != nil || resp.StatusCode != 200 {
			logger.Infof("[!] Failed to download %s. Status: %d\n", fileName, resp.StatusCode)
			continue
		}
		defer resp.Body.Close()

		out, err := os.Create(localPath)
		if err != nil {
			logger.Infof("[!] Error creating file %s: %v\n", localPath, err)
			continue
		}
		defer out.Close()

		_, err = io.Copy(out, resp.Body)
		if err != nil {
			logger.Infof("[!] Error writing file %s: %v\n", localPath, err)
			continue
		}

		logger.Infof("[✓] %s downloaded.\n", fileName)
	}

	return nil
}

// DownloadNSFData fetches and extracts NSF award data per year.
func downloadNSFData(force bool) error {
	for year := NSFAwardsStartYear; year <= NSFAwardsEndYear; year++ {
		zipFile := filepath.Join(NSFDataDir, fmt.Sprintf("nsf_awards_%d.zip", year))
		extractDir := filepath.Join(NSFDataDir, fmt.Sprintf("%d", year))

		if _, err := os.Stat(extractDir); err == nil && !force {
			logger.Infof("[✓] %s already exists. Skipping download.", filepath.Base(extractDir))
			continue
		}

		logger.Infof("[*] Downloading %s ...", filepath.Base(zipFile))

		resp, err := http.Get(fmt.Sprintf("%s%d", NSFURLPrefix, year))
		if err != nil {
			logger.Errorf("[!] Failed to fetch %s: %v", filepath.Base(zipFile), err)
			continue
		}

		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			logger.Errorf("[!] Failed to download %s. Status: %d, Body: %s", filepath.Base(zipFile), resp.StatusCode, string(body))
			continue
		}

		outFile, err := os.Create(zipFile)
		if err != nil {
			logger.Errorf("[!] Cannot create file %s: %v", zipFile, err)
			continue
		}

		defer outFile.Close()

		if _, err = io.Copy(outFile, resp.Body); err != nil {
			logger.Errorf("[!] Error writing file %s: %v", zipFile, err)
			continue
		}

		logger.Infof("[✓] %s downloaded.", filepath.Base(zipFile))

		if _, err = os.Stat(extractDir); err == nil && !force {
			logger.Infof("[✓] Already extracted to %s", extractDir)
			continue
		}

		logger.Infof("[*] Extracting %s to %s ...", filepath.Base(zipFile), extractDir)

		if err = os.MkdirAll(extractDir, os.ModePerm); err != nil {
			logger.Errorf("[!] Could not create directory %s: %v", extractDir, err)
			continue
		}

		if err = unzip(zipFile, extractDir); err != nil {
			logger.Errorf("[!] Failed to extract %s: %v", filepath.Base(zipFile), err)
			continue
		}

		logger.Infof("[✓] Extracted to %s", extractDir)

		if err = os.Remove(zipFile); err != nil {
			logger.Errorf("[!] Could not delete %s after extraction: %v", zipFile, err)
			continue
		}

		logger.Infof("[🧹] Cleaned up %s after extraction", filepath.Base(zipFile))
	}

	return nil
}

// unzip extracts a .zip archive to a destination directory
func unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return fmt.Errorf("invalid zip: %w", err)
	}
	defer r.Close()

	for _, f := range r.File {
		target := filepath.Join(dest, f.Name)

		if f.FileInfo().IsDir() {
			os.MkdirAll(target, os.ModePerm)
			continue
		}

		if err := os.MkdirAll(filepath.Dir(target), os.ModePerm); err != nil {
			return err
		}

		dstFile, err := os.OpenFile(target, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}

		srcFile, err := f.Open()
		if err != nil {
			dstFile.Close()
			return err
		}

		_, err = io.Copy(dstFile, srcFile)
		dstFile.Close()
		srcFile.Close()
		if err != nil {
			return err
		}
	}
	return nil
}
