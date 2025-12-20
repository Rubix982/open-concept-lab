#!/usr/bin/env python3
"""
Simple Demo - No Heavy Dependencies!
Just pure Python magic to show you the arXiv integration works.
"""

import sys
import os
import time
import urllib.request
import json
from xml.etree import ElementTree


def simple_arxiv_search(query, max_results=3):
    """Search arXiv using standard library only!"""
    print(f"\n🔍 Searching arXiv for: '{query}'...")

    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{query.replace(' ', '+')}&start=0&max_results={max_results}"

    with urllib.request.urlopen(base_url + search_query) as response:
        data = response.read().decode("utf-8")

    # Parse XML (simple hacky way for demo)
    root = ElementTree.fromstring(data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        paper_id = entry.find("atom:id", ns).text.split("/")[-1]

        papers.append({"title": title, "summary": summary, "id": paper_id})

    return papers


def main():
    print("\n✨ SIMPLE DEMO (No complex install needed!) ✨")
    print("=" * 50)
    print("While the heavy AI models are installing, let's test the")
    print("core research capabilities using lightweight code.\n")

    # 1. Search
    papers = simple_arxiv_search("hierarchical attention")

    print(f"\n✅ Found {len(papers)} papers:")
    for i, p in enumerate(papers, 1):
        print(f"\n{i}. {p['title']}")
        print(f"   ID: {p['id']}")
        print(f"   Summary: {p['summary'][:100]}...")

    # 2. Simulate Download
    if papers:
        print("\n📥 Downloading the first paper...")
        print(f"   Getting PDF for {papers[0]['id']}...")
        time.sleep(1)  # Fake the network delay for drama
        print("   [====================] 100%")
        print("   ✅ Download complete! (Simulated)")

    print("\n🎉 See? The logic works! The full system will be even better.")


if __name__ == "__main__":
    main()
