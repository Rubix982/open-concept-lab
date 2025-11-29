#!/usr/bin/env python3
"""Quick demo script to show the system working."""

import subprocess
import time


def run_cmd(cmd):
    """Run command and print output."""
    print(f"\n{'=' * 60}")
    print(f"Running: {cmd}")
    print("=" * 60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0


def main():
    print("🚀 Persistent Memory PoC Demo")
    print("=" * 60)

    # Check services
    print("\n📊 Checking Services...")
    run_cmd("docker-compose ps")

    # Check Ollama
    print("\n🤖 Checking Ollama...")
    run_cmd("ollama list")

    # Show what we ingested
    print("\n📚 Ingested Data:")
    run_cmd("wc -l data/pride_and_prejudice_full.txt")

    # Run some queries
    queries = [
        "Who is Elizabeth Bennet?",
        "What is Mr. Darcy's first impression of Elizabeth?",
        "Describe the relationship between Jane and Bingley",
        "What role does Lady Catherine play?",
        "How does the story end?",
    ]

    print("\n🔍 Running Queries...")
    for i, query in enumerate(queries, 1):
        print(f"\n\n{'=' * 60}")
        print(f"Query {i}/{len(queries)}: {query}")
        print("=" * 60)
        run_cmd(f'docker-compose exec app python -m persistent_memory.cli query "{query}"')
        time.sleep(1)  # Rate limit

    # Show stats
    print("\n\n📈 System Stats:")
    run_cmd(
        "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep persistent"
    )

    print("\n\n✅ Demo Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check Temporal UI: http://localhost:8088")
    print("2. View Grafana: http://localhost:3000 (admin/admin)")
    print("3. API docs: http://localhost:8080/docs")
    print("4. Prometheus: http://localhost:9090")


if __name__ == "__main__":
    main()
