# Dependency Management Guide

## 📦 Requirements Files

This project uses multiple requirements files for different environments:

### `requirements.txt` (Base)
Core dependencies needed for the application to run.
```bash
pip install -r requirements.txt
```

### `requirements-dev.txt` (Development)
Includes base requirements + development tools (testing, linting, debugging).
```bash
pip install -r requirements-dev.txt
```

### `requirements-prod.txt` (Production)
Minimal production dependencies (excludes dev tools, testing frameworks).
```bash
pip install -r requirements-prod.txt
```

## 🚀 Installation

### For Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Or use the Makefile
make install
```

### For Production
```bash
pip install -r requirements-prod.txt
```

### Using Docker
Dependencies are automatically installed in Docker containers via `Dockerfile`.

## 📋 Dependency Categories

### Core Dependencies
- **temporalio**: Workflow orchestration
- **pydantic**: Data validation
- **pydantic-settings**: Configuration management

### LLM & AI
- **openai**: OpenAI API client
- **sentence-transformers**: Text embeddings
- **torch**: Deep learning framework

### Vector Store & Database
- **chromadb**: Vector database
- **networkx**: Knowledge graph
- **redis**: Caching layer

### API & Web
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **requests**: HTTP client

### Research Paper Processing
- **feedparser**: arXiv RSS parsing
- **PyPDF2**: PDF text extraction

### Development Tools
- **pytest**: Testing framework
- **ruff**: Linting and formatting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## 🔄 Updating Dependencies

### Check for outdated packages
```bash
pip list --outdated
```

### Update all dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Update specific package
```bash
pip install --upgrade package-name
```

### Freeze current versions
```bash
pip freeze > requirements-lock.txt
```

## 🐛 Common Issues

### ChromaDB + Pydantic v2
If you see `PydanticImportError: BaseSettings has been moved`:
```bash
pip install pydantic-settings
```

### NumPy 2.0 Compatibility
Some packages don't support NumPy 2.0 yet. We pin to `<2.0.0`:
```python
numpy>=1.24.0,<2.0.0
```

### PyTorch Installation
For GPU support, install PyTorch separately:
```bash
# macOS (Metal)
pip install torch torchvision torchaudio

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📊 Dependency Tree

```
persistent-memory-models/
├── Core
│   ├── temporalio (workflows)
│   ├── pydantic (validation)
│   └── pydantic-settings (config)
├── AI/ML
│   ├── openai (LLM)
│   ├── sentence-transformers (embeddings)
│   └── torch (deep learning)
├── Storage
│   ├── chromadb (vectors)
│   ├── networkx (graphs)
│   └── redis (cache)
├── API
│   ├── fastapi (web framework)
│   └── uvicorn (server)
└── Research
    ├── feedparser (arXiv)
    └── PyPDF2 (PDF parsing)
```

## 🔐 Security

### Check for vulnerabilities
```bash
pip install safety
safety check -r requirements.txt
```

### Update security-critical packages
```bash
pip install --upgrade openai requests uvicorn
```

## 💡 Best Practices

1. **Always use virtual environments**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Pin major versions** for stability
   ```python
   package>=1.0.0,<2.0.0
   ```

3. **Separate dev and prod dependencies**
   - Keep `requirements-prod.txt` minimal
   - Use `requirements-dev.txt` for development

4. **Document why you pin versions**
   ```python
   numpy>=1.24.0,<2.0.0  # NumPy 2.0 breaks some dependencies
   ```

5. **Regularly update dependencies**
   ```bash
   make format-lint  # Check for issues after updates
   make test         # Run tests after updates
   ```

## 📚 Additional Resources

- [pip documentation](https://pip.pypa.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Dependency Management Best Practices](https://realpython.com/dependency-management-python/)

---

**Need help?** Check the main [README.md](README.md) or open an issue.
