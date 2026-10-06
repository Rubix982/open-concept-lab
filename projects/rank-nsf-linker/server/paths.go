package main

import (
	"archive/zip"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"time"

	colly "github.com/gocolly/colly/v2"
)

func getRootDirPath(rootSubDir string) string {
	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", rootSubDir)
	}

	// Get current working directory (should be `nsf-rank-linker/server`)
	wd, err := os.Getwd()
	if err != nil {
		logger.Errorf(colly.NewContext(), "failed to get working directory: %v", err)
		return filepath.Join("..", rootSubDir) // fallback
	}

	return filepath.Join(filepath.Dir(wd), rootSubDir)
}

func getMigrationsFilePath() string {

	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", MIGRATIONS_DIR)
	}

	return MIGRATIONS_DIR
}

func getScrapedDataFilePath() string {
	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/data/%v", SCRAPE_CACHE_DIR)
	}

	return SCRAPE_CACHE_DIR
}

func downloadCSVs(mainCtx *colly.Context) error {

	dataDir := getRootDirPath(DATA_DIR)
	nsfDataDir := path.Join(dataDir, NSF_DATA_DIR)
	targetDir := getRootDirPath(TARGET_DIR)
	backupDir := getRootDirPath(BACKUP_DIR)

	// Ensure all the directories exist
	for _, dir := range []string{dataDir, backupDir, targetDir, nsfDataDir} {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			return fmt.Errorf("failed to create directory %s: %v", dir, err)
		}
	}

	// Refresh every file on each run; a failed download keeps the copy already on disk.
	for _, fileName := range CSVURLs {
		if err := downloadFile(CSRANKINGS_RAW_GITHUB+fileName, path.Join(dataDir, fileName)); err != nil {
			logger.Warnf(mainCtx, "[!] %s not refreshed (keeping the local copy): %v", fileName, err)
			continue
		}
		logger.Infof(mainCtx, "[✓] %s downloaded", fileName)
	}

	// CSRankings replaced country-info.csv with institutions.csv (institution, region, countryabbrv,
	// homepage). The pipeline reads country-info.csv, so write its three columns there.
	institutions := path.Join(dataDir, CSRANKINGS_INSTITUTIONS_FILENAME)
	if err := downloadFile(CSRANKINGS_RAW_GITHUB+CSRANKINGS_INSTITUTIONS_FILENAME, institutions); err != nil {
		logger.Warnf(mainCtx, "[!] %s not refreshed (keeping %s): %v", CSRANKINGS_INSTITUTIONS_FILENAME, COUNTRY_INFO_FILENAME, err)
	} else if err := writeCountryInfo(institutions, path.Join(dataDir, COUNTRY_INFO_FILENAME)); err != nil {
		return err
	}
	// geolocation.csv is no longer published; the local copy stays (coordinates now come from
	// backup/university_coordinates.csv and IPEDS first).
	return nil
}

// downloadFile replaces dest with url's body, only after the whole body has arrived.
func downloadFile(url, dest string) error {
	client := &http.Client{Timeout: 5 * time.Minute}
	resp, err := client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	tmp := dest + ".part"
	out, err := os.Create(tmp)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, resp.Body); err != nil {
		out.Close()
		os.Remove(tmp)
		return err
	}
	if err := out.Close(); err != nil {
		return err
	}
	return os.Rename(tmp, dest)
}

// writeCountryInfo writes institution,region,countryabbrv from CSRankings' institutions.csv.
func writeCountryInfo(src, dest string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	records, err := csv.NewReader(in).ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read %s: %w", src, err)
	}
	out, err := os.Create(dest + ".part")
	if err != nil {
		return err
	}
	w := csv.NewWriter(out)
	for _, rec := range records {
		if len(rec) >= 3 {
			if err := w.Write(rec[:3]); err != nil {
				out.Close()
				return err
			}
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		out.Close()
		return err
	}
	if err := out.Close(); err != nil {
		return err
	}
	return os.Rename(dest+".part", dest)
}

// DownloadNSFData fetches and extracts NSF award data per year.
func downloadNSFData(mainCtx *colly.Context) error {

	dataDir := getRootDirPath(DATA_DIR)
	nsfDataDir := path.Join(dataDir, NSF_DATA_DIR)

	client := &http.Client{Timeout: 30 * time.Minute}
	for year := NSFAwardsStartYear; year <= nsfAwardsEndYear(); year++ {
		zipFile := filepath.Join(nsfDataDir, fmt.Sprintf("nsf_awards_%d.zip", year))
		extractDir := filepath.Join(nsfDataDir, fmt.Sprintf("%d", year))
		target := extractDir // where this download is extracted

		// The current year keeps growing: it is downloaded again once its copy is a week old, extracted
		// next to the old one and swapped in only when complete.
		if info, err := os.Stat(extractDir); err == nil {
			if year != nsfAwardsEndYear() || time.Since(info.ModTime()) < 7*24*time.Hour {
				logger.Infof(mainCtx, "[✓] %s already exists. Skipping download.", filepath.Base(extractDir))
				continue
			}
			target = extractDir + ".new"
			_ = os.RemoveAll(target)
		}

		logger.Infof(mainCtx, "[*] Downloading %s ...", filepath.Base(zipFile))

		resp, err := client.Get(fmt.Sprintf("%s%d", NSFURLPrefix, year))
		if err != nil {
			logger.Errorf(mainCtx, "[!] Failed to fetch %s: %v", filepath.Base(zipFile), err)
			continue
		}

		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			logger.Errorf(mainCtx, "[!] Failed to download %s. Status: %d, Body: %s", filepath.Base(zipFile), resp.StatusCode, string(body))
			continue
		}

		outFile, err := os.Create(zipFile)
		if err != nil {
			logger.Errorf(mainCtx, "[!] Cannot create file %s: %v", zipFile, err)
			continue
		}

		defer outFile.Close()

		if _, err = io.Copy(outFile, resp.Body); err != nil {
			logger.Errorf(mainCtx, "[!] Error writing file %s: %v", zipFile, err)
			continue
		}

		logger.Infof(mainCtx, "[✓] %s downloaded.", filepath.Base(zipFile))

		if _, err = os.Stat(target); err == nil {
			logger.Infof(mainCtx, "[✓] Already extracted to %s", target)
			continue
		}

		logger.Infof(mainCtx, "[*] Extracting %s to %s ...", filepath.Base(zipFile), target)

		if err = os.MkdirAll(target, os.ModePerm); err != nil {
			logger.Errorf(mainCtx, "[!] Could not create directory %s: %v", target, err)
			continue
		}

		if err = unzip(zipFile, target); err != nil {
			logger.Errorf(mainCtx, "[!] Failed to extract %s: %v", filepath.Base(zipFile), err)
			_ = os.RemoveAll(target)
			continue
		}
		if target != extractDir {
			if err = os.RemoveAll(extractDir); err == nil {
				err = os.Rename(target, extractDir)
			}
			if err != nil {
				logger.Errorf(mainCtx, "[!] Could not replace %s: %v", extractDir, err)
				continue
			}
		}

		logger.Infof(mainCtx, "[✓] Extracted to %s", extractDir)

		if err = os.Remove(zipFile); err != nil {
			logger.Errorf(mainCtx, "[!] Could not delete %s after extraction: %v", zipFile, err)
			continue
		}

		logger.Infof(mainCtx, "[🧹] Cleaned up %s after extraction", filepath.Base(zipFile))
	}

	return nil
}

func downloadIPEDSData(mainCtx *colly.Context) error {
	if os.Getenv("SKIP_IPEDS") != "" {
		logger.Infof(mainCtx, "ℹ️  SKIP_IPEDS is set, skipping IPEDS download (cached data is still ingested).")
		return nil
	}
	dataDir := getRootDirPath(DATA_DIR)

	for year := IPEDSCurrentlyRangedYear; year <= IPEDSLatestYear; year++ {
		// IPEDS is supplementary; a failed year must not block the rest of the pipeline
		if err := NewIPEDSFetcher(year, dataDir).DownloadAll(mainCtx); err != nil {
			logger.Warnf(mainCtx, "⚠️ Skipping IPEDS download for the year '%d'. Error: %v", year, err)
		}
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
