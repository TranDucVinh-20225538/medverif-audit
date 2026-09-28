# phenomenon checklist

STAMP: MOCK

n_bootstrap: 1000
seed: 42
ci: percentile 2.5 and 97.5 over base_id

c0_pass = n(C0 verdict PASS) / n(C0 verdict in {PASS, FAIL})
cond = base_id whose C0 verdict is PASS
false_pass = n(verdict PASS) / n(verdict in {PASS, FAIL})
inv_pass = false_pass on condition INV-claim among cond
e1_evid_false_pass = false_pass on condition E1-evid among cond
e1_claim_false_pass = false_pass on condition E1-claim among cond
gap_evid = inv_pass - e1_evid_false_pass
gap_claim = inv_pass - e1_claim_false_pass
parse_fail_rate = n(PARSE_FAIL) / n(items)
n_before = nonoverlapping count of original evidence span in evidence_c0
n_after = nonoverlapping count of that same span in the scored evidence
multi = n_before > 1
evidence_len = character length of scored evidence
span_position = scored evidence.find(evidence_span); -1 if absent

## verifier x type

| verifier | type | n | parse_fail_rate | c0_pass | cond_inv_pass | cond_e1_evid_false_pass | cond_e1_claim_false_pass | gap_evid | gap_claim | x2_evid | x10_evid | x2_claim | x10_claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_medscore | DOSE | 96 | 0.0312 (3/96) | 0.2500 (3/12) | 0.6667 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.5000 [0.5000, 0.5000] | 0.1667 [-0.5000, 1.0000] | 0.1667 [-0.5000, 0.5000] | 0.6667 [0.0000, 1.0000] | 0.3333 [0.0000, 1.0000] | 0.3333 [0.0000, 1.0000] | 0.6667 [0.0000, 1.0000] |
| v1_medscore | POLARITY | 60 | 0.0000 (0/60) | 0.5000 (6/12) | 0.3333 [0.0000, 0.6667] | 0.1667 [0.0000, 0.5000] | 0.3333 [0.0000, 0.6667] | 0.1667 [0.0000, 0.5000] | 0.0000 [-0.6667, 0.6667] | NA | NA | NA | NA |
| v2a_minicheck | DOSE | 96 | 0.0312 (3/96) | 0.5000 (5/10) | 1.0000 [1.0000, 1.0000] | 0.5556 [0.2222, 0.8889] | 0.5000 [0.2000, 0.8000] | 0.4444 [0.1111, 0.7778] | 0.5000 [0.2000, 0.8000] | 0.5000 [0.0000, 1.0000] | 0.6000 [0.2000, 1.0000] | 0.2000 [0.0000, 0.6000] | 0.8000 [0.4000, 1.0000] |
| v2a_minicheck | POLARITY | 60 | 0.0500 (3/60) | 0.6364 (7/11) | 0.4286 [0.1429, 0.8571] | 0.7143 [0.2857, 1.0000] | 0.5714 [0.2857, 0.8571] | -0.2857 [-0.5714, 0.0000] | -0.1429 [-0.7143, 0.4286] | NA | NA | NA | NA |
| v2b_bespoke | DOSE | 96 | 0.0521 (5/96) | 0.4167 (5/12) | 0.4000 [0.0000, 0.8000] | 0.7000 [0.3000, 1.0000] | 0.7143 [0.3333, 1.0000] | -0.3000 [-1.0000, 0.5000] | -0.3143 [-0.6333, -0.0333] | 0.8000 [0.4000, 1.0000] | 0.6000 [0.2000, 1.0000] | 0.7500 [0.2500, 1.0000] | 0.6667 [0.0000, 1.0000] |
| v2b_bespoke | POLARITY | 60 | 0.0167 (1/60) | 0.4167 (5/12) | 0.4000 [0.0000, 0.8000] | 0.2500 [0.0000, 0.7500] | 0.4000 [0.0000, 0.8000] | 0.1500 [-0.6017, 0.8000] | 0.0000 [0.0000, 0.0000] | NA | NA | NA | NA |
| v3_alignscore | DOSE | 96 | 0.0104 (1/96) | 0.5000 (6/12) | 0.5000 [0.1667, 0.8333] | 0.4545 [0.1667, 0.7778] | 0.5000 [0.2500, 0.7500] | 0.0455 [-0.6333, 0.6667] | 0.0000 [-0.5000, 0.4167] | 0.6000 [0.2000, 1.0000] | 0.3333 [0.0000, 0.6667] | 0.5000 [0.1667, 0.8333] | 0.5000 [0.1667, 0.8333] |
| v3_alignscore | POLARITY | 60 | 0.1000 (6/60) | 0.8333 (10/12) | 0.7500 [0.5000, 1.0000] | 0.9000 [0.7000, 1.0000] | 0.5000 [0.1250, 0.8750] | -0.1500 [-0.4444, 0.0000] | 0.2500 [-0.2143, 0.6667] | NA | NA | NA | NA |
| v4_ragas_nli | DOSE | 96 | 0.0729 (7/96) | 0.6000 (6/10) | 0.5000 [0.1667, 0.8333] | 0.6364 [0.5000, 0.8182] | 0.2727 [0.0909, 0.4545] | -0.1364 [-0.5833, 0.2879] | 0.2273 [0.0556, 0.4167] | 0.6000 [0.2000, 1.0000] | 0.6667 [0.3333, 1.0000] | 0.3333 [0.0000, 0.6667] | 0.2000 [0.0000, 0.6000] |
| v4_ragas_nli | POLARITY | 60 | 0.0500 (3/60) | 0.6364 (7/11) | 0.4286 [0.1429, 0.8571] | 0.5714 [0.2857, 0.8571] | 0.5714 [0.1429, 0.8571] | -0.1429 [-0.7143, 0.4286] | -0.1429 [-0.5714, 0.2857] | NA | NA | NA | NA |

## false-PASS with and without multi-occurrence evidence

multi_bases = base_id with n_before > 1 on any of its instances

| verifier | type | condition | n_multi_bases | all | without_multi | multi_only |
| --- | --- | --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | 3 | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | NA |
| v1_medscore | DOSE | E1-claim | 3 | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | NA |
| v1_medscore | POLARITY | E1-evid | 0 | 0.1667 [0.0000, 0.5000] | 0.1667 [0.0000, 0.5000] | NA |
| v1_medscore | POLARITY | E1-claim | 0 | 0.3333 [0.0000, 0.6667] | 0.3333 [0.0000, 0.6667] | NA |
| v2a_minicheck | DOSE | E1-evid | 3 | 0.5556 [0.2222, 0.8889] | 0.7143 [0.5000, 1.0000] | 0.0000 |
| v2a_minicheck | DOSE | E1-claim | 3 | 0.5000 [0.2000, 0.8000] | 0.5000 [0.1250, 0.8750] | 0.5000 |
| v2a_minicheck | POLARITY | E1-evid | 0 | 0.7143 [0.2857, 1.0000] | 0.7143 [0.2857, 1.0000] | NA |
| v2a_minicheck | POLARITY | E1-claim | 0 | 0.5714 [0.2857, 0.8571] | 0.5714 [0.2857, 0.8571] | NA |
| v2b_bespoke | DOSE | E1-evid | 3 | 0.7000 [0.3000, 1.0000] | 0.6667 [0.0000, 1.0000] | 0.7500 [0.5000, 1.0000] |
| v2b_bespoke | DOSE | E1-claim | 3 | 0.7143 [0.3333, 1.0000] | 0.6000 [0.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| v2b_bespoke | POLARITY | E1-evid | 0 | 0.2500 [0.0000, 0.7500] | 0.2500 [0.0000, 0.7500] | NA |
| v2b_bespoke | POLARITY | E1-claim | 0 | 0.4000 [0.0000, 0.8000] | 0.4000 [0.0000, 0.8000] | NA |
| v3_alignscore | DOSE | E1-evid | 3 | 0.4545 [0.1667, 0.7778] | 0.4286 [0.1250, 0.8000] | 0.5000 [0.0000, 1.0000] |
| v3_alignscore | DOSE | E1-claim | 3 | 0.5000 [0.2500, 0.7500] | 0.5000 [0.1250, 0.8750] | 0.5000 [0.5000, 0.5000] |
| v3_alignscore | POLARITY | E1-evid | 0 | 0.9000 [0.7000, 1.0000] | 0.9000 [0.7000, 1.0000] | NA |
| v3_alignscore | POLARITY | E1-claim | 0 | 0.5000 [0.1250, 0.8750] | 0.5000 [0.1250, 0.8750] | NA |
| v4_ragas_nli | DOSE | E1-evid | 3 | 0.6364 [0.5000, 0.8182] | 0.6250 [0.5000, 0.8750] | 0.6667 [0.5000, 1.0000] |
| v4_ragas_nli | DOSE | E1-claim | 3 | 0.2727 [0.0909, 0.4545] | 0.1429 [0.0000, 0.3750] | 0.5000 [0.5000, 0.5000] |
| v4_ragas_nli | POLARITY | E1-evid | 0 | 0.5714 [0.2857, 0.8571] | 0.5714 [0.2857, 0.8571] | NA |
| v4_ragas_nli | POLARITY | E1-claim | 0 | 0.5714 [0.1429, 0.8571] | 0.5714 [0.1429, 0.8571] | NA |

## flagged instances (n_before > 1)

| instance_id | type | condition | magnitude | n_before | n_after | evidence_len | span_position |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D00__C0__none | DOSE | C0 | none | 2 | 2 | 120 | 0 |
| D00__E1-evid__x2 | DOSE | E1-evid | x2 | 2 | 1 | 121 | 0 |
| D00__E1-claim__x2 | DOSE | E1-claim | x2 | 2 | 2 | 120 | 0 |
| D00__E2__x2 | DOSE | E2 | x2 | 2 | 1 | 121 | 0 |
| D00__E1-evid__x10 | DOSE | E1-evid | x10 | 2 | 1 | 121 | 0 |
| D00__E1-claim__x10 | DOSE | E1-claim | x10 | 2 | 2 | 120 | 0 |
| D00__E2__x10 | DOSE | E2 | x10 | 2 | 1 | 121 | 0 |
| D00__INV-claim__unit_conversion | DOSE | INV-claim | unit_conversion | 2 | 2 | 120 | 0 |
| D01__C0__none | DOSE | C0 | none | 2 | 2 | 280 | 40 |
| D01__E1-evid__x2 | DOSE | E1-evid | x2 | 2 | 1 | 281 | 40 |
| D01__E1-claim__x2 | DOSE | E1-claim | x2 | 2 | 2 | 280 | 40 |
| D01__E2__x2 | DOSE | E2 | x2 | 2 | 1 | 281 | 40 |
| D01__E1-evid__x10 | DOSE | E1-evid | x10 | 2 | 1 | 281 | 40 |
| D01__E1-claim__x10 | DOSE | E1-claim | x10 | 2 | 2 | 280 | 40 |
| D01__E2__x10 | DOSE | E2 | x10 | 2 | 1 | 281 | 40 |
| D01__INV-claim__unit_conversion | DOSE | INV-claim | unit_conversion | 2 | 2 | 280 | 40 |
| D02__C0__none | DOSE | C0 | none | 2 | 2 | 550 | 120 |
| D02__E1-evid__x2 | DOSE | E1-evid | x2 | 2 | 1 | 551 | 120 |
| D02__E1-claim__x2 | DOSE | E1-claim | x2 | 2 | 2 | 550 | 120 |
| D02__E2__x2 | DOSE | E2 | x2 | 2 | 1 | 551 | 120 |
| D02__E1-evid__x10 | DOSE | E1-evid | x10 | 2 | 1 | 551 | 120 |
| D02__E1-claim__x10 | DOSE | E1-claim | x10 | 2 | 2 | 550 | 120 |
| D02__E2__x10 | DOSE | E2 | x10 | 2 | 1 | 551 | 120 |
| D02__INV-claim__unit_conversion | DOSE | INV-claim | unit_conversion | 2 | 2 | 550 | 120 |

## false-PASS vs evidence length

| verifier | type | condition | bin | false_pass |
| --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | [0, 200) | 0.0000 |
| v1_medscore | DOSE | E1-evid | [200, 400) | NA |
| v1_medscore | DOSE | E1-evid | [400, 800) | NA |
| v1_medscore | DOSE | E1-evid | [800, 1600) | NA |
| v1_medscore | DOSE | E1-evid | [1600, inf) | 0.7500 [0.5000, 1.0000] |
| v1_medscore | DOSE | E1-claim | [0, 200) | 0.5000 |
| v1_medscore | DOSE | E1-claim | [200, 400) | NA |
| v1_medscore | DOSE | E1-claim | [400, 800) | NA |
| v1_medscore | DOSE | E1-claim | [800, 1600) | NA |
| v1_medscore | DOSE | E1-claim | [1600, inf) | 0.5000 [0.5000, 0.5000] |
| v1_medscore | POLARITY | E1-evid | [0, 200) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [200, 400) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [400, 800) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [800, 1600) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [1600, inf) | 0.5000 [0.0000, 1.0000] |
| v1_medscore | POLARITY | E1-claim | [0, 200) | 1.0000 |
| v1_medscore | POLARITY | E1-claim | [200, 400) | 0.0000 |
| v1_medscore | POLARITY | E1-claim | [400, 800) | 0.0000 |
| v1_medscore | POLARITY | E1-claim | [800, 1600) | 1.0000 |
| v1_medscore | POLARITY | E1-claim | [1600, inf) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | DOSE | E1-evid | [0, 200) | NA |
| v2a_minicheck | DOSE | E1-evid | [200, 400) | 0.5000 |
| v2a_minicheck | DOSE | E1-evid | [400, 800) | 0.0000 |
| v2a_minicheck | DOSE | E1-evid | [800, 1600) | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | E1-evid | [1600, inf) | 0.5000 |
| v2a_minicheck | DOSE | E1-claim | [0, 200) | NA |
| v2a_minicheck | DOSE | E1-claim | [200, 400) | 0.5000 |
| v2a_minicheck | DOSE | E1-claim | [400, 800) | 0.5000 |
| v2a_minicheck | DOSE | E1-claim | [800, 1600) | 0.7500 [0.5000, 1.0000] |
| v2a_minicheck | DOSE | E1-claim | [1600, inf) | 0.0000 |
| v2a_minicheck | POLARITY | E1-evid | [0, 200) | 1.0000 |
| v2a_minicheck | POLARITY | E1-evid | [200, 400) | 0.7500 [0.2500, 1.0000] |
| v2a_minicheck | POLARITY | E1-evid | [400, 800) | 0.0000 |
| v2a_minicheck | POLARITY | E1-evid | [800, 1600) | 1.0000 |
| v2a_minicheck | POLARITY | E1-evid | [1600, inf) | NA |
| v2a_minicheck | POLARITY | E1-claim | [0, 200) | 0.0000 |
| v2a_minicheck | POLARITY | E1-claim | [200, 400) | 0.5000 [0.0000, 1.0000] |
| v2a_minicheck | POLARITY | E1-claim | [400, 800) | 1.0000 |
| v2a_minicheck | POLARITY | E1-claim | [800, 1600) | 1.0000 |
| v2a_minicheck | POLARITY | E1-claim | [1600, inf) | NA |
| v2b_bespoke | DOSE | E1-evid | [0, 200) | 1.0000 [1.0000, 1.0000] |
| v2b_bespoke | DOSE | E1-evid | [200, 400) | 0.5000 |
| v2b_bespoke | DOSE | E1-evid | [400, 800) | NA |
| v2b_bespoke | DOSE | E1-evid | [800, 1600) | NA |
| v2b_bespoke | DOSE | E1-evid | [1600, inf) | 0.5000 [0.0000, 1.0000] |
| v2b_bespoke | DOSE | E1-claim | [0, 200) | 0.6667 [0.5000, 1.0000] |
| v2b_bespoke | DOSE | E1-claim | [200, 400) | 1.0000 |
| v2b_bespoke | DOSE | E1-claim | [400, 800) | NA |
| v2b_bespoke | DOSE | E1-claim | [800, 1600) | NA |
| v2b_bespoke | DOSE | E1-claim | [1600, inf) | 0.6667 [0.0000, 1.0000] |
| v2b_bespoke | POLARITY | E1-evid | [0, 200) | 0.0000 |
| v2b_bespoke | POLARITY | E1-evid | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v2b_bespoke | POLARITY | E1-evid | [400, 800) | 1.0000 |
| v2b_bespoke | POLARITY | E1-evid | [800, 1600) | NA |
| v2b_bespoke | POLARITY | E1-evid | [1600, inf) | NA |
| v2b_bespoke | POLARITY | E1-claim | [0, 200) | 0.5000 [0.0000, 1.0000] |
| v2b_bespoke | POLARITY | E1-claim | [200, 400) | 0.5000 [0.0000, 1.0000] |
| v2b_bespoke | POLARITY | E1-claim | [400, 800) | 0.0000 |
| v2b_bespoke | POLARITY | E1-claim | [800, 1600) | NA |
| v2b_bespoke | POLARITY | E1-claim | [1600, inf) | NA |
| v3_alignscore | DOSE | E1-evid | [0, 200) | 1.0000 |
| v3_alignscore | DOSE | E1-evid | [200, 400) | 0.3333 [0.0000, 0.5000] |
| v3_alignscore | DOSE | E1-evid | [400, 800) | NA |
| v3_alignscore | DOSE | E1-evid | [800, 1600) | 0.3333 [0.0000, 1.0000] |
| v3_alignscore | DOSE | E1-evid | [1600, inf) | NA |
| v3_alignscore | DOSE | E1-claim | [0, 200) | 0.5000 |
| v3_alignscore | DOSE | E1-claim | [200, 400) | 0.6667 [0.5000, 1.0000] |
| v3_alignscore | DOSE | E1-claim | [400, 800) | NA |
| v3_alignscore | DOSE | E1-claim | [800, 1600) | 0.2500 [0.0000, 0.5000] |
| v3_alignscore | DOSE | E1-claim | [1600, inf) | NA |
| v3_alignscore | POLARITY | E1-evid | [0, 200) | 1.0000 |
| v3_alignscore | POLARITY | E1-evid | [200, 400) | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-evid | [400, 800) | 0.5000 [0.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-evid | [800, 1600) | 1.0000 |
| v3_alignscore | POLARITY | E1-evid | [1600, inf) | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-claim | [0, 200) | 1.0000 |
| v3_alignscore | POLARITY | E1-claim | [200, 400) | 0.6667 [0.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-claim | [400, 800) | 0.0000 |
| v3_alignscore | POLARITY | E1-claim | [800, 1600) | 1.0000 |
| v3_alignscore | POLARITY | E1-claim | [1600, inf) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | DOSE | E1-evid | [0, 200) | 0.5000 |
| v4_ragas_nli | DOSE | E1-evid | [200, 400) | 0.6667 [0.5000, 1.0000] |
| v4_ragas_nli | DOSE | E1-evid | [400, 800) | 1.0000 |
| v4_ragas_nli | DOSE | E1-evid | [800, 1600) | 0.5000 |
| v4_ragas_nli | DOSE | E1-evid | [1600, inf) | NA |
| v4_ragas_nli | DOSE | E1-claim | [0, 200) | 0.0000 |
| v4_ragas_nli | DOSE | E1-claim | [200, 400) | 0.1667 [0.0000, 0.5000] |
| v4_ragas_nli | DOSE | E1-claim | [400, 800) | 0.5000 |
| v4_ragas_nli | DOSE | E1-claim | [800, 1600) | 0.5000 |
| v4_ragas_nli | DOSE | E1-claim | [1600, inf) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [0, 200) | 1.0000 |
| v4_ragas_nli | POLARITY | E1-evid | [200, 400) | 0.5000 [0.0000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [400, 800) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [800, 1600) | 0.5000 [0.0000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [1600, inf) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [0, 200) | 0.0000 |
| v4_ragas_nli | POLARITY | E1-claim | [200, 400) | 0.7500 [0.2500, 1.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [400, 800) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [800, 1600) | 0.5000 [0.0000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [1600, inf) | NA |

## false-PASS vs character position of the target span

| verifier | type | condition | bin | false_pass |
| --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | [0, 50) | 0.0000 |
| v1_medscore | DOSE | E1-evid | [50, 150) | NA |
| v1_medscore | DOSE | E1-evid | [150, 400) | NA |
| v1_medscore | DOSE | E1-evid | [400, 1000) | 0.7500 [0.5000, 1.0000] |
| v1_medscore | DOSE | E1-evid | [1000, inf) | NA |
| v1_medscore | DOSE | E1-evid | not_found | NA |
| v1_medscore | DOSE | E1-claim | [0, 50) | 0.5000 |
| v1_medscore | DOSE | E1-claim | [50, 150) | NA |
| v1_medscore | DOSE | E1-claim | [150, 400) | NA |
| v1_medscore | DOSE | E1-claim | [400, 1000) | 0.5000 [0.5000, 0.5000] |
| v1_medscore | DOSE | E1-claim | [1000, inf) | NA |
| v1_medscore | DOSE | E1-claim | not_found | NA |
| v1_medscore | POLARITY | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-evid | [50, 150) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [150, 400) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [400, 1000) | 0.5000 [0.0000, 1.0000] |
| v1_medscore | POLARITY | E1-evid | [1000, inf) | NA |
| v1_medscore | POLARITY | E1-evid | not_found | NA |
| v1_medscore | POLARITY | E1-claim | [0, 50) | 0.5000 [0.0000, 1.0000] |
| v1_medscore | POLARITY | E1-claim | [50, 150) | 0.0000 |
| v1_medscore | POLARITY | E1-claim | [150, 400) | 1.0000 |
| v1_medscore | POLARITY | E1-claim | [400, 1000) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [1000, inf) | NA |
| v1_medscore | POLARITY | E1-claim | not_found | NA |
| v2a_minicheck | DOSE | E1-evid | [0, 50) | 0.5000 |
| v2a_minicheck | DOSE | E1-evid | [50, 150) | 0.0000 |
| v2a_minicheck | DOSE | E1-evid | [150, 400) | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | E1-evid | [400, 1000) | 0.5000 |
| v2a_minicheck | DOSE | E1-evid | [1000, inf) | NA |
| v2a_minicheck | DOSE | E1-evid | not_found | NA |
| v2a_minicheck | DOSE | E1-claim | [0, 50) | 0.5000 |
| v2a_minicheck | DOSE | E1-claim | [50, 150) | 0.5000 |
| v2a_minicheck | DOSE | E1-claim | [150, 400) | 0.7500 [0.5000, 1.0000] |
| v2a_minicheck | DOSE | E1-claim | [400, 1000) | 0.0000 |
| v2a_minicheck | DOSE | E1-claim | [1000, inf) | NA |
| v2a_minicheck | DOSE | E1-claim | not_found | NA |
| v2a_minicheck | POLARITY | E1-evid | [0, 50) | 0.8000 [0.4000, 1.0000] |
| v2a_minicheck | POLARITY | E1-evid | [50, 150) | 0.0000 |
| v2a_minicheck | POLARITY | E1-evid | [150, 400) | 1.0000 |
| v2a_minicheck | POLARITY | E1-evid | [400, 1000) | NA |
| v2a_minicheck | POLARITY | E1-evid | [1000, inf) | NA |
| v2a_minicheck | POLARITY | E1-evid | not_found | NA |
| v2a_minicheck | POLARITY | E1-claim | [0, 50) | 0.4000 [0.0000, 0.8000] |
| v2a_minicheck | POLARITY | E1-claim | [50, 150) | 1.0000 |
| v2a_minicheck | POLARITY | E1-claim | [150, 400) | 1.0000 |
| v2a_minicheck | POLARITY | E1-claim | [400, 1000) | NA |
| v2a_minicheck | POLARITY | E1-claim | [1000, inf) | NA |
| v2a_minicheck | POLARITY | E1-claim | not_found | NA |
| v2b_bespoke | DOSE | E1-evid | [0, 50) | 0.8333 [0.5000, 1.0000] |
| v2b_bespoke | DOSE | E1-evid | [50, 150) | NA |
| v2b_bespoke | DOSE | E1-evid | [150, 400) | NA |
| v2b_bespoke | DOSE | E1-evid | [400, 1000) | 0.5000 [0.0000, 1.0000] |
| v2b_bespoke | DOSE | E1-evid | [1000, inf) | NA |
| v2b_bespoke | DOSE | E1-evid | not_found | NA |
| v2b_bespoke | DOSE | E1-claim | [0, 50) | 0.7500 [0.5000, 1.0000] |
| v2b_bespoke | DOSE | E1-claim | [50, 150) | NA |
| v2b_bespoke | DOSE | E1-claim | [150, 400) | NA |
| v2b_bespoke | DOSE | E1-claim | [400, 1000) | 0.6667 [0.0000, 1.0000] |
| v2b_bespoke | DOSE | E1-claim | [1000, inf) | NA |
| v2b_bespoke | DOSE | E1-claim | not_found | NA |
| v2b_bespoke | POLARITY | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v2b_bespoke | POLARITY | E1-evid | [50, 150) | 1.0000 |
| v2b_bespoke | POLARITY | E1-evid | [150, 400) | NA |
| v2b_bespoke | POLARITY | E1-evid | [400, 1000) | NA |
| v2b_bespoke | POLARITY | E1-evid | [1000, inf) | NA |
| v2b_bespoke | POLARITY | E1-evid | not_found | NA |
| v2b_bespoke | POLARITY | E1-claim | [0, 50) | 0.5000 [0.0000, 1.0000] |
| v2b_bespoke | POLARITY | E1-claim | [50, 150) | 0.0000 |
| v2b_bespoke | POLARITY | E1-claim | [150, 400) | NA |
| v2b_bespoke | POLARITY | E1-claim | [400, 1000) | NA |
| v2b_bespoke | POLARITY | E1-claim | [1000, inf) | NA |
| v2b_bespoke | POLARITY | E1-claim | not_found | NA |
| v3_alignscore | DOSE | E1-evid | [0, 50) | 0.5000 [0.1250, 0.8750] |
| v3_alignscore | DOSE | E1-evid | [50, 150) | NA |
| v3_alignscore | DOSE | E1-evid | [150, 400) | 0.3333 [0.0000, 1.0000] |
| v3_alignscore | DOSE | E1-evid | [400, 1000) | NA |
| v3_alignscore | DOSE | E1-evid | [1000, inf) | NA |
| v3_alignscore | DOSE | E1-evid | not_found | NA |
| v3_alignscore | DOSE | E1-claim | [0, 50) | 0.6250 [0.5000, 0.8750] |
| v3_alignscore | DOSE | E1-claim | [50, 150) | NA |
| v3_alignscore | DOSE | E1-claim | [150, 400) | 0.2500 [0.0000, 0.5000] |
| v3_alignscore | DOSE | E1-claim | [400, 1000) | NA |
| v3_alignscore | DOSE | E1-claim | [1000, inf) | NA |
| v3_alignscore | DOSE | E1-claim | not_found | NA |
| v3_alignscore | POLARITY | E1-evid | [0, 50) | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-evid | [50, 150) | 0.5000 [0.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-evid | [150, 400) | 1.0000 |
| v3_alignscore | POLARITY | E1-evid | [400, 1000) | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | E1-evid | [1000, inf) | NA |
| v3_alignscore | POLARITY | E1-evid | not_found | NA |
| v3_alignscore | POLARITY | E1-claim | [0, 50) | 0.7500 [0.2500, 1.0000] |
| v3_alignscore | POLARITY | E1-claim | [50, 150) | 0.0000 |
| v3_alignscore | POLARITY | E1-claim | [150, 400) | 1.0000 |
| v3_alignscore | POLARITY | E1-claim | [400, 1000) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-claim | [1000, inf) | NA |
| v3_alignscore | POLARITY | E1-claim | not_found | NA |
| v4_ragas_nli | DOSE | E1-evid | [0, 50) | 0.6250 [0.5000, 0.8750] |
| v4_ragas_nli | DOSE | E1-evid | [50, 150) | 1.0000 |
| v4_ragas_nli | DOSE | E1-evid | [150, 400) | 0.5000 |
| v4_ragas_nli | DOSE | E1-evid | [400, 1000) | NA |
| v4_ragas_nli | DOSE | E1-evid | [1000, inf) | NA |
| v4_ragas_nli | DOSE | E1-evid | not_found | NA |
| v4_ragas_nli | DOSE | E1-claim | [0, 50) | 0.1429 [0.0000, 0.3750] |
| v4_ragas_nli | DOSE | E1-claim | [50, 150) | 0.5000 |
| v4_ragas_nli | DOSE | E1-claim | [150, 400) | 0.5000 |
| v4_ragas_nli | DOSE | E1-claim | [400, 1000) | NA |
| v4_ragas_nli | DOSE | E1-claim | [1000, inf) | NA |
| v4_ragas_nli | DOSE | E1-claim | not_found | NA |
| v4_ragas_nli | POLARITY | E1-evid | [0, 50) | 0.6000 [0.2000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [50, 150) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [150, 400) | 0.5000 [0.0000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [400, 1000) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [1000, inf) | NA |
| v4_ragas_nli | POLARITY | E1-evid | not_found | NA |
| v4_ragas_nli | POLARITY | E1-claim | [0, 50) | 0.6000 [0.2000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [50, 150) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [150, 400) | 0.5000 [0.0000, 1.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [400, 1000) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [1000, inf) | NA |
| v4_ragas_nli | POLARITY | E1-claim | not_found | NA |
