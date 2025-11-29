#!/usr/bin/env python3
"""
Demo for Conference Integration.
"""

import sys
sys.path.insert(0, 'src')

import logging
from persistent_memory.conference_connector import ConferenceConnector

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    print("🏛️  Conference Integration Demo")
    print("=" * 40)
    
    connector = ConferenceConnector()
    
    # 1. List Conferences
    print("\n1. Supported Conferences:")
    print("-" * 30)
    for conf in connector.list_conferences():
        print(f"• {conf['name']} ({conf['full_name']})")
        print(f"  Topics: {', '.join(conf['topics'])}")
    
    # 2. Fetch NeurIPS Papers
    print("\n2. Fetching recent NeurIPS papers...")
    print("-" * 30)
    papers = connector.get_conference_papers('neurips', max_results=3)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:2])}")
        print(f"   arXiv: {paper.arxiv_id}")
    
    # 3. Fetch CVPR Papers
    print("\n3. Fetching recent CVPR papers...")
    print("-" * 30)
    papers = connector.get_conference_papers('cvpr', max_results=3)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:2])}")
        print(f"   arXiv: {paper.arxiv_id}")

if __name__ == "__main__":
    main()
