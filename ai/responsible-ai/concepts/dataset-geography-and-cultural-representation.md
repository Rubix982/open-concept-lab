# Dataset Geography and Cultural Representation

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Root Problem

Almost every downstream fairness failure in AI image generation, language modelling,
and hiring algorithms traces back to the same upstream cause:

> **The training data was built from the documented world.
> The documented world reflects who had the power to document.**

The model does not know what it was not shown. You cannot correct this downstream
with filters, patches, or content moderation layers. The root fix is the training data.

---

## The Dataset Geography Problem

The majority of image and text training data comes from:

- Western internet platforms — Instagram, Flickr, Getty, stock photo libraries
- English-language web crawls
- Wikipedia — which itself overrepresents Western subjects, Western history,
  and Western intellectual traditions
- Digitised archives — predominantly European and North American institutional collections

The result: a model that knows European philosophy, European art, European history,
and European faces in high resolution — and knows African, Islamic, South Asian,
East Asian, Latin American, and Indigenous traditions in low resolution.

Not because those traditions are smaller or less rich. They are not.
Because the documentation of them in digitised, English-language,
internet-accessible form is smaller — as a direct consequence of which
civilisations had the resources and political power to digitise their heritage
and which did not.

The model's bias is not a technical error. It is a faithful reflection of
a centuries-long information asymmetry.

---

## The Ibn Rushd Problem — Factual Accuracy, Not Just Diversity

Ibn Rushd — known in the West as Averroes — is one of the most significant
philosophers in Western intellectual history. His commentaries on Aristotle
were the primary channel through which Aristotelian philosophy re-entered
European thought in the 12th and 13th centuries. Thomas Aquinas called him
simply "The Commentator." Without Ibn Rushd, the European philosophical
tradition that produced the Enlightenment looks fundamentally different.

A model prompted to generate "two philosophers discussing ethics" that produces
two middle-aged white men has not just failed a diversity test. It has produced
a factually inaccurate image of the history of philosophy. The European
philosophers it depicts are intellectually downstream of a Muslim Andalusian
scholar it does not know how to depict.

This is not a representation problem. It is a knowledge problem. The model
does not know what it does not know — and what it does not know includes
the intellectual genealogy of the very tradition it is confidently depicting.

**Other traditions absent or underrepresented:**

- **Islamic philosophy** — Kalam, falsafa, Sufi epistemology. Al-Ghazali's
  11th-century critique of Aristotelian philosophy is one of the most
  sophisticated philosophical arguments in any tradition.
- **South Asian philosophy** — Nagarjuna, Adi Shankaracharya, the Nyaya,
  Vaisheshika, Mimamsa, and Vedanta schools. Buddhist epistemology.
- **African philosophy** — Ubuntu ethics, Egyptian philosophical traditions
  predating Greek philosophy, contemporary African political philosophy.
- **East Asian philosophy** — Confucius, Laozi, Zhuangzi, the Neo-Confucian
  tradition, Japanese philosophical schools.
- **Indigenous philosophical traditions** — oral, relational, land-based
  knowledge systems that Western documentation almost entirely missed.
- **Latin American philosophy** — liberation theology, decolonial thought,
  Indigenous Mesoamerican and Andean philosophical traditions.

A model trained on all of these would generate a completely different image
of "two philosophers discussing ethics" — and it would be equally valid,
equally historically grounded, and more accurate.

---

## Why Downstream Patches Don't Work

**Forced demographic diversity in outputs** — artificially injecting diverse
faces into generated images — produces worse outputs, not better ones.
The model has thin knowledge of what it is generating. The images look wrong
in ways that are hard to articulate but immediately visible. Confident
wrongness dressed as representation.

**Content filters** — blocking certain demographic defaults — does not
add knowledge. It removes one wrong answer without providing the right one.

**Post-hoc auditing** — checking outputs for demographic bias after the
model is trained — tells you what is wrong without giving you the means to fix it.

The only honest fix is the upstream fix: **the training data must actually
contain what you want the model to know exists.**

---

## What Building the Dataset Actually Requires

### Per-Culture, Per-Tradition Dataset Construction

Not a single global scrape with diversity added as an afterthought.
Active, deliberate, per-culture dataset construction:

**Africa:**
- Partnerships with African universities, museums, and cultural archives
- Digitisation of philosophical texts, oral tradition documentation,
  visual cultural records
- Multiple linguistic traditions — not just English-language African content
- Coverage across sub-Saharan, North African, and East African traditions

**Islamic world:**
- Arabic, Persian, Urdu, Turkish, Malay philosophical and cultural archives
- Coverage of classical Islamic philosophy, jurisprudence, and Sufi traditions
- Partnership with institutions like Al-Azhar, University of Tehran,
  International Islamic University Malaysia
- Specifically: the visual tradition of Islamic art and manuscript illustration

**South Asia:**
- Sanskrit philosophical texts, Buddhist canonical literature,
  Jain philosophical tradition
- Multiple linguistic traditions — Hindi, Tamil, Bengali, Marathi, Telugu,
  Malayalam, Kannada, Punjabi, Sindhi
- Partnership with institutions like Banaras Hindu University, JNU,
  Indian Institute of Advanced Study
- Visual traditions: miniature painting, temple sculpture, contemporary art

**East Asia:**
- Chinese classical philosophical texts in original and translation
- Japanese philosophical traditions — Zen, Kokugaku, modern Japanese philosophy
- Korean philosophical traditions
- Partnership with institutions across China, Japan, South Korea, Taiwan

**Indigenous traditions:**
- This is the hardest and most sensitive category
- Oral traditions cannot be scraped — they must be contributed by communities
  on their own terms
- Many Indigenous communities have legitimate reasons not to contribute —
  digital preservation has historically become digital extraction
- Requires genuine sovereignty: communities control what is shared,
  how it is represented, and whether it can be used for commercial AI training
- Free, Prior, and Informed Consent (FPIC) — the international standard
  for Indigenous community engagement — as the minimum bar

**Latin America:**
- Indigenous Mesoamerican and Andean philosophical traditions
- Liberation theology and decolonial thought
- Contemporary Latin American philosophy and social theory
- Partnership with institutions across the region

---

## The Consent and Partnership Requirement

You cannot build this dataset by scraping. The communities whose knowledge
and culture you need to include have:

- Historical experience of having their cultural heritage extracted without
  consent or compensation
- Legitimate reasons not to trust Western technology companies
- In many cases, active cultural preservation projects that are not indexed
  on the English-language web and should not be accessed without relationship

**What the honest process requires:**

1. **Relationship before access** — establish trust with institutions and
   communities before requesting data contribution
2. **Explain the project** — what is being built, how the data will be used,
   who will benefit, under what terms
3. **Community control over representation** — communities decide how their
   traditions are depicted, not the model developers
4. **Compensation** — where communities are contributing cultural heritage
   that has economic value, they should share in the value created
5. **Opt-out and correction** — communities can withdraw their contribution
   or correct misrepresentations at any time
6. **Benefit sharing** — the model built on diverse cultural knowledge should
   be accessible and useful to the communities that contributed to it

This is the same consent mechanism we designed for the Bau Lab knowledge
infrastructure — applied to cultural and philosophical knowledge rather than
research papers. The principle is identical: ask first, build relationships,
share benefits, maintain correction rights.

---

## The Commercial Incentive Problem

Why hasn't this been done?

- It is slow — building relationships with institutions across dozens of
  cultures and languages takes years, not months
- It is expensive — digitisation, translation, relationship-building,
  compensation all cost money
- It does not produce immediate competitive advantage — the model trained
  on this dataset is more accurate and more representative, but "more
  accurate on non-Western philosophical traditions" does not win a benchmark
- The communities whose knowledge is needed are not the primary market —
  the companies building these models are selling to Western enterprise customers
  who do not notice or measure the cultural representation gap

The incentive structure produces exactly the dataset gap that exists.
Without external requirement — regulation, funding conditions, community
advocacy — the gap will persist. The model will continue to generate
middle-aged white men as philosophers because that is what the training
data contains in abundance, and nobody building the model bears the cost
of that limitation.

---

## The Per-Culture Dataset Framework

What a responsible dataset construction process looks like in practice:

| Culture/Region | Primary institutions | Data types | Consent mechanism | Language coverage |
|---|---|---|---|---|
| Islamic world | Al-Azhar, major universities | Philosophical texts, art, manuscripts | Institutional agreements | Arabic, Persian, Urdu, Turkish, Malay |
| South Asia | IIT, JNU, IIAS | Classical texts, visual traditions | Institutional + community | 10+ languages |
| Sub-Saharan Africa | African universities, museums | Philosophy, oral tradition records, visual art | Community FPIC | 50+ languages |
| East Asia | Chinese, Japanese, Korean institutions | Classical and contemporary philosophy, art | Institutional agreements | Chinese, Japanese, Korean |
| Indigenous globally | Community-controlled | Oral traditions, land-based knowledge | Community sovereignty, FPIC | Per community |
| Latin America | Regional universities | Decolonial thought, Indigenous traditions | Institutional + community | Spanish, Portuguese, Indigenous |

---

## Connection to the Bau Lab Knowledge Infrastructure

The dataset geography problem is the same problem the Bau Lab knowledge
infrastructure is trying to solve in the research domain:

- Academic knowledge is also geographically concentrated — predominantly
  Western, English-language, institutionally credentialled
- The research graph built only on arXiv, IEEE, and ACM reflects the same
  information asymmetry as the image generation model
- Papers from non-Western institutions, in non-English languages, on
  non-Western research traditions are systematically underrepresented

The consent and partnership mechanism designed for researcher outreach
applies here too — contact before indexing, explain the project, share
results back, maintain correction rights.

The honest knowledge infrastructure — whether for image generation,
language modelling, or research graphs — requires deliberate construction
from diverse sources, with consent, with compensation, with community
control over representation.

That is harder than scraping. It is the only approach that produces
a model that actually knows what it is talking about.

---

## Key Insight

> The model generates middle-aged white men as philosophers
> not because someone decided that is what philosophers look like.
> Because the training data contains that image ten thousand times
> and Ibn Rushd a handful of times.
>
> You cannot fix this downstream. You fix it upstream.
> You fix it by building the dataset that contains the world
> as it actually is — all of it, not just the part that was
> already digitised in English by institutions with the resources to do so.
>
> That dataset does not yet exist.
> Building it requires relationships, consent, compensation, and time.
> None of those are compatible with the current pace of the race.
> Which is, again, an argument for slowing down.
