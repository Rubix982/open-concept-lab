# Technical AI

The technical dimensions of AI accountability — interpretability, safety, and dataset
problems. The honest state of the field: we deployed systems we cannot explain, at scale,
to billions of users, before we had tools to understand what they are doing.

---

## [Explainability Gap and Mechanistic Interpretability](explainability-gap-and-mechanistic-interpretability.md)
The most important note for understanding the Bau Lab context. What current XAI tools can
and cannot do: attribution at output level (useful but shallow), attention visualisation
(interpretable for researchers, not actionable for regulators), probing classifiers (can
identify concepts but not causes), RLHF fingerprinting. What we cannot do: trace a harmful
output to a specific training document, prove removal prevents recurrence, predict novel
harm patterns. What standards for safer LMs would actually require: training data auditing,
behavioural red-teaming with causal logging, formal harm taxonomies, machine unlearning,
incident reporting.

The Kaggle fluency vs understanding distinction: practitioners know which techniques
work; nobody knows why. The math genius filter as cultural construction. Two questions:
"which technique works?" vs "what is the model doing?" — the second was always the right
question. The Bau Lab is the formal research programme for the second question.

## [Dataset Geography and Cultural Representation](dataset-geography-and-cultural-representation.md)
The root problem: training data reflects who had power to document. The Ibn Rushd problem
(factual accuracy, not just diversity — the European philosophical tradition is intellectually
downstream of Islamic scholarship the model cannot depict). Per-culture dataset construction
framework: Islamic world, South Asia, Africa, East Asia, Indigenous traditions, Latin America.
Why downstream patches don't work. The consent and partnership requirement. The commercial
incentive problem. Connection to Bau Lab: the knowledge infrastructure faces the same
geography problem in research papers.

## [Biosecurity Risk](biosecurity-risk.md)
Pre-existing note on AI and biosecurity risk.

## [IAM Access Control Gap](iam-access-control-gap.md)
Pre-existing note on identity and access management gaps in AI systems.

## [Safety as Mimicry](safety-as-mimicry.md)
Pre-existing note on how AI safety practices can mimic the appearance of safety without
the substance.
