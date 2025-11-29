# Makefile Commands Reference

## 🎨 Code Quality & Formatting

### `make format`
Automatically formats all Python code using `ruff`.
- Formats `src/`, `tests/`, and root-level `.py` files
- Applies consistent code style
- Safe to run anytime

### `make lint`
Runs linting and type checking with auto-fix.
- Runs `ruff check` with `--fix` to automatically fix issues
- Runs `mypy` for type checking (non-blocking)
- Shows warnings but continues on errors

### `make lint-strict`
Strict linting without auto-fix.
- Runs `ruff check` without auto-fix
- Runs `mypy` with strict checking
- Fails on any errors (good for CI/CD)

### `make format-lint`
**Recommended**: Runs both formatting and linting in sequence.
```bash
make format-lint
```
This is the command you should run before committing!

### `make check`
Complete quality check pipeline.
- Runs `format-lint`
- Runs unit tests
- Comprehensive pre-commit validation

### `make pre-commit`
Runs all pre-commit hooks.
```bash
make pre-commit
```

## 📦 Development Workflow

### Typical workflow:
```bash
# 1. Make your changes
vim src/persistent_memory/my_file.py

# 2. Format and lint
make format-lint

# 3. Run tests
make test-unit

# 4. Full check (optional)
make check

# 5. Commit
git add .
git commit -m "feat: add new feature"
```

## 🧪 Testing Commands

### `make test`
Run all tests
```bash
make test
```

### `make test-unit`
Run only unit tests
```bash
make test-unit
```

### `make test-integration`
Run integration tests
```bash
make test-integration
```

### `make test-coverage`
Generate coverage report
```bash
make test-coverage
# Opens htmlcov/index.html
```

## 🐳 Docker Commands

### `make up`
Start all services
```bash
make up
```

### `make down`
Stop all services
```bash
make down
```

### `make shell`
Open shell in app container
```bash
make shell
```

### `make logs`
View app logs
```bash
make logs
```

## 🤖 LLM Setup

### `make setup-host-llm`
Install and configure Ollama on macOS
```bash
make setup-host-llm
```

### `make pull-model`
Pull Mistral model
```bash
make pull-model
```

## 📊 Monitoring

### `make metrics`
Show monitoring URLs
```bash
make metrics
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# API Metrics: http://localhost:8080/metrics
```

## 🧹 Maintenance

### `make clean`
Remove Python cache files
```bash
make clean
```

### `make backup`
Backup database and data
```bash
make backup
```

## ⚡ Quick Reference

| Command | Description |
|---------|-------------|
| `make format` | Format code |
| `make lint` | Lint with auto-fix |
| `make format-lint` | **Format + Lint (recommended)** |
| `make check` | Full quality check |
| `make test` | Run all tests |
| `make up` | Start services |
| `make down` | Stop services |
| `make clean` | Clean cache |

## 💡 Pro Tips

1. **Before every commit**: Run `make format-lint`
2. **Before pushing**: Run `make check`
3. **CI/CD**: Use `make lint-strict` and `make test`
4. **Quick iteration**: Use `make format` while coding

## 🔧 Configuration

Linting and formatting rules are configured in:
- `pyproject.toml` - Ruff and tool settings
- `.pre-commit-config.yaml` - Pre-commit hooks
- `pytest.ini` - Test configuration

---

**Note**: All these commands are now available in your Makefile! 🎉
