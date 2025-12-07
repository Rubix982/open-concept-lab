package scraperworker

import (
	"fmt"
	"os"
)

const (
	APP_ENV_FLAG    = "APP_ENV"
	SCRIPTS_DIR     = "scripts"
	EMBEDDER_SCRIPT = "embedder.py"
)

func getEmbedderFilePath() string {
	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/%v", EMBEDDER_SCRIPT)
	}

	return fmt.Sprintf("%v", EMBEDDER_SCRIPT)
}
