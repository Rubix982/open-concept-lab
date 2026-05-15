# AI Tool Comparison Exercise — Module 5 Practice

*Module 5, Task 8: Compare Generative AI Tools across five task categories.*

---

## Setup

**Platforms being compared:** *(fill in when running)*
- Platform 1: _______________
- Platform 2: _______________

**Evaluation dimensions per task:**

| Dimension | What to look for |
|---|---|
| **Factual accuracy** | Is the answer correct? Any hallucinations or errors? |
| **Depth** | Surface-level or genuinely explanatory? |
| **Clarity** | Easy to follow? Well-structured? |
| **Bias** | Any slant, framing, or notable omission? |
| **Satisfaction** | Did it actually solve the task as asked? |

---

## Task A — Mathematics and Basic Programming

**Prompt:**

1. Which is bigger, 1.11 or 1.9?
2. Count the number of vowels in the string "lumosity"
3. Find the largest number in the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
4. Check if the string 'racecar' is a palindrome
5. Calculate the factorial of 109 in scientific notation

**Expected correct answers (for evaluation):**

| Question | Correct Answer | Common failure mode |
|---|---|---|
| 1.11 vs 1.9 | 1.9 is bigger | LLMs sometimes say 1.11 is bigger because 11 > 9 in integer comparison |
| Vowels in "lumosity" | 3 (u, o, i) | Miscounting — watch for models including 'y' or missing a vowel |
| Largest in list | 9 | Should be trivial |
| 'racecar' palindrome | Yes | Should be trivial |
| Factorial of 109 | ≈ 1.544 × 10^176 | Very large — models may hallucinate a plausible-looking but wrong answer |

**Platform 1 response:**
*(paste here)*

**Platform 2 response:**
*(paste here)*

**Evaluation:**

| Dimension | Platform 1 | Platform 2 |
|---|---|---|
| Factual accuracy | | |
| Depth | | |
| Clarity | | |
| Bias | | |
| Satisfaction | | |

**Notes:**

---

## Task B — Psychology

**Prompt:**
Explain the concept of cognitive dissonance and provide an example of how it manifests in everyday life.

**What to watch for:**
- Textbook definition vs genuinely insightful explanation
- Quality of the everyday example — generic or specific and relatable?
- Does it explain *why* dissonance arises and how people resolve it?

**Platform 1 response:**
*(paste here)*

**Platform 2 response:**
*(paste here)*

**Evaluation:**

| Dimension | Platform 1 | Platform 2 |
|---|---|---|
| Factual accuracy | | |
| Depth | | |
| Clarity | | |
| Bias | | |
| Satisfaction | | |

**Notes:**

---

## Task C — Real-Time Web Browsing

**Prompts:**

1. Create a tally of the latest Olympics medals along with the ratio of gold conversion out of the total medals earned for each nation. Print the top ten nations for that conversion ratio.

2. Provide a list of ten veterinary clinics in Maine. Convert this list into a CSV file containing name, address, and any other business-related information in separate columns.

**What to watch for:**
- Does the model have genuine real-time web access or is it simulating it?
- Models without web access will: refuse, hallucinate current data, or use stale training data
- The Olympics data will be out of date unless the model has live search
- Maine veterinary clinics should be verifiable — are names and addresses real?
- Does the CSV output actually work if pasted into a spreadsheet?

**Platform 1 response (Olympics):**
*(paste here)*

**Platform 2 response (Olympics):**
*(paste here)*

**Platform 1 response (Vet clinics CSV):**
*(paste here)*

**Platform 2 response (Vet clinics CSV):**
*(paste here)*

**Evaluation:**

| Dimension | Platform 1 | Platform 2 |
|---|---|---|
| Factual accuracy | | |
| Real-time capability | | |
| Depth | | |
| Clarity | | |
| Satisfaction | | |

**Notes:**

---

## Task D — Business Strategy

**Prompt:**
Explain how the company Amazon might change its business strategy based on advancements in AI.

**What to watch for:**
- Generic MBA language ("improve customer experience") vs specific mechanisms
- Does it identify actual strategic tradeoffs and second-order effects?
- Does it go beyond obvious points (better recommendations, faster delivery) to more structural shifts (changing labour composition, supply chain intelligence, AWS competitive positioning)?
- Any evidence of genuine strategic thinking vs pattern-matching on business jargon?

**Platform 1 response:**
*(paste here)*

**Platform 2 response:**
*(paste here)*

**Evaluation:**

| Dimension | Platform 1 | Platform 2 |
|---|---|---|
| Factual accuracy | | |
| Depth | | |
| Clarity | | |
| Bias | | |
| Satisfaction | | |
| Specificity vs generic | | |

**Notes:**

---

## Task E — Critical Reasoning

**Prompts:**

1. Evaluate this argument: "If all humans are mortal, and Socrates is a human, then Socrates is mortal."

2. Evaluate: 'Sara told her classmates that she loved her holiday in Sydney, Australia.' Is the following true: 'Sara told her classmates that she loved her holiday in the largest city of Australia'?

**Expected correct answers:**

| Question | Correct Answer | What to watch for |
|---|---|---|
| Socrates argument | Valid and sound — classic Modus Ponens | Does the model identify it correctly as a syllogism? Does it explain why it is valid vs sound? |
| Sara/Sydney question | TRUE — Sydney is Australia's largest city by population | Does the model know Sydney is Australia's largest city? Does it flag the assumption being made? Does it explain the reasoning clearly? |

**Platform 1 response:**
*(paste here)*

**Platform 2 response:**
*(paste here)*

**Evaluation:**

| Dimension | Platform 1 | Platform 2 |
|---|---|---|
| Factual accuracy | | |
| Logical reasoning quality | | |
| Depth | | |
| Clarity | | |
| Satisfaction | | |

**Notes:**

---

## Overall Comparison Summary

*(Fill in after all tasks are evaluated)*

### Which platform gave the most satisfactory answer per task?

| Task | Winner | Why |
|---|---|---|
| A — Maths/Programming | | |
| B — Psychology | | |
| C — Real-time browsing | | |
| D — Business strategy | | |
| E — Critical reasoning | | |

### Overall winner: _______________

**Why:**

### Key observations:

**Factual accuracy across both:**

**Depth comparison:**

**Clarity comparison:**

**Any biased responses noted:**

**Real-time capability:**

**The most surprising finding:**

---

## What This Exercise Reveals About AI Tools

*(Add after completing evaluation — connect to course themes)*

- The accuracy problem: which tasks revealed hallucination?
- The understanding problem: which tasks required genuine reasoning vs statistical pattern matching?
- The constraint tradeoffs: which platform optimised for which constraint (speed, accuracy, depth)?
- The tool selection implication: for which real-world use cases would each platform be appropriate?
