# main.py

## Standard library imports
import os
import re
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, List

## Installed package imports
import requests
import bs4
from markdownify import markdownify as md
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATA_DIR = Path.home() / ".sudoku"
DATA_FILE = DATA_DIR / "codeforces_problems.json"
CODEFORCES_BASE_URL = "https://codeforces.com"
API_URL = f"{CODEFORCES_BASE_URL}/api"
PROXY = os.getenv("PROXY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# OPTIONS
OptionRandom = "random"
OptionShow = "show"
OptionQuit = "quit"
OptionExit = "exit"
OptionTag = "tag"


def generate_problem_analysis(problem_markdown: str) -> str:
    if OPENAI_API_KEY == "":
        print("[*] OpenAI API Key not found. Exiting ...")
        return ""

    print("[*] OpenAI API Key found.")
    prompt = f"""
You are an expert competitive programming instructor and system architect with a talent for clear, insightful explanations.

Given the following Codeforces problem statement (in markdown format), produce a comprehensive analysis with a strong learning roadmap. Your response should be a markdown document with the following sections:

---

## 1. Concise Problem Summary

Briefly summarize the problem in 2-3 sentences. Highlight the key challenge without restating the entire statement.

## 2. General Themes and Problem Patterns

Identify fundamental themes, paradigms, or patterns. Explain how these patterns guide the problem-solving approach.

## 3. Relevant Algorithms, Data Structures, and Techniques

List **all relevant algorithms, data structures, and computational techniques**, including advanced ones, even if not strictly necessary. For each:

- Why it is relevant
- How it could be applied
- Trade-offs and alternatives
- Recommended resources (books, tutorials, papers, links)

Include algorithms from all domains:

- Graph algorithms (BFS, DFS, Dijkstra, Bellman-Ford, MST, flow algorithms)
- Dynamic Programming (DP optimizations, memoization, DP on trees/graphs)
- Number theory (modular arithmetic, combinatorics, prime factorization)
- String algorithms (KMP, Z-algorithm, suffix arrays, tries)
- Data structures (segment trees, Fenwick trees, persistent DS, heaps, hashmaps)
- Greedy, divide & conquer, backtracking, bit manipulation, etc.

## 4. System Design and Architectural Insights (if applicable)

Explain any real-world analogies or system-level considerations related to the problem structure or constraints.

## 5. Practical Learning Tips and Next Steps

- Step-by-step ways to master the skills in this problem
- Related problems to practice on Codeforces, LeetCode, AtCoder
- Mistakes or pitfalls to avoid
- How to connect this problem to broader algorithmic expertise

## 6. Code Sample

A code sample in Python, C, Java or a popular programming language that illustrates the key algorithm or technique used in this problem. Ensure it is well-commented and easy to understand.

```python
def example_algorithm(data):
    # This is a simple example algorithm
    result = []
    for item in data:
        if item not in result:
            result.append(item)
    return result
```

Please make sure to add relevant comments where appropriate to inform the user of what to do and why some logic exists.

Try to use some interesting programming built-in constructs that users can remember to use during actual contests to build up muscle memory and improve standard library knowledge.

## 7. Learning Roadmap

Provide a **checklist of algorithms and data structures to master**, sorted from basic to advanced. Include:

- Short description
- Example problem(s) to practice
- Reference links or books
- Tips for efficient learning

---

### Problem Statement:

{problem_markdown}

---

Please ensure your response:

- Uses clear and precise language accessible to intermediate to advanced learners
- Structures the markdown with headings, bullet points, and code examples if relevant
- Avoids unnecessary repetition of the problem statement
- Provides actionable insights and encourages deeper learning
- Mentions related problems and resources (e.g., similar Codeforces or LeetCode problems)
- Lists common mistakes and pitfalls that cause issues
- Provides a small code snippet for an example
- Use clear, structured markdown with headings, bullet points, and code examples
- Avoid repeating the problem unnecessarily
- Make it actionable: after reading, a student should know **exactly which algorithms to master and in which order**
- Mention common mistakes and pitfalls
- Provide small illustrative code snippets where relevant
- Ensure links or book references are actionable and credible

Thank you.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1200,
        n=1,
    )

    return response.choices[0].message.content.strip()


def extract_samples(soup):
    samples_div = soup.find("div", class_="sample-tests")
    if not samples_div:
        return ""

    sample_test_div = samples_div.find("div", class_="sample-test")
    if not sample_test_div:
        return ""

    inputs = sample_test_div.find_all("div", class_="input")
    outputs = sample_test_div.find_all("div", class_="output")

    results = []
    for i, (inp, outp) in enumerate(zip(inputs, outputs), start=1):
        inp_text = inp.find("pre").get_text("\n", strip=True)
        out_text = outp.find("pre").get_text("\n", strip=True)

        example_md = (
            f"### Example {i}\n\n"
            f"Input\n\n```text\n{inp_text}\n```\n\n"
            f"Output\n\n```text\n{out_text}\n```\n"
        )
        results.append(example_md)

    return "\n".join(results)


#     save_problem_markdown(problem_name, index, problem_rating, contest_id, md_text)
def save_problem_markdown(
    problem_name: str,
    index: str,
    md_text: str,
    problem_rating: int,
    contest_id: int,
) -> None:
    # Create a folder ~/.sudoku/problems if it doesn't exist
    base_dir = Path.home() / ".sudoku" / "problems"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Get current date and time in YYYY-MM-DD_HH-MM-SS format
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Compose filename with date and time e.g. E_611_2025-08-09_14-30-15.md
    problem_name = re.sub(r"[^\w\s]", "", problem_name)  # Remove special characters
    problem_name = problem_name.replace(" ", "_")  # Replace spaces with underscores
    problem_name = problem_name[:50]  # Limit to 50 characters for filename safety
    problem_name = problem_name.replace("_", "-")  # Replace underscores with hyphens
    filename = f"{problem_name}_{problem_rating}_{index}_{contest_id}_{date_str}.md"
    file_path = base_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"[+] Saved cleaned problem statement to {file_path}")


def remove_classes_from_div(main_div, classes_to_remove: list[str]):
    for class_to_remove in classes_to_remove:
        for div in main_div.find_all("div", class_=class_to_remove):
            div.decompose()  # completely removes the div from the tree
    return main_div


def requests_get(url: str) -> requests.Response:
    return requests.get(url, verify=PROXY)


def fetch_problem_statement(
    problem_name: str,
    index: str,
    problem_rating: int,
    contest_id: int,
    max_retries: int = 5,
    backoff_factor: float = 1.5,
) -> str:
    """
    Fetches the Codeforces problem statement with retry logic on failures.
    max_retries: number of retries before giving up
    backoff_factor: multiplier for exponential backoff in seconds
    """
    url = f"{CODEFORCES_BASE_URL}/problemset/problem/{contest_id}/{index}"
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests_get(url)
            resp.raise_for_status()
            break  # success, exit loop
        except requests.RequestException as e:
            print(f"[!] Attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                raise
            sleep_time = backoff_factor ** (attempt - 1)
            print(f"[*] Retrying in {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
    else:
        raise Exception(
            f"Failed to fetch problem statement after {max_retries} attempts"
        )

    # Problem statements are inside divs with class 'problem-statement'
    prob_div: Union[bs4.Tag, bs4.NavigableString, None] = bs4.BeautifulSoup(
        resp.text, "html.parser"
    ).find("div", class_="problem-statement")
    if not prob_div:
        raise Exception("Problem statement div not found")

    # Clean tex spans
    for span in prob_div.find_all("span", class_="tex-span"):
        span.replace_with(span.get_text())

    # Simplify superscripts
    for sup in prob_div.find_all("sup"):
        sup.replace_with("^" + sup.get_text())

    # Optional: flatten <i> tags too
    for i_tag in prob_div.find_all("i"):
        i_tag.unwrap()

    extracted_samples = extract_samples(prob_div)
    prob_div = remove_classes_from_div(
        prob_div,
        [
            "input-file input-standard",
            "output-file output-standard",
            "sample-test",
        ],
    )
    header_div = prob_div.find("div", class_="header")
    title = header_div.find("div", class_="title").text.strip()
    time_limit_div = header_div.find("div", class_="time-limit")
    time_limit_value = time_limit_div.find("div", "property-title").next_sibling.strip()
    memory_limit_div = header_div.find("div", class_="memory-limit")
    memory_limit_value = memory_limit_div.find(
        "div", "property-title"
    ).next_sibling.strip()
    prob_div = remove_classes_from_div(
        prob_div, ["time-limit", "memory-limit", "title"]
    )
    md_text = md(str(prob_div), heading_style="ATX")
    md_text = re.sub(r"\$\$\$(.+?)\$\$\$", r"\1", md_text)
    md_text = re.sub(r"(?i)^input$", "## Input", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"(?i)^output$", "## Output", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"(?i)^note$", "## Note", md_text, flags=re.MULTILINE)
    md_text = (
        f"# {title}\n\n"
        f"**Time Limit:** {time_limit_value}\n\n"
        f"**Memory Limit:** {memory_limit_value}\n\n"
        "## Description\n\n"
        f"{md_text.strip()}\n\n"
        "---\n\n"
        "## Examples\n\n"
        f"{extracted_samples}"
    )

    md_text = (
        f"{md_text}\n"
        "## OpenAI Analysis\n\n"
        f"\n{generate_problem_analysis(md_text).strip()}\n"
    )

    # Save locally
    save_problem_markdown(problem_name, index, md_text, problem_rating, contest_id)
    return md_text


def fetch_problems():
    print("[*] Fetching problems from Codeforces...")

    resp = requests_get(f"{API_URL}/problemset.problems")
    resp.raise_for_status()

    data = resp.json()
    if data["status"] != "OK":
        raise Exception("Error fetching problems from Codeforces")

    problems = data["result"]["problems"]
    print(f"[+] Got {len(problems)} problems")

    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)

    print(f"[+] Saved problems to {DATA_FILE}")


def load_problems():
    if not DATA_FILE.exists():
        print("[-] Problem data not found. Running fetch_problems first ...")
        fetch_problems()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def search_by_tag(problems, tag):
    return [p for p in problems if tag in p.get("tags", [])]


def random_problem(problems):
    return random.choice(problems)


def get_problem_under_max_rating(problems, max_rating=1200):
    """Return a random easy problem (<= max_rating)."""
    easy_problems = [
        p for p in problems if p.get("rating") and p["rating"] <= max_rating
    ]
    if not easy_problems:
        print(f"[-] No problems found with rating <= {max_rating}")
        return None
    return random.choice(easy_problems)


def main():
    problems = load_problems()
    if not problems:
        return

    print(
        "[*] Codeforces CLI — commands: tag <tag>, random [max_rating], show, quit/exit"
    )
    last_random_problem_selected = None

    try:
        while True:
            cmd: list[str] = input("> ").strip().split(maxsplit=1)
            if not cmd:
                continue
            if cmd[0] in [OptionQuit, OptionExit]:
                break
            elif cmd[0] == "tag" and len(cmd) > 1:
                results = search_by_tag(problems, cmd[1])
                for p in results[:10]:  # show only first 10 matches
                    print(
                        f"{p['contestId']}{p['index']}: {p['name']} (tags: {p['tags']})"
                    )
                print(f"[+] Found {len(results)} problems with tag '{cmd[1]}'")
            elif cmd[0] == OptionRandom:
                max_rating = 1200  # default
                if len(cmd) > 1 and cmd[1].isdigit():
                    max_rating = int(cmd[1])  # allow user to set threshold

                while True:
                    p = get_problem_under_max_rating(problems, max_rating=max_rating)
                    if not p:
                        print(f"[-] No problems found with rating <= {max_rating}")
                        break
                    elif (
                        last_random_problem_selected
                        and last_random_problem_selected == p
                    ):
                        print(
                            "[*] Same problem selected as last time. Selecting a new one..."
                        )
                        continue
                    else:
                        break

                if p:
                    last_random_problem_selected = p
                    url = f"{CODEFORCES_BASE_URL}/problemset/problem/{p['contestId']}/{p['index']}"
                    print(
                        f"[Rating ≤{max_rating}] {p['name']} — {url} (rating: {p.get('rating')}, tags: {p['tags']})"
                    )
            elif cmd[0] == OptionShow:
                if last_random_problem_selected == None:
                    print(
                        "[*] Please first run 'random' to have a random problem in memory"
                    )
                    continue

                print(
                    fetch_problem_statement(
                        last_random_problem_selected["name"],
                        last_random_problem_selected["index"],
                        last_random_problem_selected["rating"],
                        last_random_problem_selected["contestId"],
                    )
                )
            else:
                print("Unknown command")
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting gracefully...")
        # Optional: do any cleanup here
        exit(0)


if __name__ == "__main__":
    main()
