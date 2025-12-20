# 🎯 Quick Reference Cheat Sheet

## ⚡ Start Here (Copy & Paste)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start services
make up

# 3. Run demo
python quick_demo.py
```

---

## 📋 Essential Commands

| What | Command |
|------|---------|
| **Search papers** | `python -m persistent_memory.cli search-papers "transformers"` |
| **Download paper** | `python -m persistent_memory.repo_cli get 1706.03762` |
| **Check cache** | `python -m persistent_memory.repo_cli stats` |
| **Ingest papers** | `python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms` |
| **Query system** | `python -m persistent_memory.cli query "What is attention?"` |
| **List conferences** | `python -m persistent_memory.cli list-conferences` |

---

## 🐳 Docker

| What | Command |
|------|---------|
| **Start** | `make up` |
| **Stop** | `make down` |
| **Logs** | `make logs` |
| **Status** | `docker-compose ps` |

---

## 🎨 Code Quality

| What | Command |
|------|---------|
| **Format & Lint** | `make format-lint` |
| **Tests** | `make test` |
| **Full Check** | `make check` |

---

## 🎓 Demos

| Demo | Command |
|------|---------|
| **Quick Demo** | `python quick_demo.py` |
| **Conferences** | `python demo_conferences.py` |
| **Papers** | `python demo_papers.py` |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Module not found** | `export PYTHONPATH=$PYTHONPATH:$(pwd)/src` |
| **Services down** | `make up` |
| **Dependencies missing** | `pip install -r requirements.txt` |
| **ChromaDB error** | `pip install pydantic-settings` |

---

## 📚 Curated Collections

- `attention_mechanisms` - Transformer papers
- `rag_systems` - RAG papers
- `memory_networks` - Memory papers
- `hierarchical_models` - Hierarchical papers

**Use:** `--collection=attention_mechanisms`

---

## 🏛️ Conferences

NeurIPS • ICML • ICLR • CVPR • ACL • SIGGRAPH

**Use:** `--name=neurips --year=2023`

---

## 📖 Full Docs

- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete guide
- [MAKEFILE_COMMANDS.md](MAKEFILE_COMMANDS.md) - All commands
- [DEMO_OUTPUT.md](DEMO_OUTPUT.md) - Example outputs
