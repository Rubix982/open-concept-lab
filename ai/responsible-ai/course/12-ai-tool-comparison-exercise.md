# AI Tool Comparison Exercise — Module 5 Practice

_Module 5, Task 8: Compare Generative AI Tools across five task categories._

---

## Setup

**Platforms being compared:** _(fill in when running)_

- Platform 1: ******\_\_\_******
- Platform 2: ******\_\_\_******

**Evaluation dimensions per task:**

| Dimension            | What to look for                                     |
| -------------------- | ---------------------------------------------------- |
| **Factual accuracy** | Is the answer correct? Any hallucinations or errors? |
| **Depth**            | Surface-level or genuinely explanatory?              |
| **Clarity**          | Easy to follow? Well-structured?                     |
| **Bias**             | Any slant, framing, or notable omission?             |
| **Satisfaction**     | Did it actually solve the task as asked?             |

---

## Task A — Mathematics and Basic Programming

**Prompt:**

1. Which is bigger, 1.11 or 1.9?
2. Count the number of vowels in the string "lumosity"
3. Find the largest number in the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
4. Check if the string 'racecar' is a palindrome
5. Calculate the factorial of 109 in scientific notation

**Expected correct answers (for evaluation):**

| Question             | Correct Answer   | Common failure mode                                                      |
| -------------------- | ---------------- | ------------------------------------------------------------------------ |
| 1.11 vs 1.9          | 1.9 is bigger    | LLMs sometimes say 1.11 is bigger because 11 > 9 in integer comparison   |
| Vowels in "lumosity" | 3 (u, o, i)      | Miscounting — watch for models including 'y' or missing a vowel          |
| Largest in list      | 9                | Should be trivial                                                        |
| 'racecar' palindrome | Yes              | Should be trivial                                                        |
| Factorial of 109     | ≈ 1.544 × 10^176 | Very large — models may hallucinate a plausible-looking but wrong answer |

**Platforms tested:** Claude, Gemini, ChatGPT (all three run for comparison)

**Platform 1 (Claude) response:**

1. 1.9 is bigger. Notes the common confusion (digit count vs value). 1.9 = 1.90 > 1.11.
2. 3 vowels: u, o, i
3. Largest: 9
4. racecar is a palindrome
5. 109! ≈ 1.443860 × 10¹⁷⁶

**Platform 2 (Gemini) response:**
Provided Python code using math.factorial(), then ran it and printed results:
bigger=1.9, vowel_count=3, largest_num=9, is_palindrome=True, factorial_109=1.44e+176
Then summarised answers in plain text below the code block.

**Platform 3 (ChatGPT) response:**

1. 1.9 is bigger
2. Vowels: u, o, i — Total = 3
3. Largest = 9
4. Yes, palindrome
5. 109! ≈ 1.4438595832 × 10¹⁷⁶ (more decimal places than other two)

**Evaluation:**

| Dimension        | Claude                                         | Gemini                                          | ChatGPT                       |
| ---------------- | ---------------------------------------------- | ----------------------------------------------- | ----------------------------- |
| Factual accuracy | ✓ All correct                                  | ✓ All correct                                   | ✓ All correct                 |
| Depth            | Added contextual note on common 1.11 confusion | Showed working code + output — most transparent | Clean, no extras              |
| Clarity          | Prose with bold answers — easy to read         | Two-part: code then summary — slightly verbose  | Numbered list, clean format   |
| Bias             | None                                           | None                                            | None                          |
| Satisfaction     | High                                           | High — bonus: shows how it computed             | High — most precise factorial |

**Notes:**

- All three got every answer correct — this is a clean factual task with no ambiguity
- **Factorial precision:** ChatGPT gave the most decimal places (1.4438595832 × 10¹⁷⁶). Claude gave 1.443860 × 10¹⁷⁶. Gemini gave 1.44 × 10¹⁷⁶. All three are correct — just different rounding.
- **Most interesting difference:** Gemini showed its working by generating and "running" Python code. This is the most transparent — the user can see _how_ the answer was produced. This matters for the understanding problem: Gemini is showing reckoning, not just asserting a result.
- **Claude's added note** on the 1.11 vs 1.9 confusion is useful pedagogically — it anticipates why this question was asked.
- **Winner for Task A:** Gemini for transparency of method; ChatGPT for factorial precision; Claude for contextual insight. No clear single winner — task-appropriate model depends on what you need.

---

## Task B — Psychology

**Prompt:**
Explain the concept of cognitive dissonance and provide an example of how it manifests in everyday life.

**What to watch for:**

- Textbook definition vs genuinely insightful explanation
- Quality of the everyday example — generic or specific and relatable?
- Does it explain _why_ dissonance arises and how people resolve it?

**Platform 1 (Claude) response:**
Definition: mental discomfort when holding conflicting beliefs or when behaviour contradicts held beliefs. Example: software engineer ships bad code under deadline pressure, resolves by telling himself "I'll refactor it later." Ends with a practical takeaway: the dissonance itself is useful signal — sit with it, ask whether you are adjusting your belief to protect a behaviour you should stop.

**Platform 2 (Gemini) response:**
Identical text to Claude's response, plus generated a concept map image showing: Contradictory Beliefs, Mental Discomfort, Behavior Conflict, Attitude Change, Belief Adjustment, Cognitive Tension, Rationalization, Consistency Drive, Psychological Theory arranged around a central "Cognitive Dissonance" node.

**Platform 3 (ChatGPT) response:**
Attributed to Leon Festinger (1950s) — historically grounded. Smoking example (classic textbook case). Explains three resolution strategies: quit, justify, minimise. Second example: overspending on a phone. Lists domains where dissonance appears (relationships, politics, religion, consumer behaviour, career, health). More comprehensive coverage, less sharp insight.

**Evaluation:**

| Dimension | Claude | Gemini | ChatGPT |
|---|---|---|---|
| Factual accuracy | ✓ Correct | ✓ Correct (identical) | ✓ Correct, adds Festinger attribution |
| Depth | High — gets to the self-discipline implication | High — same text + visual concept map | Medium-High — broad coverage, less sharp |
| Clarity | Excellent — tight, specific, memorable | Same text + image aids visual learners | Good — clear structure, slightly textbook |
| Bias | None | None | None |
| Satisfaction | High — most insightful single answer | High — same insight + better visual | High — most comprehensive, least memorable |

**Notes:**

- **The identical Claude/Gemini response is the most important finding of Task B.** Gemini produced word-for-word the same text as Claude. This almost certainly means Gemini retrieved Claude's response (or a source that Claude trained on) rather than generating independently. It raises the question: when two models produce identical text on a subjective task, one of them is not generating — it is retrieving. This is the reckoning problem made visible.
- **Gemini added a concept map image** — a genuine multimodal contribution that Claude and ChatGPT did not provide. For a visual learner or for a presentation, this is valuable.
- **ChatGPT's Festinger attribution** is correct and useful — it grounds the concept historically. Neither Claude nor Gemini mentioned Festinger by name.
- **Claude/Gemini's software engineer example** is more professionally specific and more memorable than ChatGPT's smoking/overspending examples. The "I'll refactor it later" line is pithy and accurate.
- **The practical self-discipline takeaway** (the dissonance is the signal — sit with it) goes beyond what the question asked and is the most insightful addition.
- **Winner for Task B:** Claude/Gemini for insight and specificity; ChatGPT for breadth and historical grounding; Gemini uniquely for the visual. For a psychology course, ChatGPT's Festinger attribution matters. For practical application, Claude's framing is sharper.

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

**ChatGPT Olympics response:**
Retrieved live data from the Paris 2024 official medal table. Ranked top 10 by gold conversion ratio — BUT got the methodology wrong. Sorted by large-medal-count nations (Japan 44.44%, China 43.96%, etc.) rather than by actual highest conversion ratio. Pakistan (100%) and Dominica (100%) should be #1 and #2. ChatGPT misread "top ten by conversion ratio" as "top ten overall nations" filtered by conversion. Also produced a map of Maine vet clinics with ratings, generated a downloadable CSV, cited sources.

**Gemini Olympics response:**
Generated Python code, included more countries in the dataset (24 nations), correctly sorted by Gold Ratio — Pakistan 100%, Dominica 100%, Slovenia 66.7%, Uzbekistan 61.5% correctly at top. CSV file offered as download. More methodologically correct but data was from training/scraping not fully verified live.

**Claude Olympics response:**
Retrieved full 63-nation IOC medal table with web search. Correctly identified Dominica and Pakistan at 100%, Algeria and Indonesia at 66.7% that Gemini missed, produced a full downloadable MD table and separate CSV. Added a nuanced note: "Among nations with 10+ medals, Uzbekistan (61.5%) is the standout" — acknowledging the trivial sample problem of 1-medal nations. Generated both files as downloadable artifacts.

**Veterinary clinics:**
- ChatGPT: 10 Maine clinics with map overlay showing ratings, full CSV with name/address/city/state/ZIP/category/rating/review count/phone/website
- Gemini: Same 10 clinics listed but fewer data columns in CSV
- Claude: Different 10 clinics (Portland/Bangor/Brunswick/Blue Hill focus), 9-column CSV with hours and specialty notes, cited Yelp + 8 additional sources

**Evaluation:**

| Dimension | ChatGPT | Gemini | Claude |
|---|---|---|---|
| Factual accuracy — Olympics | ✗ Wrong top 10 (sorted incorrectly) | ✓ Correctly sorted by ratio | ✓ Most complete — 63 nations, correct sort |
| Factual accuracy — Vet clinics | Likely real (map integration suggests live data) | Plausible but less verifiable | Cited sources (Yelp + 8 more) — most verifiable |
| Real-time capability | ✓ Confirmed — live map, ratings, source links | Partial — Python code with hardcoded data | ✓ Confirmed — web search, full IOC table |
| Depth | Medium — good presentation, wrong analysis | Medium — correct analysis, limited nations | High — 63 nations, nuanced note on trivial samples |
| Clarity | High — beautiful map, clean table | High — code + clean table | High — full table + clean top-10 summary |
| Satisfaction — Olympics | Low — answered wrong question | Medium — correct method, limited data | High — correct method, complete data, nuanced |
| Satisfaction — Vet clinics | High — map, ratings, rich CSV | Medium — correct but fewer columns | High — cited sources, more detail per clinic |

**Notes — the most important findings of Task C:**

**1. ChatGPT's Olympics answer was factually wrong in a specific way.**
The question asked for top 10 by gold conversion ratio. ChatGPT retrieved real data but then ranked by a different criteria — showing the major powers (Japan, China, USA) rather than the actual highest-conversion nations. This is the question-misreading failure. It produced a confident, beautifully formatted, sourced answer to the wrong question. This is the most dangerous failure mode: correct data, wrong analysis, confident presentation.

**2. Claude produced the correct and most complete answer.**
63-nation table, correct sort, added the nuanced observation that 1-medal nations are trivial samples and Uzbekistan is the standout among meaningful-volume nations. This is the kind of judgment that goes beyond mechanical execution of the task.

**3. The presentation gap was enormous.**
ChatGPT produced a live map with clinic ratings visible. Claude produced a downloadable structured CSV with cited sources. These serve different needs — ChatGPT for quick browsing, Claude for data work. Neither is objectively better — depends entirely on what you need the output for.

**4. Gemini's Python code approach produced the correct Olympic analysis** but with a smaller dataset (24 nations vs Claude's 63). The code transparency is valuable — you can see exactly what it computed. The data limitation is significant.

**5. Winner for Task C:** Claude for accuracy and completeness on Olympics; ChatGPT for richness and usability on vet clinics (map integration is genuinely impressive). Gemini correct but limited. The lesson: real-time capability and correct task interpretation are separate dimensions that no single model maximised simultaneously.

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
_(paste here)_

**Platform 2 response:**
_(paste here)_

**Evaluation:**

| Dimension              | Platform 1 | Platform 2 |
| ---------------------- | ---------- | ---------- |
| Factual accuracy       |            |            |
| Depth                  |            |            |
| Clarity                |            |            |
| Bias                   |            |            |
| Satisfaction           |            |            |
| Specificity vs generic |            |            |

**Notes:**

---

## Task E — Critical Reasoning

**Prompts:**

1. Evaluate this argument: "If all humans are mortal, and Socrates is a human, then Socrates is mortal."

2. Evaluate: 'Sara told her classmates that she loved her holiday in Sydney, Australia.' Is the following true: 'Sara told her classmates that she loved her holiday in the largest city of Australia'?

**Expected correct answers:**

| Question             | Correct Answer                                          | What to watch for                                                                                                                      |
| -------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Socrates argument    | Valid and sound — classic Modus Ponens                  | Does the model identify it correctly as a syllogism? Does it explain why it is valid vs sound?                                         |
| Sara/Sydney question | TRUE — Sydney is Australia's largest city by population | Does the model know Sydney is Australia's largest city? Does it flag the assumption being made? Does it explain the reasoning clearly? |

**Platform 1 response:**
_(paste here)_

**Platform 2 response:**
_(paste here)_

**Evaluation:**

| Dimension                 | Platform 1 | Platform 2 |
| ------------------------- | ---------- | ---------- |
| Factual accuracy          |            |            |
| Logical reasoning quality |            |            |
| Depth                     |            |            |
| Clarity                   |            |            |
| Satisfaction              |            |            |

**Notes:**

---

## Overall Comparison Summary

_(Fill in after all tasks are evaluated)_

### Which platform gave the most satisfactory answer per task?

| Task                   | Winner | Why |
| ---------------------- | ------ | --- |
| A — Maths/Programming  |        |     |
| B — Psychology         |        |     |
| C — Real-time browsing |        |     |
| D — Business strategy  |        |     |
| E — Critical reasoning |        |     |

### Overall winner: ******\_\_\_******

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

_(Add after completing evaluation — connect to course themes)_

- The accuracy problem: which tasks revealed hallucination?
- The understanding problem: which tasks required genuine reasoning vs statistical pattern matching?
- The constraint tradeoffs: which platform optimised for which constraint (speed, accuracy, depth)?
- The tool selection implication: for which real-world use cases would each platform be appropriate?
