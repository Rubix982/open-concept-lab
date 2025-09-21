# 🚀 Math + AI Reasoning Project Ideas

This document tracks small, curiosity-driven projects at the intersection of **mathematics, AI, and automated reasoning**.  
Each project is designed to be **tiny but meaningful**, something you can prototype in a weekend while demonstrating alignment with research themes like **computer-aided reasoning, proof assistants, and symbolic AI**.

---

## 🔹 1. Mini Wolfram Alpha for Proofs

- **Idea:** Input a math statement → system verifies with symbolic math or SMT solvers.
- **Tech:** Python `sympy`, `z3-solver`.
- **Example:**  
  - Input: `forall n in N, n^2 >= 0`  
  - Output: ✅ True, proved.  
- **Demonstrates:** Automated reasoning + formal verification basics.

---

## 🔹 2. Math Proof Explorer

- **Idea:** Curated set of theorems (Pythagoras, AM ≥ GM, inequalities).  
- **UI:** Click a theorem → get symbolic verification (Sympy) or solver check.  
- **Tech:** Streamlit + `sympy`.  
- **Demonstrates:** Bridging human-readable theorems + machine reasoning.

---

## 🔹 3. Counterexample Generator

- **Idea:** Users type a conjecture, system searches for counterexamples.  
- **Example:** "Is every even number > 2 prime?" → Counterexample: 4.  
- **Tech:** Python number theory libs.  
- **Demonstrates:** Computational exploration of conjectures.

---

## 🔹 4. Proof Assistant Playground

- **Idea:** Small tutorial app with a few ready-made proofs in **Lean4** or **Coq**.  
- **Format:** Jupyter or Streamlit with buttons like "Show distributivity proof."  
- **Demonstrates:** Exposure to modern proof assistants.

---

## 🔹 5. Math Q&A with LLM + Solver

- **Idea:** Hybrid: LLM parses → symbolic engine verifies/solves.  
- **Example:** User: "Integrate sin(x)^2." → Sympy returns result.  
- **Tech:** LLM (OpenAI / local) + `sympy`.  
- **Demonstrates:** AI + symbolic reasoning synergy.

---

## 🔹 6. Visual Proof Explorer

- **Idea:** Visualize geometric proofs (Pythagoras, triangle inequalities).  
- **Tech:** `manim` or `matplotlib`.  
- **Demonstrates:** Math visualization + reasoning.

---

## 🔹 7. Logic Puzzle Solver

- **Idea:** Encode classic puzzles (Einstein's riddle, Sudoku) → solve via SMT (`z3`).  
- **Tech:** `z3-solver`.  
- **Demonstrates:** Constraint solving + logic encoding.

---

## 🔹 8. Theorem Search Engine

- **Idea:** Mini "search" where user enters a math keyword → returns theorem + symbolic check.  
- **Tech:** Scraped dataset of 10-20 theorems + `sympy`.  
- **Demonstrates:** Information retrieval + reasoning.

---

## 🌱 Guiding Principles

- Keep it **small + demonstrable** (1-5 theorems, toy UI, short notebook).  
- Focus on **curiosity, not production**.  
- Tie back to **big research questions**:  
  - How can machines reason about math?  
  - How do symbolic and learning-based methods complement each other?  
