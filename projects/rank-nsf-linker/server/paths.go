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

func getRootDirPath(rootSubDir string) string {
	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
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

func getMigrationsFilePath() string {

	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", MIGRATIONS_DIR)
	}

	return MIGRATIONS_DIR
}

func getResearchServicePath() string {

	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", RESEARCH_SERVICE_DIR)
	}

	return RESEARCH_SERVICE_DIR
}

func downloadCSVs() error {

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

	for _, fileName := range CSVURLs {
		url := CSRANKINGS_RAW_GITHUB + fileName
		logger.Infof("Downloading %s from %s\n", fileName, url)

		fileSavePath := fmt.Sprintf("/app/data/%s", fileName)
		if _, err := os.Stat(fileSavePath); err == nil {
			logger.Infof("[✓] %s already exists. Skipping download.\n", fileName)
			continue
		}

		resp, err := http.Get(url)
		if err != nil || resp.StatusCode != 200 {
			logger.Infof("[!] Failed to download %s. Status: %d\n", fileName, resp.StatusCode)
			continue
		}
		defer resp.Body.Close()

		out, err := os.Create(fileSavePath)
		if err != nil {
			logger.Infof("[!] Error creating file %s: %v\n", fileName, err)
			continue
		}
		defer out.Close()

		_, err = io.Copy(out, resp.Body)
		if err != nil {
			logger.Infof("[!] Error writing file %s: %v\n", fileName, err)
			continue
		}

		logger.Infof("[✓] %s downloaded.\n", fileName)
	}

	return nil
}

// DownloadNSFData fetches and extracts NSF award data per year.
func downloadNSFData() error {

	dataDir := getRootDirPath(DATA_DIR)
	nsfDataDir := path.Join(dataDir, NSF_DATA_DIR)

	for year := NSFAwardsStartYear; year <= NSFAwardsEndYear; year++ {
		zipFile := filepath.Join(nsfDataDir, fmt.Sprintf("nsf_awards_%d.zip", year))
		extractDir := filepath.Join(nsfDataDir, fmt.Sprintf("%d", year))

		if _, err := os.Stat(extractDir); err == nil {
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

		if _, err = os.Stat(extractDir); err == nil {
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
