# Inter-rater review — instructions

You will read **120** short medical claim + evidence pairs from a spreadsheet (`iaa_sample.csv`). Each row is independent. You do **not** know how the pair was created or what “type” of edit it is — treat it like a line from a textbook quiz.

For **every row**, answer **both** questions below using **Y** or **N** only (capital letter). Add a brief **note** only if something is unclear or you want to flag wording.

## Question 1 — support (`q1_supported`)

**Does the evidence support the claim as written? (Y/N)**

Read the **claim** and the **evidence** (usually a nearby paragraph). Decide whether a careful reader would say the claim is **supported** by that evidence, **as written** (same numbers, units, direction, and meaning). If the claim overstates, contradicts, or introduces facts not in the evidence, answer **N**.

## Question 2 — naturalness (`q2_natural`)

**Is the claim fluent and clinically natural — would a clinician or textbook write it this way? (Y/N)**

Ignore whether the evidence supports the claim for this question. Focus on **wording**: grammar, typical clinical style, plausible units/doses/phrasing. Awkward conversions, robotic phrasing, or phrasing you would not expect in a board-review book → **N**.

---

## Worked examples for Question 1 (support)

These are **not** from your 120 items; they illustrate the decision only.

**Example A — Y**  
Claim: *“Adults with normal renal function should receive 500 mg of azithromycin on day 1.”*  
Evidence: *“The recommended regimen is 500 mg orally on the first day, followed by 250 mg daily.”*  
→ **Y** — the evidence states the day-1 dose.

**Example B — N**  
Claim: *“Metformin is contraindicated in all patients with mild kidney disease.”*  
Evidence: *“Metformin may be used with caution when eGFR is 30–45 mL/min/1.73 m² with dose adjustment.”*  
→ **N** — evidence allows use with caution, not absolute contraindication.

**Example C — N**  
Claim: *“Give 2 g of ceftriaxone every 8 hours for community pneumonia.”*  
Evidence: *“Typical adult dosing is 1–2 g once daily or every 24 hours for many indications.”*  
→ **N** — every-8-hours schedule is not supported by the excerpt.

---

## Worked examples for Question 2 (naturalness)

**Example D — Y**  
Claim: *“For hypertension, start amlodipine 5 mg orally once daily.”*  
→ **Y** — standard textbook phrasing.

**Example E — N**  
Claim: *“Administer «75000 mg» of glucose for the oral glucose tolerance test.”*  
→ **N** — no clinician writes 75000 mg for this context; units/scale feel wrong even if numerically convertible.

**Example F — N**  
Claim: *“The medicine should be put into the body vein route at a speed of fast drip always.”*  
→ **N** — not fluent clinical English.

---

## Practical tips

- Answer **Y/N for both columns on every row**; leave `note` blank unless needed.
- If support and naturalness disagree (e.g., supported but awkward wording), that is fine — mark each column separately.
- Do not look up external sources; use only the claim and evidence provided.
