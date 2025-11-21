# Contributing Guide

## Welcome! 🎉

Thank you for your interest in contributing to the Persistent Memory Models project!

## Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/[your-org]/persistent-memory-models.git
cd persistent-memory-models
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
```

### 3. Install pre-commit hooks
```bash
pre-commit install
```

### 4. Start development environment
```bash
make up
make setup-host-llm
```

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Run before committing:
```bash
make format
make lint
make test
```

## Testing

### Unit Tests
```bash
make test-unit
```

### Integration Tests
```bash
make test-integration
```

### Benchmarks
```bash
make test-benchmark
```

## Pull Request Process

1. **Create a branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Follow code style guidelines
3. **Add tests**: Ensure coverage doesn't decrease
4. **Update docs**: If adding features
5. **Run checks**: `make lint && make test`
6. **Commit**: Use conventional commits
   - `feat: add new feature`
   - `fix: resolve bug`
   - `docs: update documentation`
7. **Push**: `git push origin feature/your-feature`
8. **Open PR**: Describe changes clearly

## Architecture Decisions

For significant changes, create an ADR (Architecture Decision Record):

```bash
cp docs/architecture/ADR-template.md docs/architecture/ADR-XXX-your-decision.md
```

## Areas for Contribution

### High Priority
- [ ] Improve fact extraction quality
- [ ] Add support for Neo4j backend
- [ ] Implement query result caching
- [ ] Add multi-user support

### Medium Priority
- [ ] Improve documentation
- [ ] Add more benchmarks
- [ ] Create example notebooks
- [ ] Optimize vector search

### Good First Issues
- [ ] Add more unit tests
- [ ] Improve error messages
- [ ] Fix typos in documentation
- [ ] Add type hints

## Questions?

- Open an issue for bugs
- Start a discussion for feature ideas
- Join our Discord: [link]

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and build cool stuff together! 🚀
