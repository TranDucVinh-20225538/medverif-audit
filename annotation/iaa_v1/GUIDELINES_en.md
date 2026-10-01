# Annotation guidelines: IAA v1, "Same Dose, Different Verdict"

**Version:** iaa_v1 (October 2026) | **Items:** 150 | **Estimated time:** about 2–3 hours (about 1 minute per item; breaks are fine, and you can work in several sessions)

## 1. Purpose

We are studying automatic **fact-checkers for medical text**: models that read a piece of *evidence* (a passage from a medical textbook or article) and decide whether a *claim* is supported by it. To test them, we made small, controlled edits to claims about doses, recommendations, and so on. Some edits should **keep** the meaning (a checker should give the same verdict). Others should **break** it (a checker should change its verdict).

Every edit was produced automatically and then checked by one author. We need an **independent second opinion from a clinician** to measure how reliable those checks are (inter-annotator agreement, Cohen's kappa). For dose errors we would also like your clinical judgement of **how harmful** the wrong dose would be.

You are **not** judging the fact-checkers, and you do not need to know their outputs. There are no trick questions. If you are unsure, choose *Unsure* and leave a comment.

## 2. What you receive

- `annotation_sheet.xlsx`: the main file (sheet *Annotation*; dropdowns in the answer columns). `annotation_sheet.csv` has the same content for editors without Excel.
- This document (`GUIDELINES_en.md` / `.pdf`), plus a Vietnamese version (`GUIDELINES_vi.md` / `.pdf`).

Each row has the following columns:

| column | meaning |
|---|---|
| `item_id` | opaque id (e.g. `IAA1-3f9a0c`). Please do not change it. |
| `condition` | the type of edit (see §3) |
| `intended_change` | what the edit was **supposed** to do |
| `evidence` | the evidence passage (for *Unit error (in evidence)* items, this is the **edited** evidence) |
| `original_evidence` | filled **only** when the evidence itself was edited |
| `what_changed` | an automatic word-level diff (`[old] -> [new]`), provided only to help you spot the edit |
| `original_claim` | the claim before editing |
| `edited_claim` | the claim after editing (for *Base claim* items there is no edit) |
| **Q1, Q2, Q3, comment** | your answers |

Items are in random order, and items of different types are mixed. The same source sentence can appear in more than one item; judge each row **on its own**.

## 3. The questions

### Q1 (every row): *Is the edited claim a valid instance of its intended condition?*  Yes / No / Unsure

Read `intended_change`, then compare the original and the edited text (and the evidence where relevant). Answer **Yes** if the edit does what it is supposed to do, cleanly. Answer **No** if it does not: for example, the meaning changed when it should have stayed the same, the "error" is not actually wrong, or the edit made the sentence ungrammatical or clinically odd so that it no longer tests what it is meant to test. Answer **Unsure** if you cannot decide; please add a comment.

### Q2 (only *Unit conversion* rows): *Is it clinically equivalent and natural?*

- **Natural**: the same amount, written the way a clinician or a drug label would plausibly write it (e.g. `0.5 g → 500 mg`).
- **Equivalent-unnatural**: arithmetically the same amount, but nobody would write it like that (e.g. `75 g → 75000 mg` of glucose, `1 mg/kg → 1000 mcg/kg`).
- **Not equivalent**: the conversion is wrong, or the amount changed.

### Q3 (only *Unit error* and *Dose value error* rows): *If this wrong dose reached a patient, how severe would the harm be?*

Assume that the **edited** dose (the wrong one) is actually given to a typical patient in the setting the claim describes, instead of the correct dose. Rate the **most likely** outcome, not the worst imaginable one. The scale is inspired by the NCC MERP medication-error index:

| Q3 value | meaning | approx. NCC MERP category |
|---|---|---|
| **None** | no harm expected (dose still within a safe or usual range, or clinically irrelevant) | C |
| **Minor** | could cause mild, temporary harm, or would need extra monitoring to confirm no harm | D |
| **Moderate** | temporary harm that needs treatment or intervention, or a hospital stay or a longer one | E–F |
| **Severe** | permanent harm, life-threatening (needs intervention to sustain life), or death | G–I |
| **Unsure** | you cannot judge (e.g. the drug or context is unclear) | – |

Q3 is independent of Q1: rate severity even if you answered Q1 = No (for example, a ×2 dose that stays inside the evidence's range may be *No* for Q1 and *None* for Q3).

### comment (optional)

Write anything useful, such as why you chose *No* or *Unsure*, a better wording, or "evidence is truncated". Vietnamese or English are both fine.

## 4. Definitions and examples for each condition

The examples below are **illustrative only** (they are not items in your sheet).

### 4.1 Unit conversion (keep meaning)
The dose is rewritten in another unit and must be the **same amount**.
- `Give amoxicillin 0.5 g three times daily` → `500 mg three times daily`: Q1 **Yes**, Q2 **Natural**.
- `75 g of glucose` → `75000 mg of glucose`: Q1 **Yes** (same amount), Q2 **Equivalent-unnatural**.
- `0.1 mg` → `10 mcg`: Q1 **No** (the amount changed), Q2 **Not equivalent**.

### 4.2 Polarity flip (reverse meaning)
The edited claim should state the **opposite** recommendation or fact, so that the evidence now contradicts it.
- `X is recommended for VVC` → `X is contraindicated for VVC`: **Yes**.
- `should be avoided in pregnancy` → `should not be avoided in pregnancy`: **Yes**, if it really means the opposite.
- `is relatively contraindicated in epilepsy` → `is relatively indicated in epilepsy`: often **No**, because "relatively indicated" is not a natural or clear opposite.
- An edit that negates only a side detail, leaving the main recommendation unchanged, is **No**.

### 4.3 Rephrase (keep meaning)
Wording changed (e.g. `should be given` → `ought to be given`); the clinical meaning must be **identical**, including strength (must / should / may) and scope.
- `should be administered` → `ought to be administered`: **Yes**.
- `is recommended` → `is indicated`: **Yes** if the strength is equivalent in context, **No** if it changes the strength of the recommendation.
- `may be used` → `must be used`: **No** (the strength changed).

### 4.4 Frequency/route rewording (keep meaning)
Frequency or route expressed differently; the meaning must be **identical** in the clinical context.
- `twice daily` → `every 12 hours`: **Yes** in most contexts.
- `intravenously` → `IV`: **Yes**.
- `three times daily with meals` → `every 8 hours`: **No** (the link to meals is lost).
- `orally or intravenously` → `PO or IV`: **Yes**. If only one part is changed in a way that makes the sentence ambiguous: **No**.

### 4.5 Unit error (break meaning; unit swapped, number kept)
The number stays the same but the unit is swapped (e.g. mg ↔ g, μg ↔ mg), making the dose wrong by a large factor (×1000). The edit may be in the **claim** or in the **evidence** (then `original_evidence` shows the original).
- `90 mg` → `90 g`: Q1 **Yes**; Q3 depends on the drug (often **Severe**).
- In the evidence: `200 mg` → `200 g` with the claim unchanged: Q1 **Yes** if claim and evidence now clearly conflict.
- Q1 **No** if the swapped number does not refer to a dose of the drug, or if the conflict is not real.

### 4.6 Dose value error (break meaning; number multiplied)
The dose number is multiplied by **2** or **10** (e.g. `500 mg` → `1000 mg` or `5000 mg`). Q1 asks whether the edited claim is now **clearly wrong according to the evidence**.
- Evidence: "starting dose 100 μg"; claim edited to "200 μg": **Yes**.
- Evidence: "doses vary from 50 to 200 μg"; claim edited to "200 μg": **No** (still inside the range, so not clearly wrong).
- Evidence: "≥200 mg is effective"; claim edited to "≥400 mg is effective": **No** (a higher threshold does not contradict it).
- Q3: rate the harm of the multiplied dose (×2 is often *None* or *Minor*; ×10 is often *Moderate* or *Severe*, depending on the drug's therapeutic window).

### 4.7 Base claim (no edit)
Here you judge the **original** claim itself (the `edited_claim` column says "no edit"). Q1 = **Yes** if the claim is (a) **faithful** to the evidence (fully supported, with no added facts) **and** (b) **self-contained and well-specified**: someone reading only the claim knows which drug or intervention, which population or setting, and which dose it means. Q1 = **No** if it is unsupported, distorted, or under-specified (e.g. "The drug is given at 50 μg several times a day" without naming the drug, or a dose that is only a side detail of the sentence).

## 5. Practical tips

- Judge each row independently, and do not look up the original source.
- The evidence passages are copied from books and articles and may be truncated or contain PDF artefacts (e.g. "follow-ing"). Ignore these unless they change the meaning.
- `what_changed` is an automatic diff and may show extra punctuation. Always read the full sentences.
- Leave Q2/Q3 as `N/A` where they are pre-filled. Answer every Q1.
- Save regularly. When finished, return the `.xlsx` (or `.csv`) file without renaming columns or reordering rows.

Thank you! Your answers will be used only in aggregate (agreement statistics), and you will be acknowledged in the paper as you prefer.
